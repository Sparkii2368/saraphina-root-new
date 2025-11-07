#!/usr/bin/env python3
"""
Learning Journal and Meta-Optimizer for Saraphina.
"""
from __future__ import annotations
import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, List

from .db import write_audit_log

class LearningJournal:
    def __init__(self, conn):
        self.conn = conn

    def add_entry(self, query: str, response: str, strategy: str, success: float, notes: str = '', metrics: Dict = None) -> str:
        lid = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO learning_journal (id, timestamp, query, response, strategy, success, notes, metrics) VALUES (?,?,?,?,?,?,?,?)",
            (lid, datetime.utcnow().isoformat(), query, response, strategy, float(success), notes, json.dumps(metrics or {}))
        )
        self.conn.commit()
        write_audit_log(self.conn, 'journal', 'add_entry', lid, {'strategy': strategy, 'success': success})
        return lid

    def recent(self, limit: int = 10) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM learning_journal ORDER BY timestamp DESC LIMIT ?", (int(limit),))
        return [dict(r) for r in cur.fetchall()]

    def stats(self) -> Dict[str, Dict[str, float]]:
        cur = self.conn.cursor()
        cur.execute("SELECT strategy, COUNT(*), AVG(success) FROM learning_journal GROUP BY strategy")
        out: Dict[str, Dict[str, float]] = {}
        for strat, cnt, avg in cur.fetchall():
            out[strat or 'unknown'] = {'count': float(cnt or 0), 'avg_success': float(avg or 0.0)}
        return out

class MetaOptimizer:
    def review(self, stats: Dict[str, Dict[str, float]]) -> Dict:
        if not stats:
            return {'action': 'none', 'reason': 'no data'}
        # pick best strategy by avg_success
        best = max(stats.items(), key=lambda kv: kv[1].get('avg_success', 0.0))
        return {'action': 'prefer_strategy', 'strategy': best[0], 'confidence': best[1].get('avg_success', 0.0)}

    def apply(self, ultra_core, suggestion: Dict) -> bool:
        try:
            if suggestion.get('action') == 'prefer_strategy':
                strat = suggestion.get('strategy')
                if strat and strat in ultra_core.meta_learner.learning_strategies:
                    # boost effectiveness slightly
                    ultra_core.meta_learner.learning_strategies[strat]['effectiveness'] = min(1.0, ultra_core.meta_learner.learning_strategies[strat]['effectiveness'] + 0.05)
                    return True
            return False
        except Exception:
            return False
