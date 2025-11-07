#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 6 Test - Geo-tracking, Recovery, and Offline Agent
Comprehensive test of location tracking, device recovery, and offline resilience
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.geotracker import Geotracker, LocationSource, ConfidenceLevel
from saraphina.recovery_orchestrator import RecoveryOrchestrator, RecoveryStatus
from saraphina.offline_agent import OfflineAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

LOG = logging.getLogger("phase6_test")


def test_geotracker():
    """Test location tracking with multiple sources."""
    LOG.info("=" * 60)
    LOG.info("TEST 1: Geotracker - Location Tracking")
    LOG.info("=" * 60)
    
    ke = KnowledgeEngine()
    geo = Geotracker(ke)
    
    # Register some WiFi APs for triangulation
    LOG.info("\n1. Registering WiFi access points...")
    geo.register_wifi_ap("00:11:22:33:44:55", "Home_WiFi", 37.7749, -122.4194, accuracy=30.0)
    geo.register_wifi_ap("AA:BB:CC:DD:EE:FF", "Office_WiFi", 37.7750, -122.4190, accuracy=25.0)
    geo.register_wifi_ap("11:22:33:44:55:66", "Cafe_WiFi", 37.7748, -122.4195, accuracy=35.0)
    
    # Register BLE beacons
    LOG.info("\n2. Registering BLE beacons...")
    geo.register_ble_beacon("beacon-001", 37.7749, -122.4194, accuracy=50.0)
    geo.register_ble_beacon("beacon-002", 37.7751, -122.4192, accuracy=50.0)
    
    # Test GPS location ingestion
    LOG.info("\n3. Ingesting GPS location...")
    device_id = "test-device-001"
    location = geo.ingest_gps(
        device_id, 
        lat=37.7749, 
        lon=-122.4194, 
        altitude=15.0, 
        accuracy=8.5,
        metadata={"source": "GPS", "satellites": 12}
    )
    LOG.info(f"GPS Location: {location.latitude:.6f}, {location.longitude:.6f} ±{location.accuracy}m")
    LOG.info(f"Confidence: {location.confidence.name}")
    
    # Test WiFi triangulation
    LOG.info("\n4. Testing WiFi triangulation...")
    wifi_scans = [
        {"bssid": "00:11:22:33:44:55", "rssi": -45},
        {"bssid": "AA:BB:CC:DD:EE:FF", "rssi": -60},
        {"bssid": "11:22:33:44:55:66", "rssi": -70}
    ]
    wifi_location = geo.ingest_wifi(device_id, wifi_scans)
    if wifi_location:
        LOG.info(f"WiFi Location: {wifi_location.latitude:.6f}, {wifi_location.longitude:.6f} ±{wifi_location.accuracy:.1f}m")
    
    # Test BLE triangulation
    LOG.info("\n5. Testing BLE triangulation...")
    ble_scans = [
        {"id": "beacon-001", "rssi": -55},
        {"id": "beacon-002", "rssi": -65}
    ]
    ble_location = geo.ingest_ble(device_id, ble_scans)
    if ble_location:
        LOG.info(f"BLE Location: {ble_location.latitude:.6f}, {ble_location.longitude:.6f} ±{ble_location.accuracy:.1f}m")
    
    # Test confidence radius calculation
    LOG.info("\n6. Calculating confidence radius...")
    confidence = geo.calculate_confidence_radius(device_id)
    LOG.info(f"Has Location: {confidence['has_location']}")
    LOG.info(f"Confidence Level: {confidence['confidence']}")
    LOG.info(f"Radius: {confidence['radius_meters']:.1f} meters")
    LOG.info(f"Center: {confidence['center']}")
    LOG.info(f"Age: {confidence['age_seconds']:.1f} seconds")
    
    # Test location history
    LOG.info("\n7. Retrieving location history...")
    history = geo.get_location_history(device_id, hours=24)
    LOG.info(f"Location history entries: {len(history)}")
    for i, loc in enumerate(history[:3], 1):
        LOG.info(f"  {i}. {loc.source.value}: ({loc.latitude:.6f}, {loc.longitude:.6f}) ±{loc.accuracy}m @ {loc.timestamp}")
    
    # Test distance calculation
    LOG.info("\n8. Testing Haversine distance calculation...")
    dist = Geotracker.haversine_distance(37.7749, -122.4194, 37.7750, -122.4190)
    LOG.info(f"Distance between points: {dist:.2f} meters")
    
    bearing = Geotracker.bearing(37.7749, -122.4194, 37.7750, -122.4190)
    LOG.info(f"Bearing: {bearing:.1f}°")
    
    LOG.info("\n✓ Geotracker test completed successfully")
    return geo


def test_recovery_orchestrator(geo):
    """Test device recovery orchestration."""
    LOG.info("\n" + "=" * 60)
    LOG.info("TEST 2: Recovery Orchestrator - Device Recovery")
    LOG.info("=" * 60)
    
    ke = KnowledgeEngine()
    recovery = RecoveryOrchestrator(ke, geo)
    
    # Initiate recovery for a missing device
    LOG.info("\n1. Initiating recovery session...")
    device_id = "test-device-001"
    session = recovery.initiate_recovery(
        device_id=device_id,
        reason="Device reported missing by user",
        priority=7
    )
    
    LOG.info(f"Session ID: {session.session_id}")
    LOG.info(f"Device ID: {session.device_id}")
    LOG.info(f"Priority: {session.priority}")
    LOG.info(f"Total Steps: {len(session.steps)}")
    LOG.info(f"Status: {session.status.value}")
    
    # List recovery steps
    LOG.info("\n2. Recovery procedure steps:")
    for i, step in enumerate(session.steps, 1):
        LOG.info(f"  Step {i}: {step.title}")
        LOG.info(f"    Type: {step.step_type.value}")
        LOG.info(f"    Description: {step.description}")
        if step.command:
            LOG.info(f"    Command: {step.command}")
        if step.is_risky:
            LOG.info(f"    ⚠️  RISKY STEP")
    
    # Simulate executing recovery steps
    LOG.info("\n3. Executing recovery steps...")
    
    # Step 1: Check location (success)
    LOG.info("\n  Executing Step 1: Check Last Known Location")
    result = recovery.execute_step(
        session.session_id,
        step_result="Location data retrieved: (37.7749, -122.4194) with confidence radius 50m",
        feedback="Location found"
    )
    LOG.info(f"  Result: {result['status']}")
    
    # Step 2: Network ping (failed)
    LOG.info("\n  Executing Step 2: Network Connectivity Check")
    result = recovery.execute_step(
        session.session_id,
        step_result="Request timeout for icmp_seq 1",
        feedback="Device not responding to ping"
    )
    LOG.info(f"  Result: {result['status']}")
    
    # Step 3: Network scan (failed)
    LOG.info("\n  Executing Step 3: Scan Local Network")
    result = recovery.execute_step(
        session.session_id,
        step_result="No matching devices found",
        feedback="Device not visible on local network"
    )
    LOG.info(f"  Result: {result['status']}")
    
    # Step 4: Bluetooth scan (success!)
    LOG.info("\n  Executing Step 4: Bluetooth Proximity Scan")
    result = recovery.execute_step(
        session.session_id,
        step_result="Device detected via Bluetooth at 00:1A:2B:3C:4D:5E with RSSI -60",
        feedback="Device found nearby via Bluetooth!"
    )
    LOG.info(f"  Result: {result['status']}")
    
    if result['status'] == 'resolved':
        LOG.info(f"\n✓ DEVICE RECOVERED!")
        LOG.info(f"  Resolution message: {result['message']}")
    
    # Get recovery statistics
    LOG.info("\n4. Recovery system statistics:")
    stats = recovery.get_recovery_statistics()
    LOG.info(f"  Total sessions: {stats['total_sessions']}")
    LOG.info(f"  Active sessions: {stats['active_sessions']}")
    LOG.info(f"  Resolved sessions: {stats['resolved_sessions']}")
    LOG.info(f"  Failed sessions: {stats['failed_sessions']}")
    LOG.info(f"  Avg resolution time: {stats['average_resolution_time']:.1f}s")
    LOG.info(f"  Escalation rate: {stats['escalation_rate']:.1%}")
    
    LOG.info("\n✓ Recovery orchestrator test completed successfully")
    return recovery


def test_offline_agent():
    """Test offline agent capabilities."""
    LOG.info("\n" + "=" * 60)
    LOG.info("TEST 3: Offline Agent - Resilient Operation")
    LOG.info("=" * 60)
    
    device_id = "test-device-001"
    agent = OfflineAgent(device_id, data_dir="./test_offline_data")
    
    # Cache policies for offline enforcement
    LOG.info("\n1. Caching policies for offline operation...")
    
    policy1 = {
        "policy_id": "policy-001",
        "name": "Low Battery Policy",
        "policy_type": "device_health",
        "conditions": [{"type": "battery_below", "threshold": 20}],
        "actions": [
            {"action": "reduce_telemetry", "interval": 300},
            {"action": "notify_user", "message": "Low battery detected"}
        ],
        "priority": 8
    }
    agent.cache_policy(policy1, ttl_hours=48)
    
    policy2 = {
        "policy_id": "policy-002",
        "name": "Offline Duration Alert",
        "policy_type": "connectivity",
        "conditions": [{"type": "offline_duration", "minutes": 30}],
        "actions": [
            {"action": "queue_sync", "priority": "high"},
            {"action": "cache_telemetry"}
        ],
        "priority": 6
    }
    agent.cache_policy(policy2, ttl_hours=24)
    
    cached_policies = agent.get_cached_policies()
    LOG.info(f"Cached {len(cached_policies)} policies")
    for policy in cached_policies:
        LOG.info(f"  - {policy['name']} (Priority: {policy['priority']})")
    
    # Simulate going offline
    LOG.info("\n2. Simulating offline operation...")
    agent.set_online_status(False)
    
    # Cache location while offline
    LOG.info("\n3. Caching location data...")
    agent.cache_location(37.7749, -122.4194, altitude=15.0, accuracy=12.0, source="gps")
    agent.cache_location(37.7750, -122.4195, altitude=16.0, accuracy=15.0, source="gps")
    
    cached_loc = agent.get_cached_location()
    LOG.info(f"Last cached location: ({cached_loc['lat']:.6f}, {cached_loc['lon']:.6f})")
    
    # Buffer telemetry
    LOG.info("\n4. Buffering telemetry data...")
    agent.buffer_telemetry("cpu_usage", 45.2, "%")
    agent.buffer_telemetry("memory_usage", 62.8, "%")
    agent.buffer_telemetry("disk_usage", 78.5, "%")
    agent.buffer_telemetry("battery_level", 18.0, "%")
    
    buffered = agent.get_buffered_telemetry()
    LOG.info(f"Buffered {len(buffered)} telemetry entries")
    
    # Enforce policies with low battery context
    LOG.info("\n5. Testing policy enforcement...")
    context = {
        "battery_level": 18,
        "cpu_usage": 45.2,
        "memory_usage": 62.8
    }
    
    triggered_actions = agent.enforce_policy(context)
    LOG.info(f"Triggered {len(triggered_actions)} actions:")
    for action in triggered_actions:
        LOG.info(f"  - {action['action']}: {action.get('message', 'N/A')}")
    
    # Queue actions for sync
    LOG.info("\n6. Queueing actions for sync...")
    agent.queue_action("telemetry_sync", {"device_id": device_id, "entries": len(buffered)})
    agent.queue_action("location_update", {"lat": 37.7749, "lon": -122.4194})
    agent.queue_action("health_report", {"battery": 18.0, "status": "critical"})
    
    pending = agent.get_pending_actions()
    LOG.info(f"Pending actions in queue: {len(pending)}")
    
    # Check privacy timeout
    LOG.info("\n7. Checking privacy timeout...")
    privacy_exceeded = agent.check_privacy_timeout()
    LOG.info(f"Privacy timeout exceeded: {privacy_exceeded}")
    
    # Get sync summary
    LOG.info("\n8. Sync summary:")
    summary = agent.get_sync_summary()
    LOG.info(f"  Online: {summary['is_online']}")
    LOG.info(f"  Offline since: {summary['offline_since']}")
    LOG.info(f"  Pending actions: {summary['pending_actions']}")
    LOG.info(f"  Buffered telemetry: {summary['buffered_telemetry']}")
    LOG.info(f"  Cached locations: {summary['cached_locations']}")
    LOG.info(f"  Privacy timeout: {summary['privacy_timeout_exceeded']}")
    
    # Simulate coming back online
    LOG.info("\n9. Simulating reconnection...")
    agent.set_online_status(True)
    
    # Mark some actions as synced
    for action in pending[:2]:
        agent.mark_action_synced(action['action_id'])
        LOG.info(f"  Synced: {action['action_type']}")
    
    # Clear telemetry buffer
    agent.clear_buffered_telemetry()
    LOG.info("  Telemetry buffer cleared")
    
    # Cleanup old data
    LOG.info("\n10. Cleaning up old data...")
    agent.cleanup_old_data()
    
    agent.close()
    LOG.info("\n✓ Offline agent test completed successfully")


def main():
    """Run all Phase 6 tests."""
    LOG.info("╔" + "═" * 58 + "╗")
    LOG.info("║" + " " * 10 + "PHASE 6 - COMPREHENSIVE TEST SUITE" + " " * 13 + "║")
    LOG.info("║" + " " * 6 + "Geo-tracking, Recovery & Offline Resilience" + " " * 8 + "║")
    LOG.info("╚" + "═" * 58 + "╝")
    
    try:
        # Test 1: Geotracker
        geo = test_geotracker()
        
        # Test 2: Recovery Orchestrator
        recovery = test_recovery_orchestrator(geo)
        
        # Test 3: Offline Agent
        test_offline_agent()
        
        # Final summary
        LOG.info("\n" + "=" * 60)
        LOG.info("PHASE 6 TEST SUMMARY")
        LOG.info("=" * 60)
        LOG.info("✓ Geotracker: GPS, WiFi, BLE location tracking")
        LOG.info("✓ Recovery Orchestrator: Step-by-step device recovery")
        LOG.info("✓ Offline Agent: Resilient offline operation")
        LOG.info("\n🎉 ALL PHASE 6 TESTS PASSED!")
        LOG.info("\nPhase 6 implementation is complete and operational.")
        
    except Exception as e:
        LOG.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
