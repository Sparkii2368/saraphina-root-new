#!/usr/bin/env python3
"""
Temp Directory Manager - Manages Saraphina's temp files on D: drive
"""
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger("TempManager")


class TempManager:
    """Manage temporary files to prevent disk bloat"""
    
    def __init__(self, temp_root: str = "D:/Saraphina Root/temp"):
        self.temp_root = Path(temp_root)
        self.temp_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.audio_cache = self.temp_root / "audio"
        self.code_cache = self.temp_root / "code_gen"
        self.downloads = self.temp_root / "downloads"
        
        for d in [self.audio_cache, self.code_cache, self.downloads]:
            d.mkdir(exist_ok=True)
    
    def clean_old_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean temporary files older than max_age_hours
        
        Returns:
            Dict with files_deleted, space_freed
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        files_deleted = 0
        space_freed = 0
        
        for file in self.temp_root.rglob("*"):
            if not file.is_file():
                continue
            
            try:
                # Check file age
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                
                if mtime < cutoff:
                    file_size = file.stat().st_size
                    file.unlink()
                    files_deleted += 1
                    space_freed += file_size
                    logger.debug(f"Deleted old temp file: {file.name}")
            
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")
        
        space_freed_mb = space_freed / (1024 * 1024)
        logger.info(f"Cleaned {files_deleted} files, freed {space_freed_mb:.2f} MB")
        
        return {
            'files_deleted': files_deleted,
            'space_freed_mb': space_freed_mb
        }
    
    def get_temp_stats(self) -> Dict[str, Any]:
        """Get statistics about temp directory usage"""
        total_files = 0
        total_size = 0
        oldest_file = None
        oldest_mtime = None
        
        for file in self.temp_root.rglob("*"):
            if not file.is_file():
                continue
            
            total_files += 1
            total_size += file.stat().st_size
            
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if oldest_mtime is None or mtime < oldest_mtime:
                oldest_mtime = mtime
                oldest_file = file.name
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_file': oldest_file,
            'oldest_age_hours': (datetime.now() - oldest_mtime).total_seconds() / 3600 if oldest_mtime else 0
        }
    
    def emergency_cleanup(self) -> Dict[str, Any]:
        """
        Emergency cleanup when disk space is critical
        Deletes ALL temp files regardless of age
        """
        files_deleted = 0
        space_freed = 0
        
        logger.warning("EMERGENCY CLEANUP: Deleting ALL temp files")
        
        for file in self.temp_root.rglob("*"):
            if not file.is_file():
                continue
            
            try:
                file_size = file.stat().st_size
                file.unlink()
                files_deleted += 1
                space_freed += file_size
            except Exception as e:
                logger.error(f"Failed to delete {file}: {e}")
        
        space_freed_mb = space_freed / (1024 * 1024)
        logger.info(f"Emergency cleanup: {files_deleted} files, {space_freed_mb:.2f} MB freed")
        
        return {
            'files_deleted': files_deleted,
            'space_freed_mb': space_freed_mb
        }
    
    def get_audio_cache_path(self, filename: str) -> Path:
        """Get path for audio cache file"""
        return self.audio_cache / filename
    
    def get_code_cache_path(self, filename: str) -> Path:
        """Get path for code generation cache file"""
        return self.code_cache / filename


# Automatic cleanup on import (clean files older than 24h)
if __name__ != "__main__":
    try:
        manager = TempManager()
        result = manager.clean_old_files(max_age_hours=24)
        if result['files_deleted'] > 0:
            logger.info(f"Auto-cleanup: {result['files_deleted']} old temp files removed")
    except Exception as e:
        logger.warning(f"Auto-cleanup failed: {e}")


if __name__ == "__main__":
    # CLI usage
    import sys
    
    manager = TempManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clean":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            result = manager.clean_old_files(max_age_hours=hours)
            print(f"Cleaned {result['files_deleted']} files, freed {result['space_freed_mb']:.2f} MB")
        
        elif command == "stats":
            stats = manager.get_temp_stats()
            print(f"Total files: {stats['total_files']}")
            print(f"Total size: {stats['total_size_mb']:.2f} MB")
            print(f"Oldest file: {stats['oldest_file']} ({stats['oldest_age_hours']:.1f} hours old)")
        
        elif command == "emergency":
            result = manager.emergency_cleanup()
            print(f"EMERGENCY CLEANUP: {result['files_deleted']} files deleted, {result['space_freed_mb']:.2f} MB freed")
        
        else:
            print("Usage:")
            print("  python temp_manager.py clean [hours]  - Clean files older than [hours] (default 24)")
            print("  python temp_manager.py stats          - Show temp directory statistics")
            print("  python temp_manager.py emergency      - DELETE ALL temp files")
    else:
        stats = manager.get_temp_stats()
        print(f"Saraphina Temp Directory: {manager.temp_root}")
        print(f"Total files: {stats['total_files']}")
        print(f"Total size: {stats['total_size_mb']:.2f} MB")
        print(f"Oldest file: {stats['oldest_file']} ({stats['oldest_age_hours']:.1f} hours old)")
        print("\nRun with 'clean', 'stats', or 'emergency'")
