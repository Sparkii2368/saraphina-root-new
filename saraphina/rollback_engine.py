#!/usr/bin/env python3
"""
RollbackEngine - Track stable versions and automatic rollback on errors.

Maintains version history, detects failures, and can revert to last
stable version automatically.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class RollbackEngine:
    """Manage version tracking and rollback for live code changes."""
    
    def __init__(self, versions_dir: Path):
        """
        Initialize rollback engine.
        
        Args:
            versions_dir: Directory to store version snapshots
        """
        self.versions_dir = versions_dir
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_log_file = self.versions_dir / 'version_log.json'
        self.version_log = self._load_version_log()
        
        self.current_stable = {}  # module -> version_id
        self.rollback_points = []  # List of stable checkpoints
    
    def _load_version_log(self) -> List[Dict[str, Any]]:
        """Load version log from disk."""
        if self.version_log_file.exists():
            try:
                return json.loads(self.version_log_file.read_text())
            except Exception:
                return []
        return []
    
    def _save_version_log(self):
        """Save version log to disk."""
        try:
            self.version_log_file.write_text(
                json.dumps(self.version_log, indent=2)
            )
        except Exception as e:
            logger.error(f"Failed to save version log: {e}")
    
    def create_checkpoint(
        self,
        module_name: str,
        file_path: Path,
        reason: str = "manual_checkpoint"
    ) -> str:
        """
        Create a version checkpoint before making changes.
        
        Args:
            module_name: Module being modified
            file_path: Path to module file
            reason: Why this checkpoint is being created
        
        Returns:
            version_id for this checkpoint
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_id = f"{module_name}_{timestamp}"
        
        # Create version directory
        version_dir = self.versions_dir / version_id
        version_dir.mkdir(exist_ok=True)
        
        # Copy current file
        backup_file = version_dir / file_path.name
        shutil.copy2(file_path, backup_file)
        
        # Calculate hash
        content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
        
        # Record in log
        checkpoint = {
            'version_id': version_id,
            'module': module_name,
            'file_path': str(file_path),
            'backup_path': str(backup_file),
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'hash': content_hash,
            'marked_stable': False
        }
        
        self.version_log.append(checkpoint)
        self._save_version_log()
        
        logger.info(f"Created checkpoint {version_id} for {module_name}")
        
        return version_id
    
    def mark_stable(self, version_id: str) -> bool:
        """
        Mark a version as stable (tests passed, no errors).
        
        Args:
            version_id: Version to mark as stable
        
        Returns:
            True if marked successfully
        """
        for checkpoint in self.version_log:
            if checkpoint['version_id'] == version_id:
                checkpoint['marked_stable'] = True
                checkpoint['marked_stable_at'] = datetime.now().isoformat()
                
                # Update current stable version for this module
                module_name = checkpoint['module']
                self.current_stable[module_name] = version_id
                
                # Add to rollback points
                self.rollback_points.append({
                    'version_id': version_id,
                    'module': module_name,
                    'timestamp': checkpoint['marked_stable_at']
                })
                
                self._save_version_log()
                logger.info(f"Marked {version_id} as stable")
                return True
        
        return False
    
    def get_last_stable_version(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Get last known stable version for a module.
        
        Args:
            module_name: Module to check
        
        Returns:
            Checkpoint dict for last stable version, or None
        """
        # Check cache first
        if module_name in self.current_stable:
            version_id = self.current_stable[module_name]
            for checkpoint in self.version_log:
                if checkpoint['version_id'] == version_id:
                    return checkpoint
        
        # Search log for last stable
        for checkpoint in reversed(self.version_log):
            if checkpoint['module'] == module_name and checkpoint.get('marked_stable'):
                return checkpoint
        
        return None
    
    def rollback_to_version(
        self,
        version_id: str
    ) -> Dict[str, Any]:
        """
        Rollback to a specific version.
        
        Args:
            version_id: Version to restore
        
        Returns:
            Dict with success status and details
        """
        # Find checkpoint
        checkpoint = None
        for cp in self.version_log:
            if cp['version_id'] == version_id:
                checkpoint = cp
                break
        
        if not checkpoint:
            return {
                'success': False,
                'error': f'Version {version_id} not found'
            }
        
        backup_path = Path(checkpoint['backup_path'])
        if not backup_path.exists():
            return {
                'success': False,
                'error': f'Backup file not found: {backup_path}'
            }
        
        target_path = Path(checkpoint['file_path'])
        
        try:
            # Create backup of current version before rollback
            current_backup_id = self.create_checkpoint(
                checkpoint['module'],
                target_path,
                reason=f"pre_rollback_to_{version_id}"
            )
            
            # Restore old version
            shutil.copy2(backup_path, target_path)
            
            # Verify hash
            restored_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()[:16]
            expected_hash = checkpoint['hash']
            
            if restored_hash != expected_hash:
                logger.warning(f"Hash mismatch after rollback: {restored_hash} != {expected_hash}")
            
            logger.info(f"Rolled back {checkpoint['module']} to {version_id}")
            
            return {
                'success': True,
                'version_id': version_id,
                'module': checkpoint['module'],
                'file_path': str(target_path),
                'rollback_at': datetime.now().isoformat(),
                'pre_rollback_backup': current_backup_id
            }
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def auto_rollback_on_error(
        self,
        module_name: str,
        error: Exception
    ) -> Dict[str, Any]:
        """
        Automatically rollback to last stable version on error.
        
        Args:
            module_name: Module that failed
            error: Exception that occurred
        
        Returns:
            Dict with rollback result
        """
        logger.error(f"Auto-rollback triggered for {module_name}: {error}")
        
        last_stable = self.get_last_stable_version(module_name)
        
        if not last_stable:
            return {
                'success': False,
                'error': 'No stable version found for rollback',
                'module': module_name
            }
        
        rollback_result = self.rollback_to_version(last_stable['version_id'])
        
        if rollback_result['success']:
            rollback_result['auto_rollback'] = True
            rollback_result['trigger_error'] = str(error)
        
        return rollback_result
    
    def get_version_history(
        self,
        module_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get version history.
        
        Args:
            module_name: Filter by module (None for all)
            limit: Max versions to return
        
        Returns:
            List of checkpoints
        """
        if module_name:
            filtered = [cp for cp in self.version_log if cp['module'] == module_name]
        else:
            filtered = self.version_log
        
        return list(reversed(filtered[-limit:]))
    
    def cleanup_old_versions(
        self,
        keep_stable: bool = True,
        keep_recent_days: int = 7
    ) -> Dict[str, Any]:
        """
        Clean up old version backups to save space.
        
        Args:
            keep_stable: Always keep versions marked stable
            keep_recent_days: Keep versions from last N days
        
        Returns:
            Dict with cleanup results
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=keep_recent_days)
        
        removed = []
        kept = []
        
        for checkpoint in self.version_log:
            version_date = datetime.fromisoformat(checkpoint['timestamp'])
            is_recent = version_date > cutoff_date
            is_stable = checkpoint.get('marked_stable', False)
            
            # Keep if stable or recent
            if (keep_stable and is_stable) or is_recent:
                kept.append(checkpoint['version_id'])
                continue
            
            # Remove old, non-stable versions
            backup_path = Path(checkpoint['backup_path'])
            if backup_path.exists():
                try:
                    backup_path.unlink()
                    # Try to remove version directory if empty
                    if backup_path.parent.exists():
                        try:
                            backup_path.parent.rmdir()
                        except OSError:
                            pass  # Directory not empty
                    removed.append(checkpoint['version_id'])
                except Exception as e:
                    logger.warning(f"Failed to remove {backup_path}: {e}")
        
        return {
            'removed_count': len(removed),
            'kept_count': len(kept),
            'removed_versions': removed
        }
    
    def get_rollback_points(self) -> List[Dict[str, Any]]:
        """Get list of stable rollback points."""
        return list(reversed(self.rollback_points[-20:]))
