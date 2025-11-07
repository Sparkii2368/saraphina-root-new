#!/usr/bin/env python3
"""
ImprovementDB - Store and manage auto-improvement patches and results.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sqlite3


class ImprovementDB:
    """Persistence for improvement patches in the primary knowledge DB."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_patches (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              type TEXT NOT NULL,            -- e.g., sql_index, code_patch
              target TEXT NOT NULL,          -- e.g., table/module name
              description TEXT,
              patch TEXT NOT NULL,           -- SQL or code payload (JSON if multiple)
              status TEXT NOT NULL,          -- pending, approved, applied, rejected, failed
              risk_score REAL DEFAULT 0.0,
              before_ms REAL,
              after_ms REAL,
              estimated_gain_ms REAL,
              test_result TEXT,              -- JSON
              applied_at TEXT,
              approved_at TEXT,
              reviewer TEXT
            )
            """
        )
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_impr_status ON improvement_patches(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_impr_type ON improvement_patches(type)")
        except Exception:
            pass
        self.conn.commit()

    def create_patch(self, patch: Dict[str, Any]) -> str:
        cur = self.conn.cursor()
        patch_id = patch.get('id') or f"patch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        cur.execute(
            """
            INSERT INTO improvement_patches
            (id, created_at, type, target, description, patch, status, risk_score,
             before_ms, after_ms, estimated_gain_ms, test_result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patch_id,
                datetime.utcnow().isoformat(),
                patch['type'],
                patch['target'],
                patch.get('description', ''),
                json.dumps(patch['patch']) if not isinstance(patch['patch'], str) else patch['patch'],
                patch.get('status', 'pending'),
                float(patch.get('risk_score', 0.0)),
                float(patch.get('before_ms') or 0.0),
                float(patch.get('after_ms') or 0.0),
                float(patch.get('estimated_gain_ms') or 0.0),
                json.dumps(patch.get('test_result', {}))
            )
        )
        self.conn.commit()
        return patch_id

    def set_status(self, patch_id: str, status: str, reviewer: Optional[str] = None):
        cur = self.conn.cursor()
        fields = ["status = ?"]
        params: List[Any] = [status]
        if status == 'approved':
            fields.append("approved_at = ?")
            params.append(datetime.utcnow().isoformat())
        if reviewer:
            fields.append("reviewer = ?")
            params.append(reviewer)
        params.append(patch_id)
        cur.execute(f"UPDATE improvement_patches SET {', '.join(fields)} WHERE id = ?", params)
        self.conn.commit()

    def mark_applied(self, patch_id: str, after_ms: Optional[float] = None):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE improvement_patches SET status='applied', applied_at=?, after_ms=? WHERE id=?",
            (datetime.utcnow().isoformat(), after_ms, patch_id)
        )
        self.conn.commit()

    def list_patches(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if status:
            cur.execute(
                "SELECT * FROM improvement_patches WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            )
        else:
            cur.execute(
                "SELECT * FROM improvement_patches ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d['patch'] = json.loads(d['patch'])
            except Exception:
                pass
            try:
                d['test_result'] = json.loads(d['test_result'] or '{}')
            except Exception:
                d['test_result'] = {}
            out.append(d)
        return out

    def get_patch(self, patch_id: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM improvement_patches WHERE id=?", (patch_id,))
        r = cur.fetchone()
        if not r:
            return None
        d = dict(r)
        try:
            d['patch'] = json.loads(d['patch'])
        except Exception:
            pass
        try:
            d['test_result'] = json.loads(d['test_result'] or '{}')
        except Exception:
            d['test_result'] = {}
        return d
