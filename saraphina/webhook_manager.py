#!/usr/bin/env python3
"""
WebhookManager: event-driven HTTP notifications with retry logic.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class WebhookManager:
    def __init__(self, conn):
        self.conn = conn
        self._ensure_table()

    def _ensure_table(self):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id TEXT PRIMARY KEY,
                    event_type TEXT,
                    url TEXT,
                    active INTEGER,
                    created_at TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    id TEXT PRIMARY KEY,
                    webhook_id TEXT,
                    timestamp TEXT,
                    payload TEXT,
                    status INTEGER,
                    response TEXT
                )
            """)
            self.conn.commit()
        except Exception:
            pass

    def register(self, event_type: str, url: str) -> str:
        from uuid import uuid4
        wid = str(uuid4())
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO webhooks (id, event_type, url, active, created_at) VALUES (?,?,?,?,?)",
                (wid, event_type, url, 1, datetime.utcnow().isoformat())
            )
            self.conn.commit()
        except Exception:
            pass
        return wid

    def send(self, event_type: str, payload: Dict[str, Any], max_retries: int = 3) -> None:
        try:
            import requests
        except Exception:
            return
        cur = self.conn.cursor()
        cur.execute("SELECT id, url FROM webhooks WHERE event_type=? AND active=1", (event_type,))
        hooks = cur.fetchall()
        for hook in hooks:
            wid, url = hook[0], hook[1]
            for attempt in range(max_retries):
                try:
                    r = requests.post(url, json=payload, timeout=10)
                    status = r.status_code
                    resp = r.text[:500]
                    self._log_delivery(wid, payload, status, resp)
                    if status < 500:
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        self._log_delivery(wid, payload, 0, str(e))

    def _log_delivery(self, webhook_id: str, payload: Dict[str, Any], status: int, response: str):
        from uuid import uuid4
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO webhook_deliveries (id, webhook_id, timestamp, payload, status, response) VALUES (?,?,?,?,?,?)",
                (str(uuid4()), webhook_id, datetime.utcnow().isoformat(), json.dumps(payload), status, response)
            )
            self.conn.commit()
        except Exception:
            pass
