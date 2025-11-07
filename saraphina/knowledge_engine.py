#!/usr/bin/env python3
"""
KnowledgeEngine - manages facts, recall, links, and query logging using SQLite
"""

import json
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Optional

from .db import init_db, backup_db, write_audit_log, get_preference

try:
    from rapidfuzz.fuzz import ratio as fuzz_ratio
    _RAPIDFUZZ = True
except Exception:
    _RAPIDFUZZ = False

class KnowledgeEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.conn = init_db(db_path)

    def store_fact(self, topic: str, summary: str, content: str, source: str, confidence: float) -> str:
        fact_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO facts (id, topic, summary, content, source, confidence, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (fact_id, topic, summary, content, source, float(confidence), now, now)
        )
        # Initial version record
        version_id = str(uuid4())
        cur.execute(
            "INSERT INTO fact_versions (version_id, fact_id, content, changed_at, reason) VALUES (?,?,?,?,?)",
            (version_id, fact_id, content, now, "initial")
        )
        self.conn.commit()
        # Optional embedding index
        try:
            from .embeddings import EmbeddingIndex
            idx = EmbeddingIndex(self.conn)
            idx.upsert_fact(fact_id, f"{topic} {summary} {content}")
        except Exception:
            pass
        write_audit_log(self.conn, actor="knowledge", action="store_fact", target=fact_id, details={
            "topic": topic, "source": source, "confidence": confidence
        })
        return fact_id

    def recall(self, query: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict]:
        cur = self.conn.cursor()
        results: List[Dict] = []
        # Embedding search (optional)
        embed_scores = {}
        try:
            if (get_preference(self.conn, 'enable_embeddings') == 'true'):
                from .embeddings import EmbeddingIndex
                idx = EmbeddingIndex(self.conn)
                pairs = idx.search(query, top_k=top_k)
                embed_scores = {fid: score for fid, score in pairs}
            else:
                embed_scores = {}
        except Exception:
            embed_scores = {}
        # FTS search
        try:
            q = query.replace('"', ' ').strip()
            cur.execute(
                """
                SELECT f.* FROM facts f
                JOIN facts_fts ff ON f.id = ff.id
                WHERE f.confidence >= ? AND ff MATCH ?
                LIMIT ?
                """,
                (float(threshold), q, int(top_k))
            )
            results = [dict(r) for r in cur.fetchall()]
        except Exception:
            results = []
        # LIKE fallback
        if not results:
            like = f"%{query}%"
            cur.execute(
                """
                SELECT DISTINCT f.* FROM facts f
                LEFT JOIN fact_aliases a ON a.fact_id = f.id
                WHERE f.confidence >= ? AND (
                    f.summary LIKE ? OR f.content LIKE ? OR f.topic LIKE ? OR a.alias LIKE ?
                )
                ORDER BY f.confidence DESC, f.updated_at DESC
                LIMIT ?
                """,
                (float(threshold), like, like, like, like, int(top_k))
            )
            results = [dict(row) for row in cur.fetchall()]
        # Score and annotate
        out: List[Dict] = []
        candidate_pairs: List[Tuple[str, str]] = []
        for r in results:
            text = (r.get('summary') or '') + ' ' + (r.get('content') or '')
            candidate_pairs.append((r['id'], text))
            tf = text.lower().count(query.lower())
            fuzzy = 0.0
            if _RAPIDFUZZ:
                try:
                    fuzzy = max(
                        fuzz_ratio(query, (r.get('summary') or '')),
                        fuzz_ratio(query, (r.get('content') or '')),
                        fuzz_ratio(query, (r.get('topic') or ''))
                    ) / 100.0
                except Exception:
                    fuzzy = 0.0
            score = (
                float(r.get('confidence') or 0) * 0.35 +
                (embed_scores.get(r['id'], 0.0) * 0.35) +
                (0.2 * fuzzy) +
                (0.1 * tf)
            )
            r2 = dict(r)
            r2['score'] = score
            out.append(r2)
        # Cross-encoder rerank boost (optional)
        try:
            if (get_preference(self.conn, 'enable_reranker') == 'true'):
                from .reranker import Reranker
                rr = Reranker()
                re_scores = rr.score(query, candidate_pairs)
                if re_scores:
                    for r in out:
                        r['score'] = 0.7 * r['score'] + 0.3 * re_scores.get(r['id'], 0.0)
        except Exception:
            pass
        # Also add top purely-embedding matches not in FTS results
        ids_present = {r['id'] for r in out}
        for fid, sc in embed_scores.items():
            if fid not in ids_present:
                cur.execute("SELECT * FROM facts WHERE id=?", (fid,))
                row = cur.fetchone()
                if row:
                    d = dict(row)
                    d['score'] = sc
                    out.append(d)
        out.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        return out[:top_k]

    def link_facts(self, a: str, b: str, relation: str) -> str:
        link_id = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO concept_links (id, from_fact, to_fact, relation_type) VALUES (?,?,?,?)",
            (link_id, a, b, relation)
        )
        self.conn.commit()
        write_audit_log(self.conn, actor="knowledge", action="link_facts", target=link_id, details={
            "from": a, "to": b, "relation": relation
        })
        return link_id

    def backup(self, path: str) -> str:
        return backup_db(self.conn, path)

    def log_query(self, text: str, fact_id: Optional[str], response_text: str) -> str:
        qid = str(uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO queries (id, text, fact_id, response_text, timestamp) VALUES (?,?,?,?,?)",
            (qid, text, fact_id, response_text, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return qid
