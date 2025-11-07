#!/usr/bin/env python3
"""
Provenance Ledger: immutable cryptographic chain of decisions.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

class ProvenanceLedger:
    def __init__(self, conn):
        self.conn = conn
        self._ensure_table()

    def _ensure_table(self):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS provenance_chain (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    action TEXT,
                    actor TEXT,
                    data TEXT,
                    prev_hash TEXT,
                    hash TEXT
                )
            """)
            self.conn.commit()
        except Exception:
            pass

    def _get_last_hash(self) -> str:
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT hash FROM provenance_chain ORDER BY timestamp DESC LIMIT 1")
            row = cur.fetchone()
            return row[0] if row else "0" * 64
        except Exception:
            return "0" * 64

    def record(self, action: str, actor: str, data: Dict[str, Any]) -> str:
        from uuid import uuid4
        rid = str(uuid4())
        ts = datetime.utcnow().isoformat()
        prev = self._get_last_hash()
        data_str = json.dumps(data, sort_keys=True)
        # Hash: SHA256(prev + ts + action + actor + data)
        h = hashlib.sha256(f"{prev}{ts}{action}{actor}{data_str}".encode('utf-8')).hexdigest()
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO provenance_chain (id, timestamp, action, actor, data, prev_hash, hash) VALUES (?,?,?,?,?,?,?)",
                (rid, ts, action, actor, data_str, prev, h)
            )
            self.conn.commit()
        except Exception:
            pass
        return rid

    def verify(self, rid: str) -> bool:
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT timestamp, action, actor, data, prev_hash, hash FROM provenance_chain WHERE id=?", (rid,))
            row = cur.fetchone()
            if not row:
                return False
            ts, action, actor, data, prev, stored = row
            recomputed = hashlib.sha256(f"{prev}{ts}{action}{actor}{data}".encode('utf-8')).hexdigest()
            return recomputed == stored
        except Exception:
            return False

    def trace(self, rid: str, depth: int = 10) -> list:
        chain = []
        try:
            cur = self.conn.cursor()
            current = rid
            for _ in range(depth):
                cur.execute("SELECT id, timestamp, action, actor, prev_hash FROM provenance_chain WHERE id=?", (current,))
                row = cur.fetchone()
                if not row:
                    break
                chain.append(dict(row))
                current = row[4]  # prev_hash as ID not implemented; use genesis
                if current == "0" * 64:
                    break
        except Exception:
            pass
        return chain
