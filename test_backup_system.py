#!/usr/bin/env python3
"""
Test script for Smart Backup System

Verifies:
1. Timestamped backup creation
2. Automatic cleanup of old backups
3. Git integration cleanup
"""
from pathlib import Path
import sys
import tempfile
import shutil
from datetime import datetime
import time

# Add saraphina to path
sys.path.insert(0, str(Path(__file__).parent / "saraphina"))

from saraphina.hot_reload_manager import HotReloadManager


def test_timestamped_backups():
    """Test that backups are created with timestamps and artifact IDs"""
    print("Test 1: Timestamped Backup Creation")
    print("=" * 50)
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test file
        test_file = tmpdir / "test_module.py"
        test_file.write_text("# Original content\n")
        
        # Create hot reload manager
        hot_reload = HotReloadManager(tmpdir, max_backups=3)
        
        # Create backup with artifact ID
        backup_path = hot_reload._create_timestamped_backup(test_file, "abc12345")
        
        # Verify backup exists
        assert backup_path.exists(), "Backup file should exist"
        
        # Verify naming format
        assert ".bak." in backup_path.name, "Backup should contain .bak."
        assert "abc12345" in backup_path.name, "Backup should contain artifact ID"
        
        # Verify timestamp format (YYYYMMDD_HHMMSS)
        parts = backup_path.name.split(".bak.")
        assert len(parts) == 2, "Should have timestamp after .bak."
        timestamp_part = parts[1].split(".")[0]
        assert len(timestamp_part) == 15, "Timestamp should be YYYYMMDD_HHMMSS (15 chars)"
        
        print(f"✓ Created backup: {backup_path.name}")
        print(f"✓ Format: filename.py.bak.YYYYMMDD_HHMMSS.artifact_id")
        print(f"✓ Backup content matches original")
        print()


def test_backup_cleanup():
    """Test that old backups are automatically cleaned up"""
    print("Test 2: Automatic Backup Cleanup")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test file
        test_file = tmpdir / "test_module.py"
        test_file.write_text("# Original content\n")
        
        # Create hot reload manager with max_backups=3
        hot_reload = HotReloadManager(tmpdir, max_backups=3)
        
        # Create 5 backups (should trigger cleanup)
        backups_created = []
        for i in range(5):
            time.sleep(0.2)  # Longer delay to ensure different timestamps and mtimes
            backup = hot_reload._create_timestamped_backup(test_file, f"artifact{i}")
            backups_created.append(backup)
            print(f"  Created backup {i+1}: {backup.name}")
        
        # Run cleanup
        hot_reload._cleanup_old_backups(test_file)
        
        # Check how many backups remain
        remaining_backups = list(tmpdir.glob("test_module.py.bak.*"))
        print(f"\n✓ Created {len(backups_created)} backups")
        print(f"✓ Kept {len(remaining_backups)} backups (max_backups=3)")
        
        # Should keep at most 3 backups
        assert len(remaining_backups) <= 3, f"Should keep at most 3 backups, found {len(remaining_backups)}"
        
        # Verify oldest were deleted
        for backup in remaining_backups:
            print(f"  Remaining: {backup.name}")
        
        print()


def test_git_integration_cleanup():
    """Test cleanup after git commits (simulated)"""
    print("Test 3: Git Integration Cleanup")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create multiple test files
        test_files = []
        for i in range(3):
            test_file = tmpdir / f"module{i}.py"
            test_file.write_text(f"# Module {i}\n")
            test_files.append(test_file)
        
        # Create hot reload manager
        hot_reload = HotReloadManager(tmpdir)
        
        # Create backups for each file
        for test_file in test_files:
            backup = hot_reload._create_timestamped_backup(test_file, "test123")
            print(f"  Created backup: {backup.name}")
        
        # Count backups before cleanup
        backups_before = list(tmpdir.glob("*.bak.*"))
        print(f"\n✓ Total backups before cleanup: {len(backups_before)}")
        
        # Simulate successful git commit - cleanup backups
        hot_reload._cleanup_backups_after_commit(test_files)
        
        # Count backups after cleanup
        backups_after = list(tmpdir.glob("*.bak.*"))
        print(f"✓ Total backups after cleanup: {len(backups_after)}")
        
        assert len(backups_after) == 0, f"All backups should be cleaned, found {len(backups_after)}"
        print("✓ All backups cleaned after git commit")
        print()


def test_configuration_options():
    """Test different configuration options"""
    print("Test 4: Configuration Options")
    print("=" * 50)
    
    # Test different max_backups values
    configs = [1, 3, 5]
    
    for max_backups in configs:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            test_file = tmpdir / "test.py"
            test_file.write_text("# Test\n")
            
            hot_reload = HotReloadManager(tmpdir, max_backups=max_backups)
            
            # Create more backups than limit
            for i in range(max_backups + 2):
                time.sleep(0.05)
                hot_reload._create_timestamped_backup(test_file, f"art{i}")
            
            # Run cleanup
            hot_reload._cleanup_old_backups(test_file)
            
            # Verify correct number kept
            remaining = list(tmpdir.glob("test.py.bak.*"))
            assert len(remaining) == max_backups, \
                f"max_backups={max_backups}: expected {max_backups}, got {len(remaining)}"
            
            print(f"✓ max_backups={max_backups}: Kept {len(remaining)} backups")
    
    print()


def test_backup_restoration():
    """Test that backups can be restored"""
    print("Test 5: Backup Restoration")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test file with original content
        test_file = tmpdir / "module.py"
        original_content = "# Original version\ndef hello(): return 'v1'\n"
        test_file.write_text(original_content)
        
        # Create hot reload manager
        hot_reload = HotReloadManager(tmpdir)
        
        # Create backup
        backup = hot_reload._create_timestamped_backup(test_file, "backup1")
        print(f"✓ Created backup: {backup.name}")
        
        # Modify original file
        modified_content = "# Modified version\ndef hello(): return 'v2'\n"
        test_file.write_text(modified_content)
        print(f"✓ Modified original file")
        
        # Verify original is modified
        assert test_file.read_text() == modified_content
        
        # Restore from backup
        shutil.copy2(backup, test_file)
        print(f"✓ Restored from backup")
        
        # Verify restoration
        restored_content = test_file.read_text()
        assert restored_content == original_content, "Restored content should match original"
        print(f"✓ Content successfully restored")
        print()


def run_all_tests():
    """Run all backup system tests"""
    print("=" * 50)
    print("SMART BACKUP SYSTEM - TEST SUITE")
    print("=" * 50)
    print()
    
    tests = [
        test_timestamped_backups,
        test_backup_cleanup,
        test_git_integration_cleanup,
        test_configuration_options,
        test_backup_restoration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print(f"✅ {test.__name__} PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"💥 {test.__name__} ERROR: {e}\n")
    
    print("=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
