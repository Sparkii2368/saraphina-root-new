#!/usr/bin/env python3
"""
ImprovementLoop - Continuous improvement system with AutoPatch and ApprovalPolicy.

- Detects weak spots (slow recall)
- Generates candidate fixes (SQL indexes)
- Tests in sandbox (DB copy) and applies per policy
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from statistics import mean
from pathlib import Path
from time import perf_counter
import shutil
import sqlite3
import json

from .db import get_preference, set_preference, write_audit_log
from .improvement_db import ImprovementDB


@dataclass
class ApprovalPolicy:
    auto_approve_safe: bool = True
    slow_query_ms_threshold: float = 150.0
    min_gain_percent: float = 20.0
    risk_threshold: float = 0.3  # 0..1

    @classmethod
    def load(cls, conn: sqlite3.Connection) -> "ApprovalPolicy":
        def _get(k, default):
            v = get_preference(conn, f"improve.{k}")
            if v is None:
                return default
            try:
                if isinstance(default, bool):
                    return v.lower() in ['true','1','yes','on']
                return type(default)(v)
            except Exception:
                return default
        return cls(
            auto_approve_safe=_get('auto_approve', True),
            slow_query_ms_threshold=_get('slow_ms', 150.0),
            min_gain_percent=_get('min_gain_pct', 20.0),
            risk_threshold=_get('risk_threshold', 0.3),
        )

    @classmethod
    def save_key(cls, conn: sqlite3.Connection, key: str, value: str) -> None:
        set_preference(conn, f"improve.{key}", value)

    def should_auto_approve(self, risk_score: float, gain_percent: float) -> bool:
        return self.auto_approve_safe and (risk_score <= self.risk_threshold) and (gain_percent >= self.min_gain_percent)


class AutoPatch:
    def __init__(self, conn: sqlite3.Connection, ke):
        self.conn = conn
        self.ke = ke

    def sample_recent_queries(self, limit: int = 10) -> List[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT text FROM queries ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [r[0] for r in cur.fetchall() if r and r[0]] or ["python", "ai", "security"]

    def measure_recall_ms(self, queries: List[str]) -> Tuple[float, List[float]]:
        times: List[float] = []
        for q in queries:
            t0 = perf_counter()
            try:
                _ = self.ke.recall(q, top_k=5)
            except Exception:
                pass
            dt = (perf_counter() - t0) * 1000.0
            times.append(dt)
        return (mean(times) if times else 0.0, times)

    def existing_indexes(self, table: str) -> List[str]:
        cur = self.conn.cursor()
        cur.execute("PRAGMA index_list('{}')".format(table))
        return [row[1] for row in cur.fetchall()]

    def generate_index_patch(self) -> Optional[Dict[str, Any]]:
        # Heuristics for KE recall: filter by confidence/order by updated_at; alias lookup; ensure FTS triggers already exist
        idx = []
        missing = []
        facts_idx = self.existing_indexes('facts')
        if 'idx_facts_conf_updated' not in facts_idx:
            missing.append("CREATE INDEX IF NOT EXISTS idx_facts_conf_updated ON facts(confidence, updated_at);")
        aliases_idx = self.existing_indexes('fact_aliases')
        if 'idx_fact_aliases_alias' not in aliases_idx:
            missing.append("CREATE INDEX IF NOT EXISTS idx_fact_aliases_alias ON fact_aliases(alias);")
        if not missing:
            return None
        return {
            'type': 'sql_index',
            'target': 'knowledge_db',
            'description': 'Add helpful indexes for recall() filters and alias lookups',
            'patch': missing
        }

    def test_index_patch_in_sandbox(self, sql_statements: List[str], baseline_ms: float, queries: List[str]) -> Dict[str, Any]:
        # Copy DB file via backup into temp path
        import tempfile
        tmp_dir = Path(tempfile.gettempdir()) / "saraphina_improve"
        tmp_dir.mkdir(exist_ok=True)
        # Attempt to locate underlying DB path from connection
        tmp_db = tmp_dir / "test_improve.db"
        try:
            # Use SQLite backup API for a consistent copy
            with sqlite3.connect(str(tmp_db)) as dest:
                self.conn.backup(dest)
        except Exception:
            # Fallback: use in-memory
            tmp_db = None
        # Connect to sandbox DB and apply indexes
        if tmp_db and tmp_db.exists():
            sconn = sqlite3.connect(str(tmp_db))
        else:
            sconn = sqlite3.connect(":memory:")
        sconn.row_factory = sqlite3.Row
        try:
            scur = sconn.cursor()
            # If memory, recreate minimal schema? Try to clone via backup if possible
            if tmp_db is None:
                return {'success': False, 'error': 'sandbox copy failed'}
            for stmt in sql_statements:
                scur.execute(stmt)
            sconn.commit()
            # Measure recall via direct SQL approximations: use LIKE/FTS queries similar to KE
            # For simplicity, we measure a SELECT COUNT(*) with the same WHERE/ORDER as fallback query
            like_q = queries[0] if queries else 'test'
            like = f"%{like_q}%"
            t0 = perf_counter()
            try:
                scur.execute(
                    """
                    SELECT COUNT(1) FROM (
                      SELECT DISTINCT f.id FROM facts f
                      LEFT JOIN fact_aliases a ON a.fact_id = f.id
                      WHERE f.confidence >= ? AND (
                        f.summary LIKE ? OR f.content LIKE ? OR f.topic LIKE ? OR a.alias LIKE ?
                      )
                      ORDER BY f.confidence DESC, f.updated_at DESC
                      LIMIT 5
                    )
                    """,
                    (0.7, like, like, like, like)
                )
                _ = scur.fetchone()
            except Exception:
                pass
            dt_ms = (perf_counter() - t0) * 1000.0
            gain_ms = max(0.0, baseline_ms - dt_ms)
            gain_pct = (gain_ms / baseline_ms * 100.0) if baseline_ms > 0 else 0.0
            return {
                'success': True,
                'after_ms': dt_ms,
                'gain_ms': gain_ms,
                'gain_pct': gain_pct,
            }
        finally:
            try:
                sconn.close()
            except Exception:
                pass
            if tmp_db and tmp_db.exists():
                try:
                    tmp_db.unlink()
                except Exception:
                    pass


class ImprovementLoop:
    def __init__(self, conn: sqlite3.Connection, ke):
        self.conn = conn
        self.ke = ke
        self.db = ImprovementDB(conn)

    def run_once(self) -> Dict[str, Any]:
        policy = ApprovalPolicy.load(self.conn)
        autop = AutoPatch(self.conn, self.ke)

        queries = autop.sample_recent_queries(limit=10)
        baseline_avg_ms, samples = autop.measure_recall_ms(queries)
        result: Dict[str, Any] = {
            'baseline_ms': baseline_avg_ms,
            'samples': samples,
            'patch_created': False
        }
        if baseline_avg_ms < policy.slow_query_ms_threshold:
            result['message'] = 'Recall is within threshold; no action.'
            return result
        # Generate candidate patch (indexes)
        patch = autop.generate_index_patch()
        if not patch:
            result['message'] = 'No missing indexes identified.'
            return result
        # Test in sandbox
        test_res = autop.test_index_patch_in_sandbox(patch['patch'], baseline_avg_ms, queries)
        if not test_res.get('success'):
            result['message'] = f"Sandbox test failed: {test_res.get('error')}"
            return result
        gain_pct = test_res['gain_pct']
        risk_score = 0.1  # creating indexes is low risk
        patch_record = {
            'type': patch['type'],
            'target': patch['target'],
            'description': patch['description'],
            'patch': patch['patch'],
            'status': 'pending',
            'risk_score': risk_score,
            'before_ms': baseline_avg_ms,
            'after_ms': test_res['after_ms'],
            'estimated_gain_ms': test_res['gain_ms'],
            'test_result': test_res,
        }
        patch_id = self.db.create_patch(patch_record)
        result['patch_created'] = True
        result['patch_id'] = patch_id
        result['gain_pct'] = gain_pct
        # Auto-approve/apply if policy allows
        if policy.should_auto_approve(risk_score, gain_pct):
            self.db.set_status(patch_id, 'approved', reviewer='policy')
            apply_res = self.apply_patch(patch_id)
            result['applied'] = apply_res.get('success', False)
            result['apply_result'] = apply_res
        return result

    def apply_patch(self, patch_id: str) -> Dict[str, Any]:
        p = self.db.get_patch(patch_id)
        if not p:
            return {'success': False, 'error': 'patch not found'}
        if p['status'] not in ['approved', 'pending']:
            return {'success': False, 'error': f"invalid status {p['status']}"}
        # For safety, only allow sql_index here
        if p['type'] != 'sql_index':
            return {'success': False, 'error': 'unsupported patch type'}
        cur = self.conn.cursor()
        try:
            cur.execute('BEGIN')
            for stmt in p['patch']:
                cur.execute(stmt)
            self.conn.commit()
            # Measure after apply
            autop = AutoPatch(self.conn, self.ke)
            after_ms, _ = autop.measure_recall_ms(autop.sample_recent_queries(limit=5))
            self.db.mark_applied(patch_id, after_ms=after_ms)
            write_audit_log(self.conn, actor='improvement_loop', action='apply_patch', target=patch_id, details={
                'type': p['type'], 'target': p['target'], 'after_ms': after_ms
            })
            return {'success': True, 'after_ms': after_ms}
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            self.db.set_status(patch_id, 'failed')
            return {'success': False, 'error': str(e)}
