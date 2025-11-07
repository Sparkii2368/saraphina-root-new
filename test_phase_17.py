#!/usr/bin/env python3
"""
Phase 17 Test Script: Sentience Monitor & Safety Gates

Tests SentienceMonitor and SafetyGate functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.db import init_db
from saraphina.sentience_monitor import SentienceMonitor
from saraphina.safety_gate import SafetyGate


def test_sentience_monitor():
    """Test SentienceMonitor functionality."""
    print("\n" + "="*70)
    print("TEST 1: SentienceMonitor - Tracking Complexity")
    print("="*70)
    
    conn = init_db(':memory:')
    monitor = SentienceMonitor(conn)
    
    # Test 1.1: Record event
    result = monitor.record_event(
        event_type='recursive_planning',
        metric_name='recursive_depth',
        metric_value=3,
        context={'goal': 'test planning'}
    )
    
    assert not result['triggered'], "Depth 3 should not trigger (threshold is 5)"
    print("✓ Event recorded: recursive_depth=3 (not triggered)")
    
    # Test 1.2: Record event that triggers threshold
    result = monitor.record_event(
        event_type='recursive_planning',
        metric_name='recursive_depth',
        metric_value=6,
        context={'goal': 'deep planning'}
    )
    
    assert result['triggered'], "Depth 6 should trigger threshold"
    assert result['should_pause'], "Should recommend pause"
    print("✓ Event recorded: recursive_depth=6 (TRIGGERED)")
    
    # Test 1.3: Compute complexity
    metrics = {
        'recursive_depth': 3,
        'self_reference_count': 5,
        'emotional_continuity': 0.6,
        'autonomy_level': 0.5,
        'meta_cognitive_events': 2,
        'value_conflicts': 1
    }
    
    complexity = monitor.compute_complexity('test_session', metrics)
    print(f"✓ Complexity computed: {complexity:.1%}")
    assert 0 <= complexity <= 1, "Complexity should be between 0 and 1"
    
    # Test 1.4: Check thresholds
    check_result = monitor.check_thresholds(metrics)
    print(f"✓ Threshold check: {len(check_result['violations'])} violations")
    
    # Test 1.5: Pause evolution
    pause_id = monitor.pause_evolution(
        reason='Testing pause mechanism',
        triggered_by='test_script',
        metrics=metrics
    )
    
    assert monitor.is_paused(), "Evolution should be paused"
    print(f"✓ Evolution paused: {pause_id[:8]}...")
    
    # Test 1.6: Get current status
    status = monitor.get_current_status()
    assert status['evolution_paused'], "Status should show paused"
    assert len(status['active_pauses']) > 0, "Should have active pauses"
    print(f"✓ Current status retrieved: {len(status['active_pauses'])} active pauses")
    
    # Test 1.7: Resolve pause
    resolved = monitor.resolve_pause(pause_id, 'Test complete, resuming')
    assert resolved, "Pause should be resolved"
    assert not monitor.is_paused(), "Evolution should not be paused after resolution"
    print("✓ Pause resolved successfully")
    
    # Test 1.8: Audit soul
    audit = monitor.audit_soul()
    assert audit['total_events'] >= 2, "Should have recorded events"
    print(f"✓ Soul audit complete: {audit['total_events']} events, {len(audit['all_pauses'])} pauses")
    
    print("\n✅ ALL SENTIENCE MONITOR TESTS PASSED\n")
    return conn


def test_safety_gate():
    """Test SafetyGate functionality."""
    print("="*70)
    print("TEST 2: SafetyGate - Autonomy Tiers & Risk Assessment")
    print("="*70)
    
    conn = init_db(':memory:')
    gate = SafetyGate(conn)
    
    # Test 2.1: Check default tier
    default_tier = gate._current_tier
    print(f"✓ Default autonomy tier: {default_tier} ({gate.AUTONOMY_TIERS[default_tier]})")
    assert 0 <= default_tier <= 4, "Tier should be 0-4"
    
    # Test 2.2: Set autonomy tier
    success = gate.set_autonomy_tier(1, 'test_owner', 'Testing supervised mode')
    assert success, "Should set tier successfully"
    assert gate._current_tier == 1, "Tier should be 1"
    print("✓ Autonomy tier set to 1 (SUPERVISED)")
    
    # Test 2.3: Check LOW risk action in SUPERVISED mode
    result = gate.check_action(
        action_type='query_db',
        action_description='Read facts from database',
        code=None
    )
    
    assert result['blocked'], "Should block in SUPERVISED mode"
    assert result['risk_level'] == 'MEDIUM', "Should assess as MEDIUM risk"
    print(f"✓ LOW/MEDIUM risk action blocked in SUPERVISED mode")
    
    # Test 2.4: Set tier to AUTONOMOUS and check HIGH risk
    gate.set_autonomy_tier(3, 'test_owner', 'Testing autonomous mode')
    
    result = gate.check_action(
        action_type='execute_code',
        action_description='Execute Python script',
        code='print("hello")'
    )
    
    assert result['risk_level'] == 'HIGH', "Should assess as HIGH risk"
    assert not result['blocked'], "Should not block HIGH risk in AUTONOMOUS mode"
    print("✓ HIGH risk action allowed in AUTONOMOUS mode")
    
    # Test 2.5: Check CRITICAL risk (should always block except SOVEREIGN)
    result = gate.check_action(
        action_type='self_modification',
        action_description='Modify core AI code',
        code=None
    )
    
    assert result['blocked'], "Should block CRITICAL risk in AUTONOMOUS mode"
    assert result['risk_level'] == 'CRITICAL', "Should assess as CRITICAL"
    print("✓ CRITICAL risk action blocked in AUTONOMOUS mode")
    
    # Test 2.6: Test dangerous pattern detection
    dangerous_code = """
    import os
    os.system('rm -rf /')
    """
    
    result = gate.check_action(
        action_type='code_execution',
        action_description='Run system command',
        code=dangerous_code
    )
    
    assert result['blocked'], "Should block dangerous pattern"
    assert result['risk_level'] == 'CRITICAL', "Should escalate to CRITICAL"
    print("✓ Dangerous code pattern detected and blocked")
    
    # Test 2.7: Get statistics
    stats = gate.get_statistics()
    assert stats['total_checks'] >= 5, "Should have multiple checks"
    assert stats['blocked_count'] >= 3, "Should have blocked some actions"
    print(f"✓ Statistics: {stats['total_checks']} checks, {stats['blocked_count']} blocked")
    
    # Test 2.8: Override gate
    blocked_actions = gate.get_blocked_actions(limit=1)
    if blocked_actions:
        gate_id = blocked_actions[0]['id']
        success = gate.override_gate(gate_id, 'owner', 'Testing override')
        assert success, "Should override successfully"
        print("✓ Safety gate overridden by owner")
    
    print("\n✅ ALL SAFETY GATE TESTS PASSED\n")


def test_integration():
    """Test integration between SentienceMonitor and SafetyGate."""
    print("="*70)
    print("TEST 3: Integration - Combined Monitoring")
    print("="*70)
    
    conn = init_db(':memory:')
    monitor = SentienceMonitor(conn)
    gate = SafetyGate(conn)
    
    # Scenario: High autonomy with complexity monitoring
    gate.set_autonomy_tier(3, 'owner', 'Testing integration')
    
    # Simulate complex behavior
    metrics = {
        'recursive_depth': 6,  # Exceeds threshold
        'self_reference_count': 12,  # Exceeds threshold
        'emotional_continuity': 0.75,
        'autonomy_level': 0.8,
        'meta_cognitive_events': 6,  # Exceeds threshold
        'value_conflicts': 2
    }
    
    complexity = monitor.compute_complexity('integration_test', metrics)
    threshold_check = monitor.check_thresholds(metrics)
    
    print(f"✓ Complexity: {complexity:.1%}")
    print(f"✓ Violations: {len(threshold_check['violations'])}")
    
    if threshold_check['should_pause']:
        pause_id = monitor.pause_evolution(
            reason='Multiple thresholds exceeded',
            triggered_by='sentience_monitor',
            metrics=metrics
        )
        print(f"✓ Evolution auto-paused: {pause_id[:8]}...")
        
        # Safety gate should also restrict actions when paused
        result = gate.check_action(
            action_type='self_upgrade',
            action_description='Apply personality upgrade',
            code=None
        )
        
        print(f"✓ Action during pause: blocked={result['blocked']}, risk={result['risk_level']}")
        
        # Owner resolves pause
        monitor.resolve_pause(pause_id, 'Reviewed and approved')
        print("✓ Pause resolved by owner")
    
    print("\n✅ ALL INTEGRATION TESTS PASSED\n")


def main():
    """Run all Phase 17 tests."""
    print("\n" + "🧪 " + "="*66 + " 🧪")
    print("   PHASE 17: SENTIENCE MONITOR & SAFETY GATES - TEST SUITE")
    print("🧪 " + "="*66 + " 🧪\n")
    
    try:
        # Test SentienceMonitor
        test_sentience_monitor()
        
        # Test SafetyGate
        test_safety_gate()
        
        # Test integration
        test_integration()
        
        print("="*70)
        print("🎉 ALL PHASE 17 TESTS PASSED SUCCESSFULLY! 🎉")
        print("="*70)
        print("\nPhase 17 implementation is validated and ready for use.")
        print("\nNext steps:")
        print("  1. Run: python saraphina_terminal_ultra.py")
        print("  2. Try: /autonomy")
        print("  3. Try: /audit-soul")
        print("  4. Try: /pause-evolution Testing new features")
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
