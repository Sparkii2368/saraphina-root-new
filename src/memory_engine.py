#!/usr/bin/env python3
"""
Memory Engine for Saraphina
Handles short-term (in-memory), mid-term (JSON), long-term (SQLite with embeddings) memory.
"""

import json
import sqlite3
import random
import time
import numpy as np
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util  # For embeddings

MEMORY_DIR = Path("D:/Saraphina Root/data/memories")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
MID_TERM_FILE = MEMORY_DIR / "mid_term.json"
LONG_TERM_DB = MEMORY_DIR / "long_term.db"


class MemoryEngine:
    def __init__(self):
        self.short_term: List[Dict] = []  # In-memory list, recent interactions
        self.mid_term = self._load_mid_term()  # JSON for sessions
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._init_long_term_db()

    def _load_mid_term(self) -> List[Dict]:
        if MID_TERM_FILE.exists():
            with open(MID_TERM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_mid_term(self):
        with open(MID_TERM_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.mid_term, f, indent=2)

    def _init_long_term_db(self):
        conn = sqlite3.connect(str(LONG_TERM_DB))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS long_term (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_text TEXT,
                embedding BLOB,
                importance FLOAT,
                ts REAL
            )
        """)
        conn.commit()
        conn.close()

    def store_memory(self, text: str, type: str = "short", importance: float = 0.5):
        entry = {"text": text, "importance": importance, "ts": time.time()}
        if type == "short":
            self.short_term.append(entry)
            if len(self.short_term) > 10:  # Limit short-term
                self.short_term.pop(0)
        elif type == "mid":
            self.mid_term.append(entry)
            self._save_mid_term()
        elif type == "long":
            embedding = self.embedding_model.encode(text).astype(np.float32).tobytes()
            conn = sqlite3.connect(str(LONG_TERM_DB))
            conn.execute(
                "INSERT INTO long_term (memory_text, embedding, importance, ts) "
                "VALUES (?, ?, ?, ?)",
                (text, embedding, importance, time.time()),
            )
            conn.commit()
            conn.close()

    def recall_relevant_memories(self, query: str, top_k: int = 3) -> List[str]:
        # Short and mid: simple string match
        short_hits = [m["text"] for m in self.short_term if query.lower() in m["text"].lower()]
        mid_hits = [m["text"] for m in self.mid_term if query.lower() in m["text"].lower()]

        # Long: semantic search
        long_hits: List[str] = []
        try:
            query_emb = self.embedding_model.encode(query)
            conn = sqlite3.connect(str(LONG_TERM_DB))
            cur = conn.cursor()
            cur.execute("SELECT memory_text, embedding FROM long_term")
            rows = cur.fetchall()
            scored = []
            for text, emb_bytes in rows:
                emb = np.frombuffer(emb_bytes, dtype=np.float32)
                sim = float(util.cos_sim(query_emb, emb)[0][0])
                if sim > 0.5:
                    scored.append((sim, text))
            scored.sort(reverse=True, key=lambda x: x[0])
            long_hits = [text for _sim, text in scored[:top_k]]
            conn.close()
        except Exception:
            pass

        return short_hits + mid_hits + long_hits

    def summarize_session_history(self) -> str:
        history = [m["text"] for m in self.short_term + self.mid_term]
        if not history:
            return "No history yet."
        return " ".join(random.sample(history, min(3, len(history))))

    def long_term_count(self) -> int:
        """Safe count of long-term entries for GUI."""
        try:
            conn = sqlite3.connect(str(LONG_TERM_DB))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM long_term")
            cnt = cur.fetchone()[0]
            conn.close()
            return int(cnt)
        except Exception:
            return 0