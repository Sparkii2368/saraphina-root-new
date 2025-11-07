#!/usr/bin/env python3
"""
KnowledgeGraphExplorer - Advanced knowledge graph analysis with natural insight generation.
Surfaces non-obvious connections using multiple algorithms:
- Semantic similarity
- Graph centrality (PageRank, betweenness)
- Community detection
- Path analysis
"""
from __future__ import annotations
import re
import math
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import random


class KnowledgeGraphExplorer:
    def __init__(self, conn):
        self.conn = conn
        
    def _fetch_facts(self, topic: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        """Fetch facts from database with optional topic filter."""
        cur = self.conn.cursor()
        if topic:
            cur.execute(
                "SELECT id, topic, summary, content, confidence, updated_at FROM facts WHERE topic=? ORDER BY updated_at DESC LIMIT ?",
                (topic, int(limit))
            )
        else:
            cur.execute(
                "SELECT id, topic, summary, content, confidence, updated_at FROM facts ORDER BY updated_at DESC LIMIT ?",
                (int(limit),)
            )
        return [dict(r) for r in cur.fetchall()]
    
    def _fetch_links(self) -> List[Tuple[str, str, str]]:
        """Fetch all concept links from database."""
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT from_fact, to_fact, relation_type FROM concept_links")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except Exception:
            return []
    
    def _fetch_queries(self) -> List[Dict[str, Any]]:
        """Fetch query history for usage patterns."""
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT fact_id, text, timestamp FROM queries ORDER BY timestamp DESC LIMIT 1000")
            return [dict(r) for r in cur.fetchall()]
        except Exception:
            return []
    
    @staticmethod
    def _tokens(text: str) -> Set[str]:
        """Extract meaningful tokens from text."""
        toks = re.findall(r"[a-zA-Z0-9_#+.-]{3,}", (text or '').lower())
        stop = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'have', 'has', 
                'are', 'was', 'were', 'into', 'onto', 'your', 'you', 'our', 'will', 'can'}
        return {t for t in toks if t not in stop}
    
    def build_graph(self, topic: Optional[str] = None, limit: int = 500) -> Dict[str, Any]:
        """Build full graph structure with nodes and edges."""
        facts = self._fetch_facts(topic, limit)
        links = self._fetch_links()
        queries = self._fetch_queries()
        
        # Build adjacency
        adj = defaultdict(set)
        edges = []
        for a, b, rel in links:
            adj[a].add(b)
            adj[b].add(a)
            edges.append({'from': a, 'to': b, 'relation': rel or 'related'})
        
        # Calculate query frequency
        query_freq = Counter(q['fact_id'] for q in queries if q.get('fact_id'))
        
        # Build nodes with metadata
        nodes = []
        for f in facts:
            fid = f['id']
            nodes.append({
                'id': fid,
                'label': (f.get('summary') or f.get('content') or '')[:60],
                'topic': f.get('topic') or 'general',
                'confidence': float(f.get('confidence') or 0.0),
                'degree': len(adj.get(fid, set())),
                'query_count': query_freq.get(fid, 0),
                'updated_at': f.get('updated_at', ''),
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'topics': list(set(n['topic'] for n in nodes)),
                'avg_degree': sum(n['degree'] for n in nodes) / len(nodes) if nodes else 0,
            }
        }
    
    def pagerank(self, graph: Dict[str, Any], iterations: int = 20, damping: float = 0.85) -> Dict[str, float]:
        """Calculate PageRank scores for nodes."""
        nodes = {n['id']: n for n in graph['nodes']}
        n_nodes = len(nodes)
        if n_nodes == 0:
            return {}
        
        # Build adjacency for outgoing links
        out_links = defaultdict(list)
        for e in graph['edges']:
            out_links[e['from']].append(e['to'])
        
        # Initialize scores
        scores = {nid: 1.0 / n_nodes for nid in nodes}
        
        for _ in range(iterations):
            new_scores = {}
            for nid in nodes:
                rank_sum = 0.0
                # Sum contributions from incoming links
                for other in nodes:
                    if nid in out_links[other]:
                        out_count = len(out_links[other])
                        if out_count > 0:
                            rank_sum += scores[other] / out_count
                new_scores[nid] = (1 - damping) / n_nodes + damping * rank_sum
            scores = new_scores
        
        return scores
    
    def find_shortest_path(self, graph: Dict[str, Any], start: str, end: str) -> Optional[List[str]]:
        """Find shortest path between two nodes using BFS."""
        if start == end:
            return [start]
        
        # Build adjacency
        adj = defaultdict(set)
        for e in graph['edges']:
            adj[e['from']].add(e['to'])
            adj[e['to']].add(e['from'])
        
        if start not in adj or end not in adj:
            return None
        
        # BFS
        queue = [(start, [start])]
        visited = {start}
        
        while queue:
            node, path = queue.pop(0)
            for neighbor in adj[node]:
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def discover_insights(self, query: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Discover non-obvious insights using multiple techniques.
        Returns insights with natural language explanations.
        """
        graph = self.build_graph()
        if not graph['nodes'] or not graph['edges']:
            return []
        
        nodes_map = {n['id']: n for n in graph['nodes']}
        
        # Calculate PageRank for importance
        pr_scores = self.pagerank(graph)
        
        # Extract tokens for semantic analysis
        tokens_map = {}
        for n in graph['nodes']:
            text = (n.get('label') or '') + ' ' + nodes_map[n['id']].get('topic', '')
            tokens_map[n['id']] = self._tokens(text)
        
        insights = []
        
        # Strategy 1: High PageRank nodes with shared semantic space
        top_pr = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)[:20]
        for i, (id1, pr1) in enumerate(top_pr):
            for id2, pr2 in top_pr[i+1:]:
                if id1 == id2:
                    continue
                
                # Check if they're connected
                connected = any(e for e in graph['edges'] if 
                              (e['from'] == id1 and e['to'] == id2) or
                              (e['from'] == id2 and e['to'] == id1))
                
                if not connected:
                    # Calculate semantic overlap
                    tokens1 = tokens_map.get(id1, set())
                    tokens2 = tokens_map.get(id2, set())
                    if not tokens1 or not tokens2:
                        continue
                    
                    overlap = tokens1 & tokens2
                    if len(overlap) >= 2:  # At least 2 shared concepts
                        # Find indirect path
                        path = self.find_shortest_path(graph, id1, id2)
                        
                        node1 = nodes_map[id1]
                        node2 = nodes_map[id2]
                        
                        # Generate natural explanation
                        shared_concepts = ', '.join(list(overlap)[:3])
                        explanation = self._generate_insight_explanation(
                            node1, node2, shared_concepts, path, pr1, pr2
                        )
                        
                        insights.append({
                            'from_id': id1,
                            'to_id': id2,
                            'from_label': node1['label'],
                            'to_label': node2['label'],
                            'from_topic': node1['topic'],
                            'to_topic': node2['topic'],
                            'shared_concepts': list(overlap),
                            'pagerank_from': round(pr1, 4),
                            'pagerank_to': round(pr2, 4),
                            'path_length': len(path) if path else None,
                            'explanation': explanation,
                            'confidence': self._calculate_insight_confidence(pr1, pr2, len(overlap), path)
                        })
        
        # Strategy 2: Cross-topic bridges (high betweenness)
        topic_bridges = self._find_topic_bridges(graph, nodes_map, tokens_map)
        insights.extend(topic_bridges)
        
        # Sort by confidence and filter by query if provided
        insights.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        if query:
            query_tokens = self._tokens(query)
            # Filter insights relevant to query
            filtered = []
            for ins in insights:
                shared = query_tokens & set(ins.get('shared_concepts', []))
                if shared or any(q in ins.get('explanation', '').lower() for q in query_tokens):
                    filtered.append(ins)
            insights = filtered
        
        return insights[:limit]
    
    def _find_topic_bridges(self, graph: Dict[str, Any], nodes_map: Dict, tokens_map: Dict) -> List[Dict[str, Any]]:
        """Find nodes that bridge different topics."""
        bridges = []
        
        # Group nodes by topic
        topics = defaultdict(list)
        for n in graph['nodes']:
            topics[n['topic']].append(n['id'])
        
        # Find cross-topic connections
        for e in graph['edges']:
            from_node = nodes_map.get(e['from'])
            to_node = nodes_map.get(e['to'])
            
            if not from_node or not to_node:
                continue
            
            if from_node['topic'] != to_node['topic']:
                # This is a bridge!
                tokens1 = tokens_map.get(e['from'], set())
                tokens2 = tokens_map.get(e['to'], set())
                overlap = tokens1 & tokens2
                
                if overlap:
                    explanation = f"I notice a bridge between {from_node['topic']} and {to_node['topic']}. "
                    explanation += f"They share concepts like: {', '.join(list(overlap)[:3])}. "
                    explanation += f"This cross-domain connection might reveal a transferable pattern."
                    
                    bridges.append({
                        'from_id': e['from'],
                        'to_id': e['to'],
                        'from_label': from_node['label'],
                        'to_label': to_node['label'],
                        'from_topic': from_node['topic'],
                        'to_topic': to_node['topic'],
                        'shared_concepts': list(overlap),
                        'explanation': explanation,
                        'confidence': 0.75,
                        'insight_type': 'topic_bridge'
                    })
        
        return bridges
    
    def _generate_insight_explanation(self, node1: Dict, node2: Dict, shared: str, 
                                     path: Optional[List], pr1: float, pr2: float) -> str:
        """Generate natural language explanation for an insight."""
        explanations = [
            f"I'm sensing a connection between '{node1['label'][:40]}' and '{node2['label'][:40]}'. Both involve {shared}.",
            f"Here's an interesting pattern: {node1['topic']} and {node2['topic']} intersect around {shared}.",
            f"I notice '{node1['label'][:40]}' relates to '{node2['label'][:40]}' through {shared}.",
            f"These two concepts share common ground in {shared}, even though they seem unrelated at first.",
        ]
        
        explanation = random.choice(explanations)
        
        if path and len(path) > 2:
            explanation += f" There's an indirect path through {len(path)-2} intermediate concept(s)."
        
        if pr1 > 0.02 or pr2 > 0.02:
            explanation += " This could be a key insight since both are central to the knowledge graph."
        
        return explanation
    
    def _calculate_insight_confidence(self, pr1: float, pr2: float, overlap_count: int, 
                                     path: Optional[List]) -> float:
        """Calculate confidence score for an insight."""
        # Base confidence from PageRank importance
        importance = (pr1 + pr2) * 10
        
        # Bonus for semantic overlap
        semantic = min(overlap_count * 0.15, 0.5)
        
        # Penalty for very long paths (might be spurious)
        path_penalty = 0
        if path and len(path) > 5:
            path_penalty = (len(path) - 5) * 0.05
        
        confidence = min(importance + semantic - path_penalty, 1.0)
        return max(confidence, 0.1)
    
    def explain_connection(self, fact_id1: str, fact_id2: str) -> Dict[str, Any]:
        """Explain the connection between two specific facts."""
        graph = self.build_graph()
        nodes_map = {n['id']: n for n in graph['nodes']}
        
        if fact_id1 not in nodes_map or fact_id2 not in nodes_map:
            return {'error': 'One or both facts not found'}
        
        node1 = nodes_map[fact_id1]
        node2 = nodes_map[fact_id2]
        
        # Find path
        path = self.find_shortest_path(graph, fact_id1, fact_id2)
        
        # Calculate semantic similarity
        tokens1 = self._tokens(node1['label'])
        tokens2 = self._tokens(node2['label'])
        overlap = tokens1 & tokens2
        
        explanation = {
            'from': node1['label'],
            'to': node2['label'],
            'direct_connection': any(e for e in graph['edges'] if 
                                    (e['from'] == fact_id1 and e['to'] == fact_id2) or
                                    (e['from'] == fact_id2 and e['to'] == fact_id1)),
            'path_length': len(path) if path else None,
            'path_nodes': [nodes_map[nid]['label'] for nid in path] if path else None,
            'shared_concepts': list(overlap),
            'semantic_similarity': len(overlap) / len(tokens1 | tokens2) if (tokens1 | tokens2) else 0,
        }
        
        return explanation
