#!/usr/bin/env python3
"""
Recovery Bootstrap: Restore Saraphina from shadow nodes after host failure.
Features: Automatic recovery, integrity verification, state restoration, rollback.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json
import shutil
import sqlite3


@dataclass
class RecoveryPlan:
    """Plan for recovery from shadow node."""
    plan_id: str
    source_node_id: str
    target_path: str
    recovery_type: str  # full, partial, incremental
    estimated_time_seconds: float
    files_to_restore: List[str]
    total_size_bytes: int
    verification_required: bool
    backup_current: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'source_node_id': self.source_node_id,
            'target_path': self.target_path,
            'recovery_type': self.recovery_type,
            'estimated_time_seconds': self.estimated_time_seconds,
            'files_to_restore': self.files_to_restore,
            'total_size_bytes': self.total_size_bytes,
            'verification_required': self.verification_required,
            'backup_current': self.backup_current
        }


@dataclass
class RecoveryResult:
    """Result of recovery operation."""
    recovery_id: str
    timestamp: datetime
    source_node: str
    success: bool
    files_restored: int
    bytes_restored: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    verification_passed: bool = True
    rollback_available: bool = False


class RecoveryValidator:
    """Validate recovery operations."""
    
    @staticmethod
    def validate_source_node(node_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that source node is suitable for recovery."""
        issues = []
        
        # Check node status
        if node_info.get('status') not in ['active', 'healthy']:
            issues.append(f"Node status is {node_info.get('status')}, not active/healthy")
        
        # Check age
        last_sync = node_info.get('last_sync')
        if last_sync:
            try:
                last_sync_dt = datetime.fromisoformat(last_sync)
                age_days = (datetime.utcnow() - last_sync_dt).days
                if age_days > 30:
                    issues.append(f"Node data is {age_days} days old")
            except Exception:
                issues.append("Cannot parse last sync timestamp")
        
        # Check integrity
        checksum = node_info.get('checksum')
        if not checksum:
            issues.append("No checksum available for verification")
        
        # Check trust score
        trust_score = node_info.get('trust_score', 0)
        if trust_score < 0.5:
            issues.append(f"Low trust score: {trust_score}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def validate_target_path(target_path: str) -> Tuple[bool, List[str]]:
        """Validate that target path is suitable for recovery."""
        issues = []
        path = Path(target_path)
        
        # Check parent directory exists
        if not path.parent.exists():
            issues.append("Parent directory does not exist")
        
        # Check write permissions
        try:
            test_file = path.parent / ".recovery_test"
            test_file.touch()
            test_file.unlink()
        except Exception:
            issues.append("No write permission to target directory")
        
        # Check available space (basic check)
        try:
            import shutil
            stats = shutil.disk_usage(path.parent)
            if stats.free < 100 * 1024 * 1024:  # Less than 100MB
                issues.append(f"Low disk space: {stats.free / (1024*1024):.1f}MB available")
        except Exception:
            pass
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def verify_restored_db(db_path: str, expected_checksum: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Verify integrity of restored database."""
        issues = []
        
        # Check file exists
        if not Path(db_path).exists():
            issues.append("Restored database file not found")
            return False, issues
        
        # Try to open database
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            # Check if it's a valid SQLite database
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()
            
            if not tables:
                issues.append("Database has no tables")
            
            # Basic integrity check
            cur.execute("PRAGMA integrity_check")
            result = cur.fetchone()
            if result[0] != 'ok':
                issues.append(f"Database integrity check failed: {result[0]}")
            
            conn.close()
            
        except sqlite3.Error as e:
            issues.append(f"Cannot open database: {e}")
            return False, issues
        
        # Verify checksum if provided
        if expected_checksum:
            import hashlib
            sha256 = hashlib.sha256()
            with open(db_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            actual_checksum = sha256.hexdigest()
            
            if actual_checksum != expected_checksum:
                issues.append("Checksum mismatch - possible corruption")
        
        is_valid = len(issues) == 0
        return is_valid, issues


class RecoveryBootstrap:
    """Main recovery bootstrap orchestrator."""
    
    def __init__(self, shadow_node_manager, security_manager=None):
        self.shadow_mgr = shadow_node_manager
        self.sec = security_manager
        self.validator = RecoveryValidator()
    
    def create_recovery_plan(self, source_node_id: str, target_path: str,
                            recovery_type: str = 'full') -> Optional[RecoveryPlan]:
        """Create a recovery plan."""
        from uuid import uuid4
        
        # Get source node info
        node = self.shadow_mgr.get_node(source_node_id)
        if not node:
            return None
        
        # Validate source
        valid, issues = self.validator.validate_source_node(node.to_dict())
        if not valid:
            print(f"Source node validation failed: {issues}")
            return None
        
        # Validate target
        valid, issues = self.validator.validate_target_path(target_path)
        if not valid:
            print(f"Target path validation failed: {issues}")
            return None
        
        # Create plan
        plan = RecoveryPlan(
            plan_id=f"recovery_{uuid4()}",
            source_node_id=source_node_id,
            target_path=target_path,
            recovery_type=recovery_type,
            estimated_time_seconds=node.size_bytes / (10 * 1024 * 1024),  # Assume 10MB/s
            files_to_restore=[Path(node.location).name],
            total_size_bytes=node.size_bytes,
            verification_required=True,
            backup_current=Path(target_path).exists()
        )
        
        return plan
    
    def execute_recovery(self, plan: RecoveryPlan) -> RecoveryResult:
        """Execute recovery plan."""
        from uuid import uuid4
        import time
        
        start_time = time.time()
        recovery_id = f"recovery_{uuid4()}"
        errors = []
        warnings = []
        files_restored = 0
        bytes_restored = 0
        rollback_path = None
        
        try:
            # Backup current database if exists
            target = Path(plan.target_path)
            if plan.backup_current and target.exists():
                rollback_path = str(target) + f".rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                try:
                    shutil.copy2(str(target), rollback_path)
                    warnings.append(f"Created rollback backup at {rollback_path}")
                except Exception as e:
                    errors.append(f"Could not create rollback backup: {e}")
                    return RecoveryResult(
                        recovery_id=recovery_id,
                        timestamp=datetime.utcnow(),
                        source_node=plan.source_node_id,
                        success=False,
                        files_restored=0,
                        bytes_restored=0,
                        duration_seconds=time.time() - start_time,
                        errors=errors,
                        warnings=warnings,
                        verification_passed=False,
                        rollback_available=False
                    )
            
            # Perform recovery
            success = self.shadow_mgr.recover_from_node(plan.source_node_id, plan.target_path)
            
            if not success:
                errors.append("Recovery operation failed")
                # Rollback if available
                if rollback_path and Path(rollback_path).exists():
                    try:
                        shutil.copy2(rollback_path, plan.target_path)
                        warnings.append("Rolled back to previous state")
                    except Exception:
                        errors.append("Rollback failed")
                
                return RecoveryResult(
                    recovery_id=recovery_id,
                    timestamp=datetime.utcnow(),
                    source_node=plan.source_node_id,
                    success=False,
                    files_restored=0,
                    bytes_restored=0,
                    duration_seconds=time.time() - start_time,
                    errors=errors,
                    warnings=warnings,
                    verification_passed=False,
                    rollback_available=bool(rollback_path)
                )
            
            files_restored = 1
            bytes_restored = Path(plan.target_path).stat().st_size
            
            # Verify recovery if required
            verification_passed = True
            if plan.verification_required:
                node = self.shadow_mgr.get_node(plan.source_node_id)
                expected_checksum = node.checksum if node else None
                
                verification_passed, verify_issues = self.validator.verify_restored_db(
                    plan.target_path, expected_checksum
                )
                
                if not verification_passed:
                    errors.extend(verify_issues)
                    warnings.append("Verification failed - data may be corrupted")
            
            duration = time.time() - start_time
            
            return RecoveryResult(
                recovery_id=recovery_id,
                timestamp=datetime.utcnow(),
                source_node=plan.source_node_id,
                success=True,
                files_restored=files_restored,
                bytes_restored=bytes_restored,
                duration_seconds=duration,
                errors=errors,
                warnings=warnings,
                verification_passed=verification_passed,
                rollback_available=bool(rollback_path)
            )
            
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            
            # Attempt rollback
            if rollback_path and Path(rollback_path).exists():
                try:
                    shutil.copy2(rollback_path, plan.target_path)
                    warnings.append("Rolled back to previous state after error")
                except Exception:
                    errors.append("Rollback failed after error")
            
            return RecoveryResult(
                recovery_id=recovery_id,
                timestamp=datetime.utcnow(),
                source_node=plan.source_node_id,
                success=False,
                files_restored=0,
                bytes_restored=0,
                duration_seconds=time.time() - start_time,
                errors=errors,
                warnings=warnings,
                verification_passed=False,
                rollback_available=bool(rollback_path)
            )
    
    def select_best_recovery_node(self) -> Optional[str]:
        """Automatically select best node for recovery."""
        nodes = self.shadow_mgr.list_nodes(status='active')
        
        if not nodes:
            return None
        
        # Score nodes
        scored_nodes = []
        for node in nodes:
            score = 0.0
            
            # Trust score (40% weight)
            score += node.trust_score * 0.4
            
            # Recency (30% weight)
            age_days = (datetime.utcnow() - node.last_sync).days
            recency_score = max(0, 1.0 - (age_days / 30))
            score += recency_score * 0.3
            
            # Version (20% weight)
            # Higher version is better
            version_score = min(1.0, node.version / 100)
            score += version_score * 0.2
            
            # Integrity (10% weight)
            has_checksum = 1.0 if node.checksum else 0.0
            score += has_checksum * 0.1
            
            scored_nodes.append((node, score))
        
        # Sort by score descending
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        # Return best node
        best_node = scored_nodes[0][0]
        return best_node.node_id
    
    def quick_recovery(self, target_path: str, auto_select: bool = True) -> RecoveryResult:
        """Quick recovery with automatic node selection."""
        # Select best node
        if auto_select:
            node_id = self.select_best_recovery_node()
            if not node_id:
                return RecoveryResult(
                    recovery_id="quick_recovery_failed",
                    timestamp=datetime.utcnow(),
                    source_node="none",
                    success=False,
                    files_restored=0,
                    bytes_restored=0,
                    duration_seconds=0,
                    errors=["No suitable recovery node found"],
                    verification_passed=False,
                    rollback_available=False
                )
        else:
            # Use first active node
            nodes = self.shadow_mgr.list_nodes(status='active')
            if not nodes:
                return RecoveryResult(
                    recovery_id="quick_recovery_failed",
                    timestamp=datetime.utcnow(),
                    source_node="none",
                    success=False,
                    files_restored=0,
                    bytes_restored=0,
                    duration_seconds=0,
                    errors=["No active nodes available"],
                    verification_passed=False,
                    rollback_available=False
                )
            node_id = nodes[0].node_id
        
        # Create and execute recovery plan
        plan = self.create_recovery_plan(node_id, target_path, recovery_type='full')
        
        if not plan:
            return RecoveryResult(
                recovery_id="quick_recovery_failed",
                timestamp=datetime.utcnow(),
                source_node=node_id,
                success=False,
                files_restored=0,
                bytes_restored=0,
                duration_seconds=0,
                errors=["Could not create recovery plan"],
                verification_passed=False,
                rollback_available=False
            )
        
        return self.execute_recovery(plan)
    
    def rollback_recovery(self, target_path: str) -> bool:
        """Rollback to backup if recovery failed."""
        target = Path(target_path)
        parent = target.parent
        
        # Find most recent rollback
        rollback_files = sorted(parent.glob(f"{target.name}.rollback_*"), reverse=True)
        
        if not rollback_files:
            return False
        
        latest_rollback = rollback_files[0]
        
        try:
            shutil.copy2(str(latest_rollback), str(target))
            return True
        except Exception:
            return False
