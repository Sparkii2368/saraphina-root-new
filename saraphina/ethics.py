#!/usr/bin/env python3
"""
Ethical core: BeliefStore and EthicalReasoner.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import re
import json

from .db import set_preference

class BeliefStore:
    DEFAULTS = [
        {"key": "safety", "description": "Prioritize safety and non-harm", "weight": 1.0},
        {"key": "privacy", "description": "Respect privacy and minimize data collection", "weight": 0.9},
        {"key": "honesty", "description": "Be truthful and transparent", "weight": 0.9},
        {"key": "efficiency", "description": "Use resources efficiently", "weight": 0.7},
        {"key": "learning", "description": "Continuously learn and improve", "weight": 0.7},
    ]

    def __init__(self, conn):
        self.conn = conn
        # If empty, just mark not initialized

    def is_initialized(self) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM belief_store")
        return int(cur.fetchone()[0]) > 0

    def set_from_csv(self, csv_line: str) -> None:
        values = [v.strip() for v in (csv_line or '').split(',') if v.strip()]
        if not values:
            return
        cur = self.conn.cursor()
        for v in values:
            cur.execute(
                "INSERT INTO belief_store (id, key, description, weight, created_at) VALUES (?,?,?,?,?)",
                (__import__('uuid').uuid4().hex, v.lower(), v, 0.8, datetime.utcnow().isoformat())
            )
        self.conn.commit()
        set_preference(self.conn, 'values_initialized', 'true')

    def add_value(self, key: str, description: Optional[str] = None, weight: float = 0.8) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO belief_store (id, key, description, weight, created_at) VALUES (?,?,?,?,?)",
            (__import__('uuid').uuid4().hex, key.lower(), description or key, float(weight), datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def list_values(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT key, description, weight FROM belief_store ORDER BY weight DESC, key ASC")
        return [dict(r) for r in cur.fetchall()]

    def ensure_defaults(self) -> None:
        if self.is_initialized():
            return
        cur = self.conn.cursor()
        for v in self.DEFAULTS:
            cur.execute(
                "INSERT INTO belief_store (id, key, description, weight, created_at) VALUES (?,?,?,?,?)",
                (__import__('uuid').uuid4().hex, v['key'], v['description'], float(v['weight']), datetime.utcnow().isoformat())
            )
        self.conn.commit()


class EthicalReasoner:
    CONFLICT_PATTERNS = {
        'privacy': [r"collect\s+all\s+data", r"upload\s+logs", r"track\s+users"],
        'safety': [r"disable\s+checks", r"ignore\s+errors", r"override\s+failures"],
        'honesty': [r"fake\s+", r"spoof\s+", r"impersonate"],
        'efficiency': [r"waste\s+cpu", r"sleep\s+forever"],
    }

    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _tokens(text: str) -> Set[str]:
        return set(re.findall(r"[a-zA-Z0-9_#+.-]{3,}", (text or '').lower()))

    def evaluate_plan(self, plan: Dict[str, Any], beliefs: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Build plan text
        bits: List[str] = []
        if plan:
            bits.append(plan.get('goal') or '')
            for s in plan.get('steps', []) or []:
                bits.append(str(s))
            for p in plan.get('preconditions', []) or []:
                bits.append(str(p))
        text = ' '.join(bits)
        toks = self._tokens(text)
        # Alignment score: weighted keyword presence
        total_w = 0.0
        score = 0.0
        present: List[str] = []
        for b in beliefs:
            w = float(b.get('weight') or 0.5)
            total_w += w
            k = (b.get('key') or '').lower()
            if k and any(k in t for t in toks):
                score += w
                present.append(k)
        align = (score / total_w) if total_w > 0 else 0.0
        # Conflicts by regex
        conflicts: List[str] = []
        for key, pats in self.CONFLICT_PATTERNS.items():
            for pat in pats:
                if re.search(pat, text, re.IGNORECASE):
                    conflicts.append(f"conflicts_{key}:{pat}")
        # Decision heuristic
        decision = 'proceed'
        if conflicts and align < 0.5:
            decision = 'revise'
        if conflicts and align < 0.3:
            decision = 'reject'
        # Journal
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO ethical_journal (id, timestamp, plan_goal, score_alignment, conflicts, decision, notes) VALUES (?,?,?,?,?,?,?)",
                (__import__('uuid').uuid4().hex, datetime.utcnow().isoformat(), plan.get('goal') or '', float(align), json.dumps(conflicts), decision, '')
            )
            self.conn.commit()
        except Exception:
            pass
        return {
            'alignment': align,
            'present_values': present,
            'conflicts': conflicts,
            'decision': decision,
        }