#!/usr/bin/env python3
"""
Test script for Saraphina's autonomous self-upgrade system
"""
import os
import sys
from pathlib import Path

# Add saraphina to path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.self_upgrade_orchestrator import SelfUpgradeOrchestrator


def test_roadmap_parsing():
    """Test roadmap parsing"""
    print("\n" + "="*60)
    print("TEST 1: Roadmap Parsing")
    print("="*60)
    
    orchestrator = SelfUpgradeOrchestrator()
    desktop_path = Path.home() / "Desktop" / "roadmap.txt"
    
    if not desktop_path.exists():
        print(f"❌ roadmap.txt not found at {desktop_path}")
        print("   Please create roadmap.txt on your desktop first")
        return False
    
    print(f"✓ Found roadmap at {desktop_path}")
    
    roadmap = orchestrator.roadmap_parser.parse_file(str(desktop_path))
    
    print(f"\n📋 Parsed Roadmap:")
    print(f"   Phases: {len(roadmap.phases)}")
    print(f"   Immediate Fixes: {len(roadmap.immediate_fixes)}")
    print(f"   Core Schemas: {len(roadmap.core_schemas)}")
    
    if roadmap.phases:
        print(f"\n   Phase List:")
        for phase in roadmap.phases[:5]:  # First 5
            print(f"   - Phase {phase.id}: {phase.name}")
            print(f"     Goal: {phase.goal[:60]}...")
            print(f"     Deliverables: {len(phase.deliverables)}")
    
    return True


def test_capability_audit():
    """Test capability scanning and gap detection"""
    print("\n" + "="*60)
    print("TEST 2: Capability Audit")
    print("="*60)
    
    orchestrator = SelfUpgradeOrchestrator()
    
    print("🔍 Running full audit...")
    report = orchestrator.run_full_audit()
    
    if not report.get('success'):
        print(f"❌ Audit failed: {report.get('error')}")
        return False
    
    print(f"\n📊 Audit Results:")
    print(f"   Current Capabilities: {report['total_capabilities']}")
    print(f"   Total Gaps: {report['total_gaps']}")
    print(f"\n   Severity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"   - {severity.upper()}: {count}")
    
    print(f"\n   Top 5 Gaps:")
    for gap in report['gaps'][:5]:
        print(f"   - {gap['id']}: {gap['requirement'][:60]}...")
        print(f"     Severity: {gap['severity']} | Effort: {gap['effort']}")
    
    return True


def test_code_generation():
    """Test GPT-4 code generation"""
    print("\n" + "="*60)
    print("TEST 3: Code Generation (Dry Run)")
    print("="*60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set - skipping code generation test")
        return False
    
    orchestrator = SelfUpgradeOrchestrator()
    
    # Run audit first
    print("🔍 Running audit to find gaps...")
    report = orchestrator.run_full_audit()
    
    if not report.get('success') or not orchestrator.current_gaps:
        print("❌ No gaps to test with")
        return False
    
    # Get first gap
    gap = orchestrator.current_gaps[0]
    
    print(f"\n🎯 Target Gap: {gap.gap_id}")
    print(f"   Requirement: {gap.requirement}")
    print(f"   Severity: {gap.severity}")
    
    print(f"\n🔨 Generating code with GPT-4...")
    print("   (This may take 10-30 seconds)")
    
    try:
        from saraphina.code_forge import CodeForge
        forge = CodeForge(api_key)
        
        artifact = forge.generate_from_gap(gap)
        
        print(f"\n✅ Code Generated!")
        print(f"   Artifact ID: {artifact.artifact_id}")
        print(f"   Lines of Code: {artifact.estimated_loc}")
        print(f"   Risk Score: {artifact.risk_score:.2f}")
        
        if artifact.new_files:
            print(f"\n   New Files:")
            for filename in artifact.new_files.keys():
                print(f"   - {filename}")
        
        if artifact.code_diffs:
            print(f"\n   Modified Files:")
            for filename in artifact.code_diffs.keys():
                print(f"   - {filename}")
        
        if artifact.tests:
            print(f"\n   Tests Generated:")
            for filename in artifact.tests.keys():
                print(f"   - {filename}")
        
        return True
    
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        return False


def test_status_reporting():
    """Test status and gap reporting"""
    print("\n" + "="*60)
    print("TEST 4: Status Reporting")
    print("="*60)
    
    orchestrator = SelfUpgradeOrchestrator()
    
    # Get status
    status = orchestrator.get_status()
    
    print(f"\n🚦 System Status:")
    print(f"   Roadmap Loaded: {status['roadmap_loaded']}")
    print(f"   Phases Parsed: {status['phases_parsed']}")
    print(f"   Current Gaps: {status['current_gaps']}")
    print(f"   Capabilities: {status['capabilities_count']}")
    print(f"   CodeForge Available: {status['forge_available']}")
    print(f"   Upgrade History: {status['upgrade_history_count']} items")
    
    # Get next gap
    next_gap = orchestrator.get_next_gap()
    
    if next_gap:
        print(f"\n🎯 Next Upgrade Target:")
        print(f"   ID: {next_gap['gap_id']}")
        print(f"   Requirement: {next_gap['requirement'][:80]}...")
        print(f"   Severity: {next_gap['severity']}")
        print(f"   Estimated Effort: {next_gap['estimated_effort']}")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SARAPHINA AUTONOMOUS SELF-UPGRADE SYSTEM TEST")
    print("="*60)
    
    results = {
        "Roadmap Parsing": test_roadmap_parsing(),
        "Capability Audit": test_capability_audit(),
        "Code Generation": test_code_generation(),
        "Status Reporting": test_status_reporting()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n{total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Saraphina's autonomous upgrade system is functional.")
        print("\n📝 Next Steps:")
        print("   1. In the GUI, tell Saraphina: 'Read the roadmap and upgrade yourself'")
        print("   2. She will audit, find gaps, and ask to implement them")
        print("   3. Say 'yes' and watch her autonomously generate and apply code!")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()
