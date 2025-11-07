#!/usr/bin/env python3
"""
Upgrade Ledger - Complete history of all code modifications

Different from Learning Journal:
- Learning Journal: Learns patterns from upgrade attempts (success/failure)
- Upgrade Ledger: Audit trail of actual code changes made to the system

Tracks:
- Every file modification with full diff
- Why the change was made (roadmap gap, error fix, user request)
- How it was made (GPT-4, manual, automated)
- Validation results before applying
- Rollback status if failed
"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import difflib

logger = logging.getLogger("UpgradeLedger")


@dataclass
class ChangeRecord:
    """Record of a single code modification"""
    timestamp: str
    files_changed: List[str]
    diff: str  # Unified diff
    reason_type: str  # 'roadmap_gap', 'error_fix', 'user_request', 'refactor'
    reason_description: str
    method: str  # 'gpt4', 'manual', 'automated'
    artifact_id: Optional[str] = None
    validation_passed: bool = True
    validation_details: Optional[str] = None
    applied: bool = False
    rolled_back: bool = False
    rollback_reason: Optional[str] = None
    user_approved: bool = False


class UpgradeLedger:
    """Audit trail for all code modifications"""
    
    def __init__(self, db_path: str = "D:\\Saraphina Root\\data\\upgrade_ledger.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        logger.info(f"Upgrade Ledger initialized: {self.db_path}")
    
    def _init_database(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main change log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                reason_type TEXT NOT NULL,
                reason_description TEXT,
                method TEXT,
                artifact_id TEXT,
                validation_passed BOOLEAN,
                validation_details TEXT,
                applied BOOLEAN,
                rolled_back BOOLEAN,
                rollback_reason TEXT,
                user_approved BOOLEAN
            )
        """)
        
        # Files changed (one-to-many relationship)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files_changed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_id INTEGER,
                file_path TEXT,
                change_type TEXT,
                lines_added INTEGER,
                lines_removed INTEGER,
                FOREIGN KEY(change_id) REFERENCES change_log(id)
            )
        """)
        
        # Diffs (store actual code changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_id INTEGER,
                file_path TEXT,
                diff_text TEXT,
                old_content TEXT,
                new_content TEXT,
                FOREIGN KEY(change_id) REFERENCES change_log(id)
            )
        """)
        
        # Rollback history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rollbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_id INTEGER,
                rollback_timestamp TEXT,
                reason TEXT,
                success BOOLEAN,
                FOREIGN KEY(change_id) REFERENCES change_log(id)
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON change_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reason_type ON change_log(reason_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applied ON change_log(applied)")
        
        conn.commit()
        conn.close()
    
    def record_change(self, files_old: Dict[str, str], files_new: Dict[str, str],
                     reason_type: str, reason_description: str, method: str = "gpt4",
                     artifact_id: str = None, validation_passed: bool = True,
                     validation_details: str = None, user_approved: bool = False) -> int:
        """
        Record a code modification
        
        Args:
            files_old: Dict of filename -> old content
            files_new: Dict of filename -> new content
            reason_type: Why the change ('roadmap_gap', 'error_fix', 'user_request')
            reason_description: Human-readable description
            method: How generated ('gpt4', 'manual', 'automated')
            artifact_id: Optional artifact ID from CodeForge
            validation_passed: Did validation pass
            validation_details: Validation results
            user_approved: Was change approved by user
        
        Returns:
            Change ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert change record
        cursor.execute("""
            INSERT INTO change_log
            (timestamp, reason_type, reason_description, method, artifact_id,
             validation_passed, validation_details, applied, rolled_back,
             rollback_reason, user_approved)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, NULL, ?)
        """, (
            datetime.now().isoformat(),
            reason_type,
            reason_description,
            method,
            artifact_id,
            validation_passed,
            validation_details,
            user_approved
        ))
        
        change_id = cursor.lastrowid
        
        # Record each file change
        all_files = set(files_old.keys()) | set(files_new.keys())
        
        for file_path in all_files:
            old_content = files_old.get(file_path, "")
            new_content = files_new.get(file_path, "")
            
            # Determine change type
            if not old_content and new_content:
                change_type = "created"
            elif old_content and not new_content:
                change_type = "deleted"
            else:
                change_type = "modified"
            
            # Calculate line changes
            old_lines = old_content.split('\n') if old_content else []
            new_lines = new_content.split('\n') if new_content else []
            
            lines_added = len([l for l in new_lines if l.strip()]) - len([l for l in old_lines if l.strip()])
            lines_removed = max(0, -lines_added)
            lines_added = max(0, lines_added)
            
            cursor.execute("""
                INSERT INTO files_changed
                (change_id, file_path, change_type, lines_added, lines_removed)
                VALUES (?, ?, ?, ?, ?)
            """, (change_id, file_path, change_type, lines_added, lines_removed))
            
            # Generate and store diff
            diff_text = self._generate_diff(old_content, new_content, file_path)
            
            cursor.execute("""
                INSERT INTO diffs
                (change_id, file_path, diff_text, old_content, new_content)
                VALUES (?, ?, ?, ?, ?)
            """, (change_id, file_path, diff_text, old_content, new_content))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded change {change_id}: {reason_type} - {len(all_files)} files")
        
        return change_id
    
    def mark_applied(self, change_id: int, success: bool = True):
        """Mark a change as applied"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE change_log
            SET applied = ?
            WHERE id = ?
        """, (success, change_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Marked change {change_id} as applied: {success}")
    
    def record_rollback(self, change_id: int, reason: str, success: bool = True):
        """Record a rollback of a change"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update change log
        cursor.execute("""
            UPDATE change_log
            SET rolled_back = 1, rollback_reason = ?
            WHERE id = ?
        """, (reason, change_id))
        
        # Insert rollback record
        cursor.execute("""
            INSERT INTO rollbacks
            (change_id, rollback_timestamp, reason, success)
            VALUES (?, ?, ?, ?)
        """, (change_id, datetime.now().isoformat(), reason, success))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded rollback for change {change_id}: {reason}")
    
    def _generate_diff(self, old_content: str, new_content: str, filename: str) -> str:
        """Generate unified diff"""
        old_lines = old_content.split('\n') if old_content else []
        new_lines = new_content.split('\n') if new_content else []
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return '\n'.join(diff)
    
    def get_change_history(self, limit: int = 50, reason_type: str = None) -> List[Dict[str, Any]]:
        """Get recent change history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if reason_type:
            cursor.execute("""
                SELECT id, timestamp, reason_type, reason_description, method,
                       artifact_id, validation_passed, applied, rolled_back
                FROM change_log
                WHERE reason_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (reason_type, limit))
        else:
            cursor.execute("""
                SELECT id, timestamp, reason_type, reason_description, method,
                       artifact_id, validation_passed, applied, rolled_back
                FROM change_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        changes = []
        for row in cursor.fetchall():
            change_id = row[0]
            
            # Get files changed
            cursor.execute("""
                SELECT file_path, change_type, lines_added, lines_removed
                FROM files_changed
                WHERE change_id = ?
            """, (change_id,))
            
            files = [{'path': r[0], 'type': r[1], 'added': r[2], 'removed': r[3]}
                    for r in cursor.fetchall()]
            
            changes.append({
                'id': row[0],
                'timestamp': row[1],
                'reason_type': row[2],
                'reason': row[3],
                'method': row[4],
                'artifact_id': row[5],
                'validation_passed': row[6],
                'applied': row[7],
                'rolled_back': row[8],
                'files': files
            })
        
        conn.close()
        return changes
    
    def get_change_details(self, change_id: int) -> Dict[str, Any]:
        """Get full details of a specific change"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get change info
        cursor.execute("""
            SELECT timestamp, reason_type, reason_description, method, artifact_id,
                   validation_passed, validation_details, applied, rolled_back,
                   rollback_reason, user_approved
            FROM change_log
            WHERE id = ?
        """, (change_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Get files and diffs
        cursor.execute("""
            SELECT file_path, change_type, lines_added, lines_removed
            FROM files_changed
            WHERE change_id = ?
        """, (change_id,))
        
        files = [{'path': r[0], 'type': r[1], 'added': r[2], 'removed': r[3]}
                for r in cursor.fetchall()]
        
        # Get diffs
        cursor.execute("""
            SELECT file_path, diff_text
            FROM diffs
            WHERE change_id = ?
        """, (change_id,))
        
        diffs = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Get rollback history
        cursor.execute("""
            SELECT rollback_timestamp, reason, success
            FROM rollbacks
            WHERE change_id = ?
            ORDER BY rollback_timestamp DESC
        """, (change_id,))
        
        rollbacks = [{'timestamp': r[0], 'reason': r[1], 'success': r[2]}
                    for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            'id': change_id,
            'timestamp': row[0],
            'reason_type': row[1],
            'reason': row[2],
            'method': row[3],
            'artifact_id': row[4],
            'validation_passed': row[5],
            'validation_details': row[6],
            'applied': row[7],
            'rolled_back': row[8],
            'rollback_reason': row[9],
            'user_approved': row[10],
            'files': files,
            'diffs': diffs,
            'rollbacks': rollbacks
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ledger statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total changes
        cursor.execute("SELECT COUNT(*) FROM change_log")
        total_changes = cursor.fetchone()[0]
        
        # Applied changes
        cursor.execute("SELECT COUNT(*) FROM change_log WHERE applied = 1")
        applied = cursor.fetchone()[0]
        
        # Rolled back
        cursor.execute("SELECT COUNT(*) FROM change_log WHERE rolled_back = 1")
        rolled_back = cursor.fetchone()[0]
        
        # By reason type
        cursor.execute("""
            SELECT reason_type, COUNT(*) as count
            FROM change_log
            GROUP BY reason_type
            ORDER BY count DESC
        """)
        
        by_reason = [{'type': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        # By method
        cursor.execute("""
            SELECT method, COUNT(*) as count
            FROM change_log
            GROUP BY method
            ORDER BY count DESC
        """)
        
        by_method = [{'method': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        # Total files changed
        cursor.execute("SELECT COUNT(DISTINCT file_path) FROM files_changed")
        unique_files = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_changes': total_changes,
            'applied': applied,
            'rolled_back': rolled_back,
            'success_rate': (applied - rolled_back) / applied if applied > 0 else 0,
            'by_reason': by_reason,
            'by_method': by_method,
            'unique_files_modified': unique_files
        }
    
    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all changes made to a specific file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.timestamp, c.reason_type, c.reason_description,
                   f.change_type, f.lines_added, f.lines_removed
            FROM change_log c
            JOIN files_changed f ON c.id = f.change_id
            WHERE f.file_path = ?
            ORDER BY c.timestamp DESC
        """, (file_path,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'change_id': row[0],
                'timestamp': row[1],
                'reason_type': row[2],
                'reason': row[3],
                'change_type': row[4],
                'lines_added': row[5],
                'lines_removed': row[6]
            })
        
        conn.close()
        return history


# CLI
if __name__ == "__main__":
    import sys
    
    ledger = UpgradeLedger()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            stats = ledger.get_statistics()
            print("\n" + "="*60)
            print("UPGRADE LEDGER STATISTICS")
            print("="*60)
            print(f"Total Changes: {stats['total_changes']}")
            print(f"  Applied: {stats['applied']}")
            print(f"  Rolled Back: {stats['rolled_back']}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            print(f"\nUnique Files Modified: {stats['unique_files_modified']}")
            print("\nBy Reason:")
            for r in stats['by_reason']:
                print(f"  {r['type']}: {r['count']}")
            print("\nBy Method:")
            for m in stats['by_method']:
                print(f"  {m['method']}: {m['count']}")
            print("="*60)
        
        elif command == "history":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            changes = ledger.get_change_history(limit=limit)
            print(f"\n{len(changes)} recent changes:\n")
            for ch in changes:
                status = "✓" if ch['applied'] and not ch['rolled_back'] else "✗" if ch['rolled_back'] else "⏳"
                print(f"{status} [{ch['timestamp'][:19]}] {ch['reason_type']}")
                print(f"  {ch['reason']}")
                print(f"  Files: {', '.join(f['path'] for f in ch['files'])}\n")
        
        elif command == "details":
            if len(sys.argv) < 3:
                print("Usage: python upgrade_ledger.py details <change_id>")
            else:
                change_id = int(sys.argv[2])
                details = ledger.get_change_details(change_id)
                if details:
                    print("\n" + "="*60)
                    print(f"CHANGE #{details['id']}")
                    print("="*60)
                    print(f"Timestamp: {details['timestamp']}")
                    print(f"Reason: {details['reason_type']} - {details['reason']}")
                    print(f"Method: {details['method']}")
                    print(f"Validation: {'PASS' if details['validation_passed'] else 'FAIL'}")
                    print(f"Applied: {details['applied']}")
                    print(f"Rolled Back: {details['rolled_back']}")
                    print(f"\nFiles Changed:")
                    for f in details['files']:
                        print(f"  {f['type'].upper()}: {f['path']}")
                        print(f"    +{f['added']} -{f['removed']} lines")
                    print("="*60)
                else:
                    print(f"Change {change_id} not found")
    else:
        print("Usage: python upgrade_ledger.py [stats|history|details <id>]")
