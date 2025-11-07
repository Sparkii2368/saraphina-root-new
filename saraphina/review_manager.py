#!/usr/bin/env python3
"""
ReviewManager - manage manual review queue (OOD queries, high-risk code)
"""
import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional

from .db import init_db

class ReviewManager:
    def __init__(self, db_path: Optional[str] = None):
        self.conn = init_db(db_path)

    def enqueue(self, item_type: str, reason: str, payload: Dict[str, Any]) -> str:
        rid = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO review_queue (id, item_type, reason, payload, status, created_at, reviewed_at) VALUES (?,?,?,?,?,?,?)",
            (rid, item_type, reason, json.dumps(payload, ensure_ascii=False), 'pending', datetime.utcnow().isoformat(), None)
        )
        self.conn.commit()
        return rid

    def list(self, status: Optional[str] = 'pending') -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if status:
            cur.execute("SELECT * FROM review_queue WHERE status=? ORDER BY created_at ASC", (status,))
        else:
            cur.execute("SELECT * FROM review_queue ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get(self, rid: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM review_queue WHERE id=?", (rid,))
        row = cur.fetchone()
        return dict(row) if row else None

    def set_status(self, rid: str, status: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE review_queue SET status=?, reviewed_at=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), rid)
        )
        self.conn.commit()
        return cur.rowcount > 0
