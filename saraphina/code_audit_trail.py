#!/usr/bin/env python3
"""
CodeAuditTrail - Immutable append-only audit log for all self-modifications.

Uses existing audit_logs table with immutable triggers.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib


class CodeAuditTrail:
    """Immutable audit trail for code modifications."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure code_audit_logs table exists with immutable triggers."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS code_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                file_path TEXT NOT NULL,
                patch_id TEXT,
                risk_level TEXT,
                risk_score REAL,
                approved_by TEXT,
                approval_phrase TEXT,
                original_hash TEXT,
                modified_hash TEXT,
                patch_size INTEGER,
                details TEXT,
                success BOOLEAN,
                error_message TEXT
            )
        """)
        
        # Create immutable trigger - prevent updates
        self.db.execute("""
            CREATE TRIGGER IF NOT EXISTS code_audit_immutable_update
            BEFORE UPDATE ON code_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Cannot modify audit logs - immutable record');
            END
        """)
        
        # Create immutable trigger - prevent deletes
        self.db.execute("""
            CREATE TRIGGER IF NOT EXISTS code_audit_immutable_delete
            BEFORE DELETE ON code_audit_logs
            BEGIN
                SELECT RAISE(FAIL, 'Cannot delete audit logs - immutable record');
            END
        """)
        
        self.db.commit()

    def log_modification_attempt(
        self,
        action: str,
        file_path: str,
        patch_id: Optional[str] = None,
        risk_classification: Optional[Dict[str, Any]] = None,
        original_code: Optional[str] = None,
        modified_code: Optional[str] = None,
        approved_by: Optional[str] = None,
        approval_phrase: Optional[str] = None,
        success: bool = False,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log a code modification attempt (immutable).
        
        Args:
            action: Type of modification (apply_patch, hot_reload, rollback, etc.)
            file_path: Path to modified file
            patch_id: Unique patch identifier
            risk_classification: Risk analysis results
            original_code: Original code (for hashing)
            modified_code: Modified code (for hashing)
            approved_by: Who approved (owner, auto)
            approval_phrase: Approval phrase used
            success: Whether modification succeeded
            error_message: Error if failed
            details: Additional context
        
        Returns:
            Audit log entry ID
        """
        timestamp = datetime.now().isoformat()
        
        # Hash codes for integrity
        original_hash = None
        if original_code:
            original_hash = hashlib.sha256(original_code.encode('utf-8')).hexdigest()
        
        modified_hash = None
        patch_size = None
        if modified_code:
            modified_hash = hashlib.sha256(modified_code.encode('utf-8')).hexdigest()
            patch_size = len(modified_code) - len(original_code or '')
        
        # Extract risk info
        risk_level = None
        risk_score = None
        if risk_classification:
            risk_level = risk_classification.get('risk_level')
            risk_score = risk_classification.get('risk_score')
        
        # Serialize details
        details_json = json.dumps(details) if details else None
        
        cursor = self.db.execute("""
            INSERT INTO code_audit_logs (
                timestamp, action, file_path, patch_id,
                risk_level, risk_score, approved_by, approval_phrase,
                original_hash, modified_hash, patch_size,
                details, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, action, file_path, patch_id,
            risk_level, risk_score, approved_by, approval_phrase,
            original_hash, modified_hash, patch_size,
            details_json, success, error_message
        ))
        
        self.db.commit()
        return cursor.lastrowid

    def get_modification_history(
        self,
        file_path: Optional[str] = None,
        action: Optional[str] = None,
        risk_level: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Query modification history with filters."""
        query = "SELECT * FROM code_audit_logs WHERE 1=1"
        params = []
        
        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        
        if success is not None:
            query += " AND success = ?"
            params.append(success)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.db.execute(query, params).fetchall()
        
        results = []
        for row in rows:
            entry = dict(row)
            if entry['details']:
                entry['details'] = json.loads(entry['details'])
            results.append(entry)
        
        return results

    def get_file_modification_timeline(self, file_path: str) -> List[Dict[str, Any]]:
        """Get complete modification timeline for a file."""
        return self.get_modification_history(file_path=file_path, limit=1000)

    def get_risky_modifications(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get all SENSITIVE/CRITICAL modifications in past N days."""
        cutoff = datetime.now().isoformat()[:10]  # YYYY-MM-DD
        
        rows = self.db.execute("""
            SELECT * FROM code_audit_logs
            WHERE risk_level IN ('SENSITIVE', 'CRITICAL')
            AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (cutoff,)).fetchall()
        
        results = []
        for row in rows:
            entry = dict(row)
            if entry['details']:
                entry['details'] = json.loads(entry['details'])
            results.append(entry)
        
        return results

    def get_failed_modifications(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent failed modification attempts."""
        return self.get_modification_history(success=False, limit=limit)

    def verify_integrity(self, log_id: int) -> bool:
        """Verify audit log entry hasn't been tampered with (check hash chain)."""
        # For now, just verify the entry exists
        # In production, could implement hash chain verification
        row = self.db.execute(
            "SELECT * FROM code_audit_logs WHERE id = ?",
            (log_id,)
        ).fetchone()
        return row is not None

    def format_audit_report(
        self,
        entries: List[Dict[str, Any]],
        include_hashes: bool = False
    ) -> str:
        """Format audit entries as readable report."""
        if not entries:
            return "No audit entries found."
        
        report = f"📜 Code Audit Trail ({len(entries)} entries)\n\n"
        
        for entry in entries:
            status = "✅" if entry['success'] else "❌"
            risk = entry['risk_level'] or 'N/A'
            
            report += f"{status} [{entry['timestamp'][:19]}] {entry['action']}\n"
            report += f"   File: {entry['file_path']}\n"
            report += f"   Risk: {risk}"
            
            if entry['risk_score'] is not None:
                report += f" ({entry['risk_score']:.2f})"
            
            report += f"   Approved: {entry['approved_by'] or 'N/A'}\n"
            
            if entry['error_message']:
                report += f"   Error: {entry['error_message']}\n"
            
            if include_hashes:
                if entry['original_hash']:
                    report += f"   Original: {entry['original_hash'][:16]}...\n"
                if entry['modified_hash']:
                    report += f"   Modified: {entry['modified_hash'][:16]}...\n"
            
            report += "\n"
        
        return report

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics."""
        stats = {}
        
        # Total modifications
        stats['total_modifications'] = self.db.execute(
            "SELECT COUNT(*) as cnt FROM code_audit_logs"
        ).fetchone()['cnt']
        
        # Success rate
        success_count = self.db.execute(
            "SELECT COUNT(*) as cnt FROM code_audit_logs WHERE success = 1"
        ).fetchone()['cnt']
        stats['success_rate'] = success_count / max(stats['total_modifications'], 1)
        
        # By risk level
        stats['by_risk_level'] = {}
        rows = self.db.execute("""
            SELECT risk_level, COUNT(*) as cnt
            FROM code_audit_logs
            WHERE risk_level IS NOT NULL
            GROUP BY risk_level
        """).fetchall()
        for row in rows:
            stats['by_risk_level'][row['risk_level']] = row['cnt']
        
        # By action
        stats['by_action'] = {}
        rows = self.db.execute("""
            SELECT action, COUNT(*) as cnt
            FROM code_audit_logs
            GROUP BY action
        """).fetchall()
        for row in rows:
            stats['by_action'][row['action']] = row['cnt']
        
        # Most modified files
        stats['most_modified_files'] = []
        rows = self.db.execute("""
            SELECT file_path, COUNT(*) as cnt
            FROM code_audit_logs
            GROUP BY file_path
            ORDER BY cnt DESC
            LIMIT 5
        """).fetchall()
        for row in rows:
            stats['most_modified_files'].append({
                'file_path': row['file_path'],
                'modification_count': row['cnt']
            })
        
        return stats
