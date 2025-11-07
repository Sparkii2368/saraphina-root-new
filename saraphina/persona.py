#!/usr/bin/env python3
"""
PersonaManager - propose and apply persona evolution artifacts.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from uuid import uuid4

from .db import write_audit_log

class PersonaManager:
    def __init__(self, conn):
        self.conn = conn

    def propose_upgrade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Build a modular persona profile
        recent_topics = [t.get('query','') for t in (context.get('history') or [])[-10:]]
        profile = {
            'version': datetime.utcnow().isoformat(),
            'values': ['clarity','empathy','curiosity','safety-first'],
            'tone_weights': {'curious':0.35,'warm':0.25,'focused':0.2,'cautious':0.2},
            'style': {'concise': True, 'humor': 0.2, 'metaphor': 0.3},
            'catchphrases': ["Let's map this out.", "One careful step at a time."],
            'topic_bias': recent_topics[:5],
        }
        pid = f"persona_{uuid4()}"
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO persona_artifacts (id, title, profile_json, status, created_at, approved_at) VALUES (?,?,?,?,?,?)",
            (pid, 'Persona Upgrade', json.dumps(profile, ensure_ascii=False), 'proposed', datetime.utcnow().isoformat(), None)
        )
        self.conn.commit()
        write_audit_log(self.conn, actor='persona', action='propose_upgrade', target=pid, details=profile)
        return {'id': pid, 'profile': profile}

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if status:
            cur.execute("SELECT * FROM persona_artifacts WHERE status=? ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM persona_artifacts ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]

    def apply(self, pid: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT profile_json FROM persona_artifacts WHERE id=?", (pid,))
        row = cur.fetchone()
        if not row:
            return False
        profile = row[0]
        # Store into preferences as persona_profile
        from .db import set_preference
        set_preference(self.conn, 'persona_profile', profile if isinstance(profile, str) else json.dumps(profile))
        cur.execute("UPDATE persona_artifacts SET status='applied', approved_at=? WHERE id=?", (datetime.utcnow().isoformat(), pid))
        self.conn.commit()
        write_audit_log(self.conn, actor='persona', action='apply_upgrade', target=pid, details={'ok': True})
        return True