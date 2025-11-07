#!/usr/bin/env python3
"""
Cross-encoder reranker (optional) to improve recall quality.
"""
from typing import Dict, List, Optional, Tuple

try:
    from sentence_transformers import CrossEncoder
    _RE_AVAILABLE = True
except Exception:
    _RE_AVAILABLE = False


class Reranker:
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.available = _RE_AVAILABLE
        self.model: Optional[CrossEncoder] = None
        if _RE_AVAILABLE:
            try:
                self.model = CrossEncoder(model_name)
            except Exception:
                self.model = None
                self.available = False

    def score(self, query: str, candidates: List[Tuple[str, str]]) -> Dict[str, float]:
        """Score (id, text) candidates against query; returns id->score in [0,1]."""
        if not (self.available and self.model and candidates):
            return {}
        pairs = [(query, text) for _, text in candidates]
        try:
            scores = self.model.predict(pairs)
            # Normalize to [0,1]
            mx = max(1e-6, max(scores))
            mn = min(scores)
            norm = [(s - mn) / (mx - mn) if mx > mn else 0.0 for s in scores]
            return {cid: float(sc) for (cid, _), sc in zip(candidates, norm)}
        except Exception:
            return {}
