#!/usr/bin/env python3
"""
IntuitionEngine - surfaces non-obvious connections ("hunches") using graph centrality and lexical overlap.
Also exports a knowledge graph for visualization.
"""
from __future__ import annotations
import re
import math
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime

class IntuitionEngine:
    def __init__(self, conn):
        self.conn = conn

    def _fetch_facts(self, topic: Optional[str], limit: int) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if topic:
            cur.execute("SELECT id, topic, summary, content, confidence, updated_at FROM facts WHERE topic=? ORDER BY updated_at DESC LIMIT ?", (topic, int(limit)))
        else:
            cur.execute("SELECT id, topic, summary, content, confidence, updated_at FROM facts ORDER BY updated_at DESC LIMIT ?", (int(limit),))
        return [dict(r) for r in cur.fetchall()]

    def _fetch_links(self) -> List[Tuple[str,str,str]]:
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT from_fact, to_fact, relation_type FROM concept_links")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except Exception:
            return []

    @staticmethod
    def _tokens(text: str) -> Set[str]:
        toks = re.findall(r"[a-zA-Z0-9_#+.-]{3,}", (text or '').lower())
        # Stopwords minimal
        stop = set(['the','and','for','with','from','that','this','have','has','are','was','were','into','onto','your','you','our'])
        return {t for t in toks if t not in stop}

    def export_graph(self, topic: Optional[str] = None, limit: int = 300) -> Dict[str, Any]:
        facts = self._fetch_facts(topic, limit)
        ids = {f['id'] for f in facts}
        id_to_idx = {fid: i for i, fid in enumerate(ids)}
        nodes = []
        for f in facts:
            nodes.append({
                'id': f['id'],
                'label': (f.get('summary') or f.get('content') or '')[:60],
                'topic': f.get('topic') or '',
                'confidence': float(f.get('confidence') or 0.0),
            })
        links_raw = self._fetch_links()
        links = []
        for a, b, rel in links_raw:
            if a in ids and b in ids:
                links.append({'source': a, 'target': b, 'relation': rel or 'related'})
        return {'nodes': nodes, 'links': links}

    def suggest_links(self, topic: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        facts = self._fetch_facts(topic, 500)
        if not facts:
            return []
        # Build token maps and degrees
        tokens = {f['id']: self._tokens((f.get('summary') or '') + ' ' + (f.get('content') or '')) for f in facts}
        links = self._fetch_links()
        adj: Dict[str, Set[str]] = {}
        for a, b, _ in links:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        deg = {f['id']: len(adj.get(f['id'], set())) for f in facts}
        # Precompute degrees normalized
        max_deg = max(deg.values()) if deg else 1
        suggestions: List[Tuple[float, str, str, str]] = []
        ids = [f['id'] for f in facts]
        meta = {f['id']: f for f in facts}
        n = len(ids)
        # Compare pairs with shared topic or token overlap, skip existing links
        for i in range(n):
            a = ids[i]
            for j in range(i+1, n):
                b = ids[j]
                if b in adj.get(a, set()):
                    continue
                ta = tokens.get(a, set()); tb = tokens.get(b, set())
                if not ta or not tb:
                    continue
                inter = len(ta & tb); union = len(ta | tb)
                if union == 0:
                    continue
                jacc = inter / union
                same_topic = (meta[a].get('topic') and meta[a].get('topic') == meta[b].get('topic'))
                if jacc < 0.08 and not same_topic:
                    continue
                score = 0.6 * jacc + 0.2 * (deg.get(a,0)/max_deg) + 0.2 * (deg.get(b,0)/max_deg)
                reason = 'shared_topic' if same_topic else 'lexical_overlap'
                suggestions.append((score, a, b, reason))
        suggestions.sort(key=lambda x: x[0], reverse=True)
        out = []
        for sc, a, b, reason in suggestions[:limit]:
            out.append({
                'from': a,
                'to': b,
                'relation': 'related',
                'score': float(round(sc,4)),
                'reason': reason,
                'from_summary': (meta[a].get('summary') or meta[a].get('content') or '')[:80],
                'to_summary': (meta[b].get('summary') or meta[b].get('content') or '')[:80],
            })
        return out