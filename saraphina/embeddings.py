#!/usr/bin/env python3
"""
Embeddings support (optional) using sentence-transformers.
- Stores vectors in fact_vectors as JSON list of floats
- Provides search by cosine similarity
"""
import json
import math
from typing import List, Dict, Optional, Tuple

try:
    from sentence_transformers import SentenceTransformer
    _MODEL_AVAILABLE = True
except Exception:
    _MODEL_AVAILABLE = False


class EmbeddingIndex:
    def __init__(self, conn, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.conn = conn
        self.model: Optional[SentenceTransformer] = None
        if _MODEL_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None

    def _encode(self, text: str) -> Optional[List[float]]:
        if not self.model:
            return None
        v = self.model.encode([text], normalize_embeddings=True)
        return v[0].tolist() if hasattr(v, 'tolist') else list(v[0])

    def upsert_fact(self, fact_id: str, text: str) -> bool:
        vec = self._encode(text)
        if vec is None:
            return False
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO fact_vectors (fact_id, vector_json, updated_at) VALUES (?,?,datetime('now'))",
            (fact_id, json.dumps(vec))
        )
        self.conn.commit()
        return True

    def _cosine(self, a: List[float], b: List[float]) -> float:
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        qv = self._encode(query)
        if qv is None:
            return []
        cur = self.conn.cursor()
        cur.execute("SELECT fact_id, vector_json FROM fact_vectors")
        scores: List[Tuple[str, float]] = []
        for fid, vjson in cur.fetchall():
            try:
                v = json.loads(vjson)
                s = self._cosine(qv, v)
                scores.append((fid, float(s)))
            except Exception:
                pass
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
