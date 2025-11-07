#!/usr/bin/env python3
"""
Quick test script for Phase 13: Knowledge Graph & Intuition Layer
"""
from saraphina.db import init_db
from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.knowledge_graph import KnowledgeGraphExplorer
import json

def test_phase13():
    print("🧪 Testing Phase 13: Knowledge Graph & Intuition Layer\n")
    
    # Initialize
    conn = init_db()
    ke = KnowledgeEngine()
    graph_explorer = KnowledgeGraphExplorer(conn)
    
    # Test 1: Add some test facts
    print("1️⃣ Adding test facts...")
    fact_ids = []
    test_facts = [
        ("programming", "Python basics", "Python is a high-level programming language with dynamic typing", "test", 0.9),
        ("programming", "JavaScript fundamentals", "JavaScript is a scripting language for web development", "test", 0.9),
        ("devops", "Docker containers", "Docker uses container technology for application isolation", "test", 0.8),
        ("devops", "Kubernetes orchestration", "Kubernetes orchestrates containers at scale", "test", 0.8),
        ("cloud", "AWS services", "AWS provides cloud computing services and infrastructure", "test", 0.9),
    ]
    
    for topic, summary, content, source, conf in test_facts:
        fid = ke.store_fact(topic, summary, content, source, conf)
        fact_ids.append(fid)
        print(f"   ✓ Added: {summary} (id: {fid[:12]}...)")
    
    # Test 2: Build graph
    print("\n2️⃣ Building knowledge graph...")
    graph = graph_explorer.build_graph()
    print(f"   Graph stats:")
    print(f"   - Nodes: {graph['stats']['node_count']}")
    print(f"   - Edges: {graph['stats']['edge_count']}")
    print(f"   - Topics: {', '.join(graph['stats']['topics'])}")
    print(f"   - Avg degree: {graph['stats']['avg_degree']:.2f}")
    
    # Test 3: PageRank
    print("\n3️⃣ Calculating PageRank...")
    pr_scores = graph_explorer.pagerank(graph)
    if pr_scores:
        top_nodes = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        print("   Top 3 important nodes:")
        nodes_map = {n['id']: n for n in graph['nodes']}
        for nid, score in top_nodes:
            if nid in nodes_map:
                print(f"   - {nodes_map[nid]['label'][:40]} (score: {score:.4f})")
    
    # Test 4: Discover insights
    print("\n4️⃣ Discovering insights...")
    insights = graph_explorer.discover_insights(limit=3)
    if insights:
        print(f"   Found {len(insights)} insight(s):\n")
        for i, ins in enumerate(insights, 1):
            print(f"   {i}. {ins['explanation']}")
            print(f"      Topics: {ins['from_topic']} ↔ {ins['to_topic']}")
            print(f"      Confidence: {ins['confidence']:.1%}\n")
    else:
        print("   No insights found yet (need more data and connections)")
    
    # Test 5: Explain connection
    if len(fact_ids) >= 2:
        print(f"5️⃣ Explaining connection between first two facts...")
        expl = graph_explorer.explain_connection(fact_ids[0], fact_ids[1])
        if 'error' not in expl:
            print(f"   From: {expl['from'][:50]}")
            print(f"   To: {expl['to'][:50]}")
            print(f"   Shared concepts: {', '.join(expl['shared_concepts']) if expl['shared_concepts'] else 'none'}")
            print(f"   Semantic similarity: {expl['semantic_similarity']:.2%}")
            if expl.get('direct_connection'):
                print("   ✓ Directly connected")
            elif expl.get('path_nodes'):
                print(f"   Path length: {len(expl['path_nodes'])} steps")
    
    print("\n✅ Phase 13 test complete!")
    print("\nTry these natural language queries in the terminal:")
    print('   "What patterns do you see?"')
    print('   "Any insights about programming?"')
    print('   "How do Python and JavaScript relate?"')

if __name__ == "__main__":
    test_phase13()
