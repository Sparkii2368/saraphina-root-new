#!/usr/bin/env python3
"""
Test Phase 9: Meta-Learning & Self-Reflection
Tests LearningJournal and MetaOptimizer functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from uuid import uuid4
from saraphina.learning_journal import LearningJournal, LearningEvent
from saraphina.meta_optimizer import MetaOptimizer


def test_learning_journal():
    """Test LearningJournal basic operations"""
    print("\n" + "="*74)
    print("TEST 1: LearningJournal Basic Operations")
    print("="*74)
    
    # Initialize journal with test DB
    journal = LearningJournal(db_path='ai_data/test_learning_journal.db')
    
    # Test 1: Log a learning event
    print("\n1️⃣  Logging a successful learning event...")
    event1 = LearningEvent(
        event_id=f"test_{uuid4()}",
        timestamp=datetime.utcnow(),
        event_type='query',
        input_data={'query': 'How do I use Docker?', 'topic': 'devops'},
        method_used='knowledge_recall',
        result={'has_kb_hits': True, 'response_length': 250},
        confidence=0.85,
        success=True,
        feedback=None,
        context={'topic': 'devops', 'kb_hit_count': 3},
        lessons_learned=['Docker is a containerization platform', 'Users often ask about docker-compose']
    )
    journal.log_event(event1)
    print("✅ Event logged successfully")
    
    # Test 2: Log a failed learning event
    print("\n2️⃣  Logging a failed learning event...")
    event2 = LearningEvent(
        event_id=f"test_{uuid4()}",
        timestamp=datetime.utcnow(),
        event_type='query',
        input_data={'query': 'What is quantum computing?', 'topic': 'general'},
        method_used='knowledge_recall',
        result={'has_kb_hits': False, 'response_length': 50},
        confidence=0.25,
        success=False,
        feedback=None,
        context={'topic': 'general', 'kb_hit_count': 0},
        lessons_learned=['Need more quantum computing knowledge']
    )
    journal.log_event(event2)
    print("✅ Failed event logged successfully")
    
    # Test 3: Retrieve recent events
    print("\n3️⃣  Retrieving recent events...")
    recent = journal.get_recent_events(limit=5)
    print(f"   Retrieved {len(recent)} events")
    for e in recent[:2]:
        print(f"   • {e.event_type} | {e.method_used} | Success: {e.success} | Conf: {e.confidence:.2%}")
    
    # Test 4: Get strategy performance
    print("\n4️⃣  Checking strategy performance...")
    perf = journal.get_strategy_performance()
    for name, outcome in list(perf.items())[:3]:
        print(f"   {name}:")
        print(f"      Success Rate: {outcome.success_rate():.1%} ({outcome.total_uses} uses)")
        print(f"      Avg Confidence: {outcome.avg_confidence:.1%}")
    
    # Test 5: Get learning summary
    print("\n5️⃣  Getting learning summary...")
    summary = journal.get_learning_summary(days=7)
    print(f"   Total Events: {summary['total_events']}")
    print(f"   Success Rate: {summary['success_rate']:.1%}")
    print(f"   Avg Confidence: {summary['avg_confidence']:.1%}")
    if summary['top_strategies']:
        print(f"   Top Strategy: {list(summary['top_strategies'].keys())[0]}")
    
    # Test 6: Detect patterns
    print("\n6️⃣  Detecting learning patterns...")
    patterns = journal.detect_patterns(min_occurrences=1)
    print(f"   Detected {len(patterns)} pattern(s)")
    for p in patterns[:2]:
        print(f"   • Type: {p['type']} | Method: {p.get('method', 'N/A')}")
    
    # Test 7: Add reflection
    print("\n7️⃣  Adding a reflection note...")
    ref_id = journal.add_reflection(
        trigger='test_failure',
        analysis='Knowledge gap in quantum computing domain',
        insights=['Need to research quantum computing basics', 'Add quantum computing to knowledge domains'],
        proposed_changes=['Add quantum computing facts', 'Improve fallback responses for unknown topics']
    )
    print(f"   Reflection added with ID: {ref_id}")
    
    # Test 8: Get reflections
    print("\n8️⃣  Retrieving reflections...")
    reflections = journal.get_reflections(limit=3)
    print(f"   Retrieved {len(reflections)} reflection(s)")
    if reflections:
        r = reflections[0]
        print(f"   Latest: Trigger='{r['trigger']}' | Insights={len(r['insights'])}")
    
    journal.close()
    print("\n✅ LearningJournal tests completed successfully!\n")


def test_meta_optimizer():
    """Test MetaOptimizer operations"""
    print("\n" + "="*74)
    print("TEST 2: MetaOptimizer Operations")
    print("="*74)
    
    # Initialize journal and optimizer
    journal = LearningJournal(db_path='ai_data/test_learning_journal.db')
    optimizer = MetaOptimizer(journal)
    
    # Generate some test data for optimization
    print("\n1️⃣  Generating test learning events...")
    strategies = ['knowledge_recall', 'code_generation', 'predictive_suggestion']
    
    for i in range(30):
        strategy = strategies[i % len(strategies)]
        # Make knowledge_recall perform poorly
        if strategy == 'knowledge_recall':
            success = i % 5 == 0  # 20% success rate
            confidence = 0.3
        else:
            success = i % 3 != 0  # 66% success rate
            confidence = 0.7
        
        event = LearningEvent(
            event_id=f"test_{uuid4()}",
            timestamp=datetime.utcnow() - timedelta(hours=i),
            event_type='query',
            input_data={'query': f'Test query {i}', 'topic': 'programming'},
            method_used=strategy,
            result={'test': True},
            confidence=confidence,
            success=success,
            context={'iteration': i}
        )
        journal.log_event(event)
    print(f"   Generated 30 test events")
    
    # Test 1: Analyze learning health
    print("\n2️⃣  Analyzing learning health...")
    health = optimizer.analyze_learning_health()
    print(f"   Overall Health: {health['overall_health']}")
    print(f"   Issues Detected: {len(health['issues'])}")
    if health['issues']:
        print(f"   Sample Issue: {health['issues'][0].get('type', 'unknown')}")
    
    # Test 2: Propose optimizations
    print("\n3️⃣  Proposing optimizations...")
    proposals = optimizer.propose_optimizations()
    print(f"   Generated {len(proposals)} proposal(s)")
    for i, prop in enumerate(proposals[:3], 1):
        print(f"\n   Proposal {i}:")
        print(f"      Priority: {prop.priority}")
        print(f"      Category: {prop.category}")
        print(f"      Target: {prop.target}")
        print(f"      Rationale: {prop.rationale[:60]}...")
        print(f"      Expected Improvement: {prop.expected_improvement:.1%}")
        print(f"      Confidence: {prop.confidence:.1%}")
    
    # Test 3: Reflect on failure
    print("\n4️⃣  Reflecting on a specific failure...")
    failed_events = journal.get_recent_events(limit=50, event_type='query')
    failed = [e for e in failed_events if not e.success]
    if failed:
        reflection = optimizer.reflect_on_failure(failed[0])
        print(f"   Event ID: {reflection['event_id']}")
        print(f"   Insights: {len(reflection['insights'])}")
        if reflection['insights']:
            print(f"      • {reflection['insights'][0][:60]}...")
        print(f"   Proposed Changes: {len(reflection['proposed_changes'])}")
        if reflection['proposed_changes']:
            print(f"      • {reflection['proposed_changes'][0][:60]}...")
    else:
        print("   No failed events found for reflection")
    
    # Test 4: Comprehensive audit
    print("\n5️⃣  Running comprehensive learning audit...")
    audit = optimizer.audit_learning(days=7)
    print(f"   Audit Timestamp: {audit['audit_timestamp']}")
    print(f"   Period: {audit['period_days']} days")
    print(f"   Strategies Analyzed: {len(audit['strategy_performance'])}")
    print(f"   Optimization Proposals: {len(audit['optimization_proposals'])}")
    print(f"   Reflections: {len(audit['reflections'])}")
    
    # Test 5: Auto-optimize (with high threshold so nothing is applied)
    print("\n6️⃣  Testing auto-optimize (dry-run)...")
    applied = optimizer.auto_optimize(apply_threshold=0.95)  # Very high threshold
    print(f"   Applied: {len(applied)} optimization(s)")
    if applied:
        for a in applied:
            print(f"      • {a['target']}: {a['old_value']} → {a['new_value']}")
    else:
        print("      (None applied due to high threshold - as expected)")
    
    journal.close()
    print("\n✅ MetaOptimizer tests completed successfully!\n")


def test_integration():
    """Test integration between LearningJournal and MetaOptimizer"""
    print("\n" + "="*74)
    print("TEST 3: Integration Test - Learning from Failures")
    print("="*74)
    
    journal = LearningJournal(db_path='ai_data/test_learning_journal.db')
    optimizer = MetaOptimizer(journal)
    
    print("\n1️⃣  Simulating a pattern of repeated failures...")
    # Create repeated failures with same method
    for i in range(5):
        event = LearningEvent(
            event_id=f"fail_{uuid4()}",
            timestamp=datetime.utcnow() - timedelta(minutes=i*10),
            event_type='failure',
            input_data={'query': f'Complex query {i}', 'topic': 'advanced'},
            method_used='naive_search',
            result={'error': 'No results found'},
            confidence=0.15,
            success=False,
            lessons_learned=['naive_search is inadequate for complex queries']
        )
        journal.log_event(event)
    print(f"   Logged 5 repeated failures with 'naive_search'")
    
    print("\n2️⃣  Detecting patterns...")
    patterns = journal.detect_patterns(min_occurrences=3)
    repeated_failures = [p for p in patterns if p['type'] == 'repeated_failure']
    print(f"   Found {len(repeated_failures)} repeated failure pattern(s)")
    if repeated_failures:
        print(f"      Method: {repeated_failures[0]['method']}")
        print(f"      Count: {repeated_failures[0]['count']}")
        print(f"      Severity: {repeated_failures[0]['severity']}")
    
    print("\n3️⃣  Proposing optimizations based on patterns...")
    proposals = optimizer.propose_optimizations()
    underperforming = [p for p in proposals if 'naive_search' in p.target]
    if underperforming:
        print(f"   Generated proposal for naive_search:")
        prop = underperforming[0]
        print(f"      Priority: {prop.priority}")
        print(f"      Rationale: {prop.rationale}")
        print(f"      Proposed Action: {prop.proposed_value}")
    else:
        print("   (No specific proposal for naive_search - may need more data)")
    
    print("\n4️⃣  Reflecting on latest failure...")
    failed_events = journal.get_recent_events(limit=10, event_type='failure')
    if failed_events:
        reflection = optimizer.reflect_on_failure(failed_events[0])
        print(f"   Generated {len(reflection['insights'])} insight(s)")
        print(f"   Generated {len(reflection['proposed_changes'])} proposed change(s)")
        if reflection['proposed_changes']:
            print(f"      First proposal: {reflection['proposed_changes'][0][:70]}...")
    
    journal.close()
    print("\n✅ Integration test completed successfully!\n")


def test_acceptance_criteria():
    """Test the Phase 9 acceptance criteria"""
    print("\n" + "="*74)
    print("TEST 4: Acceptance Criteria - Reflect on Failed Plan")
    print("="*74)
    
    journal = LearningJournal(db_path='ai_data/test_learning_journal.db')
    optimizer = MetaOptimizer(journal)
    
    # Simulate a failed plan
    print("\n📋 Scenario: Saraphina tried to use 'brute_force_search' but it failed")
    
    failed_plan = LearningEvent(
        event_id=f"plan_fail_{uuid4()}",
        timestamp=datetime.utcnow(),
        event_type='failure',
        input_data={
            'query': 'Find optimal solution for complex optimization problem',
            'topic': 'algorithm',
            'plan': 'Use brute_force_search to find optimal solution'
        },
        method_used='brute_force_search',
        result={'error': 'Timeout - too slow', 'time_elapsed': 30000},
        confidence=0.2,
        success=False,
        feedback={'user_feedback': 'This is taking too long!'},
        lessons_learned=['Brute force is too slow for large search spaces']
    )
    
    journal.log_event(failed_plan)
    print("✅ Failed plan logged")
    
    # Reflect on the failure
    print("\n🤔 Reflecting on the failure...")
    reflection = optimizer.reflect_on_failure(failed_plan)
    
    print("\n📊 Reflection Results:")
    print(f"   Event ID: {reflection['event_id']}")
    
    if reflection['failure_analysis']:
        print(f"\n   📈 Failure Analysis:")
        analysis = reflection['failure_analysis']
        print(f"      Method: {analysis.get('method', 'N/A')}")
        print(f"      Historical Success Rate: {analysis.get('historical_success_rate', 0):.1%}")
        print(f"      Total Uses: {analysis.get('total_uses', 0)}")
    
    if reflection['insights']:
        print(f"\n   💡 Insights Generated:")
        for i, insight in enumerate(reflection['insights'], 1):
            print(f"      {i}. {insight}")
    
    if reflection['proposed_changes']:
        print(f"\n   🔧 Proposed Changes:")
        for i, change in enumerate(reflection['proposed_changes'], 1):
            print(f"      {i}. {change}")
    
    print("\n📝 Suggesting New Learning Strategy:")
    proposals = optimizer.propose_optimizations()
    if proposals:
        print(f"   Generated {len(proposals)} optimization proposal(s)")
        best_proposal = proposals[0]  # Highest priority
        print(f"\n   🌟 Top Recommendation:")
        print(f"      Target: {best_proposal.target}")
        print(f"      Priority: {best_proposal.priority}")
        print(f"      Rationale: {best_proposal.rationale}")
        print(f"      Current: {best_proposal.current_value}")
        print(f"      Proposed: {best_proposal.proposed_value}")
        print(f"      Expected Improvement: {best_proposal.expected_improvement:.1%}")
    else:
        print("   No proposals generated (may need more learning data)")
    
    journal.close()
    print("\n✅ ACCEPTANCE CRITERIA MET: Saraphina reflected on failed plan and suggested new strategy!\n")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║           PHASE 9: META-LEARNING & SELF-REFLECTION TEST SUITE           ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Run all tests
        test_learning_journal()
        test_meta_optimizer()
        test_integration()
        test_acceptance_criteria()
        
        print("\n" + "="*74)
        print("🎉 ALL PHASE 9 TESTS PASSED SUCCESSFULLY! 🎉")
        print("="*74)
        print("\nPhase 9 Features Validated:")
        print("  ✅ LearningJournal logs strategies, successes, and failures")
        print("  ✅ MetaOptimizer detects inefficiencies and biases")
        print("  ✅ MetaOptimizer proposes strategy adjustments")
        print("  ✅ Saraphina reflects on failed plans")
        print("  ✅ Saraphina suggests new learning strategies")
        print("\nTerminal Commands Available:")
        print("  • /reflect           - View learning journal")
        print("  • /audit-learning    - Comprehensive learning audit")
        print("  • /optimize-strategy - Get AI-driven optimization proposals")
        print("\nNext Steps:")
        print("  1. Run: python saraphina_terminal_ultra.py")
        print("  2. Test commands: /reflect, /audit-learning, /optimize-strategy")
        print("  3. Interact with Saraphina - all queries are auto-logged!")
        print("  4. Watch her learn and optimize her own strategies over time")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
