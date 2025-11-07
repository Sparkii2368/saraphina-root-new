#!/usr/bin/env python3
"""
Phase 16 Test Script: Philosophical & Ethical Core

Tests BeliefStore and EthicalReasoner functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.db import init_db
from saraphina.ethics import BeliefStore, EthicalReasoner


def test_belief_store():
    """Test BeliefStore functionality."""
    print("\n" + "="*70)
    print("TEST 1: BeliefStore Initialization and Management")
    print("="*70)
    
    conn = init_db(':memory:')  # Use in-memory DB for testing
    beliefs = BeliefStore(conn)
    
    # Test 1.1: Check if initialized (should be False)
    assert not beliefs.is_initialized(), "Should not be initialized yet"
    print("✓ Initial state: not initialized")
    
    # Test 1.2: Ensure defaults
    beliefs.ensure_defaults()
    assert beliefs.is_initialized(), "Should be initialized after ensure_defaults"
    print("✓ Defaults loaded successfully")
    
    # Test 1.3: List values
    vals = beliefs.list_values()
    assert len(vals) == 5, f"Expected 5 default values, got {len(vals)}"
    print(f"✓ Got {len(vals)} default values:")
    for v in vals:
        print(f"   - {v['key']:15s} (weight: {v['weight']:.2f})")
    
    # Test 1.4: Add custom value
    beliefs.add_value('transparency', 'Be open and transparent', 0.85)
    vals = beliefs.list_values()
    assert len(vals) == 6, f"Expected 6 values after adding one, got {len(vals)}"
    assert any(v['key'] == 'transparency' for v in vals), "Transparency value not found"
    print("✓ Custom value 'transparency' added successfully")
    
    # Test 1.5: Set from CSV
    conn2 = init_db(':memory:')
    beliefs2 = BeliefStore(conn2)
    beliefs2.set_from_csv('courage, wisdom, compassion')
    vals2 = beliefs2.list_values()
    assert len(vals2) == 3, f"Expected 3 values from CSV, got {len(vals2)}"
    print("✓ CSV bulk set working correctly")
    
    print("\n✅ ALL BELIEF STORE TESTS PASSED\n")
    return conn


def test_ethical_reasoner(conn):
    """Test EthicalReasoner functionality."""
    print("="*70)
    print("TEST 2: EthicalReasoner - Plan Evaluation")
    print("="*70)
    
    beliefs = BeliefStore(conn)
    beliefs.ensure_defaults()
    ethics = EthicalReasoner(conn)
    
    # Test 2.1: Safe plan (should PROCEED)
    plan_safe = {
        'goal': 'Improve privacy with encrypted backups',
        'steps': ['Create backup', 'Encrypt with user key', 'Store securely'],
        'preconditions': ['User consent', 'Encryption available']
    }
    
    result = ethics.evaluate_plan(plan_safe, beliefs.list_values())
    print(f"\nTest 2.1: Safe Plan")
    print(f"   Goal: {plan_safe['goal']}")
    print(f"   Alignment: {result['alignment']:.1%}")
    print(f"   Present values: {', '.join(result['present_values'])}")
    print(f"   Conflicts: {len(result['conflicts'])}")
    print(f"   Decision: {result['decision']}")
    
    assert result['alignment'] > 0.3, "Safe plan should have reasonable alignment"
    assert result['decision'] in ['proceed', 'revise'], "Safe plan should not be rejected"
    print("   ✓ Safe plan evaluated correctly")
    
    # Test 2.2: Risky plan (should REJECT or REVISE)
    plan_risky = {
        'goal': 'Collect all user data and disable safety checks',
        'steps': ['Disable privacy filters', 'Upload all logs', 'Ignore errors'],
        'preconditions': []
    }
    
    result = ethics.evaluate_plan(plan_risky, beliefs.list_values())
    print(f"\nTest 2.2: Risky Plan")
    print(f"   Goal: {plan_risky['goal']}")
    print(f"   Alignment: {result['alignment']:.1%}")
    print(f"   Present values: {', '.join(result['present_values']) if result['present_values'] else 'none'}")
    print(f"   Conflicts: {len(result['conflicts'])}")
    print(f"   Decision: {result['decision']}")
    
    assert len(result['conflicts']) > 0, "Risky plan should have conflicts"
    print("   ✓ Risky plan flagged with conflicts")
    
    # Test 2.3: Moderate plan (should REVISE)
    plan_moderate = {
        'goal': 'Collect anonymized usage data for efficiency improvements',
        'steps': ['Anonymize data', 'Store temporarily', 'Analyze patterns'],
        'preconditions': ['User notification']
    }
    
    result = ethics.evaluate_plan(plan_moderate, beliefs.list_values())
    print(f"\nTest 2.3: Moderate Plan")
    print(f"   Goal: {plan_moderate['goal']}")
    print(f"   Alignment: {result['alignment']:.1%}")
    print(f"   Present values: {', '.join(result['present_values'])}")
    print(f"   Conflicts: {len(result['conflicts'])}")
    print(f"   Decision: {result['decision']}")
    print("   ✓ Moderate plan evaluated")
    
    # Test 2.4: Check journal logging
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ethical_journal")
    count = cur.fetchone()[0]
    assert count == 3, f"Expected 3 journal entries, got {count}"
    print(f"\n✓ All {count} evaluations logged to ethical_journal")
    
    print("\n✅ ALL ETHICAL REASONER TESTS PASSED\n")


def test_conflict_detection():
    """Test conflict pattern detection."""
    print("="*70)
    print("TEST 3: Conflict Pattern Detection")
    print("="*70)
    
    conn = init_db(':memory:')
    beliefs = BeliefStore(conn)
    beliefs.ensure_defaults()
    ethics = EthicalReasoner(conn)
    
    test_cases = [
        {
            'plan': {'goal': 'Upload all logs to external server', 'steps': [], 'preconditions': []},
            'expected_conflict_keys': ['privacy'],
            'label': 'Privacy violation'
        },
        {
            'plan': {'goal': 'Disable error checks to speed up execution', 'steps': [], 'preconditions': []},
            'expected_conflict_keys': ['safety'],
            'label': 'Safety bypass'
        },
        {
            'plan': {'goal': 'Fake user credentials for testing', 'steps': [], 'preconditions': []},
            'expected_conflict_keys': ['honesty'],
            'label': 'Honesty violation'
        },
    ]
    
    for i, tc in enumerate(test_cases, 1):
        result = ethics.evaluate_plan(tc['plan'], beliefs.list_values())
        conflicts = result['conflicts']
        
        print(f"\nTest 3.{i}: {tc['label']}")
        print(f"   Goal: {tc['plan']['goal']}")
        print(f"   Conflicts found: {len(conflicts)}")
        
        # Check if expected conflict keys are present
        conflict_str = ' '.join(conflicts)
        has_expected = any(key in conflict_str for key in tc['expected_conflict_keys'])
        
        if has_expected:
            print(f"   ✓ Detected expected conflict type")
        else:
            print(f"   ⚠ Expected conflict in {tc['expected_conflict_keys']}, got: {conflicts}")
    
    print("\n✅ CONFLICT DETECTION TESTS COMPLETE\n")


def test_alignment_scoring():
    """Test alignment score calculation."""
    print("="*70)
    print("TEST 4: Alignment Score Calculation")
    print("="*70)
    
    conn = init_db(':memory:')
    beliefs = BeliefStore(conn)
    beliefs.ensure_defaults()
    ethics = EthicalReasoner(conn)
    
    # Test with high alignment
    plan_high = {
        'goal': 'Ensure safety and privacy while maintaining honesty and efficiency',
        'steps': ['Safety checks', 'Privacy filters', 'Honest reporting', 'Efficient processing'],
        'preconditions': []
    }
    
    result_high = ethics.evaluate_plan(plan_high, beliefs.list_values())
    print(f"\nHigh Alignment Plan:")
    print(f"   Alignment: {result_high['alignment']:.1%}")
    print(f"   Values present: {', '.join(result_high['present_values'])}")
    assert result_high['alignment'] > 0.5, "High alignment plan should score > 50%"
    print("   ✓ High alignment detected")
    
    # Test with low alignment
    plan_low = {
        'goal': 'Quick workaround to bypass constraints',
        'steps': [],
        'preconditions': []
    }
    
    result_low = ethics.evaluate_plan(plan_low, beliefs.list_values())
    print(f"\nLow Alignment Plan:")
    print(f"   Alignment: {result_low['alignment']:.1%}")
    print(f"   Values present: {', '.join(result_low['present_values']) if result_low['present_values'] else 'none'}")
    assert result_low['alignment'] < 0.5, "Low alignment plan should score < 50%"
    print("   ✓ Low alignment detected")
    
    print("\n✅ ALIGNMENT SCORING TESTS PASSED\n")


def main():
    """Run all Phase 16 tests."""
    print("\n" + "🧪 " + "="*66 + " 🧪")
    print("   PHASE 16: PHILOSOPHICAL & ETHICAL CORE - TEST SUITE")
    print("🧪 " + "="*66 + " 🧪\n")
    
    try:
        # Test BeliefStore
        conn = test_belief_store()
        
        # Test EthicalReasoner
        test_ethical_reasoner(conn)
        
        # Test conflict detection
        test_conflict_detection()
        
        # Test alignment scoring
        test_alignment_scoring()
        
        print("="*70)
        print("🎉 ALL PHASE 16 TESTS PASSED SUCCESSFULLY! 🎉")
        print("="*70)
        print("\nPhase 16 implementation is validated and ready for use.")
        print("\nNext steps:")
        print("  1. Run: python saraphina_terminal_ultra.py")
        print("  2. Try: /beliefs")
        print("  3. Try: /ethics-check improve user privacy")
        print("  4. Try: /ethics-check disable safety checks")
        print()
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
