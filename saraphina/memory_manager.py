#!/usr/bin/env python3
"""
Memory manager for episodic/semantic memory and reminders.
"""
import json
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Optional

from .db import init_db

class MemoryManager:
    def __init__(self, conn):
        self.conn = conn
        self.stopwords = set(['the','a','an','of','and','to','in','for','on','with','at','by','from','about','is','it','this','that','you','i','we','they','he','she','as','or','be','are','am'])

    def add_episodic(self, speaker: str, text: str, mood: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        eid = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO episodic_memory (id, timestamp, speaker, text, mood, tags) VALUES (?,?,?,?,?,?)",
            (eid, datetime.utcnow().isoformat(), speaker, text, mood or '', json.dumps(tags or []))
        )
        self.conn.commit()
        return eid

    def add_semantic(self, keyphrase: str, summary: str, importance: float = 0.5) -> str:
        sid = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO semantic_memory (id, keyphrase, summary, importance, last_refreshed) VALUES (?,?,?,?,?)",
            (sid, keyphrase, summary, float(importance), datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return sid

    def list_recent_episodic(self, limit: int = 20) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM episodic_memory ORDER BY timestamp DESC LIMIT ?", (int(limit),))
        return [dict(r) for r in cur.fetchall()]

    def add_reminder(self, text: str, due_ts: str) -> str:
        rid = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO reminders (id, text, due_ts, status, created_at) VALUES (?,?,?,?,?)",
            (rid, text, due_ts, 'pending', datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return rid

    def due_reminders(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM reminders WHERE status='pending' AND due_ts <= datetime('now') ORDER BY due_ts ASC")
        return [dict(r) for r in cur.fetchall()]

    def consolidate_daily(self) -> int:
        """Summarize recent episodic into semantic keyphrases/summaries.
        Returns count of semantic entries added.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT text FROM episodic_memory WHERE speaker='user' AND timestamp >= datetime('now','-1 day') ORDER BY timestamp ASC")
        rows = [r[0] for r in cur.fetchall()]
        if not rows:
            return 0
        # naive keyphrase extraction
        freq = {}
        for t in rows:
            for w in (''.join([c.lower() if c.isalnum() else ' ' for c in t]).split()):
                if len(w) < 4 or w in self.stopwords:
                    continue
                freq[w] = freq.get(w, 0) + 1
        keyphrases = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        count = 0
        now = datetime.utcnow().isoformat()
        for k, _ in keyphrases:
            sid = str(uuid4())
            summary = f"Recent focus on '{k}': {sum(1 for t in rows if k in t.lower())} mentions"
            cur.execute(
                "INSERT INTO semantic_memory (id, keyphrase, summary, importance, last_refreshed) VALUES (?,?,?,?,?)",
                (sid, k, summary, 0.6, now)
            )
            count += 1
        self.conn.commit()
        return count

    def mark_reminder_done(self, rid: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("UPDATE reminders SET status='done' WHERE id=?", (rid,))
        self.conn.commit()
        return cur.rowcount > 0
