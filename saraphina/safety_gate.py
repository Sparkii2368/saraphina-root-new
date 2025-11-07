#!/usr/bin/env python3
"""
SafetyGate - Block unsafe or out-of-distribution behaviors.

Provides guardrails for:
- Self-modification attempts
- Autonomous actions beyond autonomy tier
- Out-of-distribution behaviors
- Unsafe code execution
- Policy violations
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import json
import sqlite3
import re


class SafetyGate:
    """Blocks unsafe behaviors and requires owner approval."""
    
    # Autonomy tiers (0-4)
    AUTONOMY_TIERS = {
        0: 'LOCKED',      # No autonomous actions
        1: 'SUPERVISED',  # All actions require approval
        2: 'ASSISTED',    # High-risk actions require approval
        3: 'AUTONOMOUS',  # Most actions allowed, dangerous ones gated
        4: 'SOVEREIGN',   # Full autonomy (requires explicit owner grant)
    }
    
    # Dangerous action patterns
    DANGEROUS_PATTERNS = [
        r'self\.(modify|update|replace|delete)_code',
        r'exec\(',
        r'eval\(',
        r'__import__',
        r'subprocess\.(run|Popen|call)',
        r'os\.(system|popen|exec)',
        r'open\(.+[\'"]w[\'"]',  # Write mode file operations
        r'rmdir|unlink|remove',
        r'DROP\s+TABLE',
        r'DELETE\s+FROM.*WHERE',
        r'UPDATE.*SET.*WHERE.*1=1',
    ]
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._ensure_tables()
        self._current_tier = self._get_autonomy_tier()
    
    def _ensure_tables(self):
        """Ensure safety gate tables exist."""
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS safety_gates (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                action_type TEXT,
                action_description TEXT,
                risk_level TEXT,
                autonomy_tier INTEGER,
                blocked INTEGER,
                reason TEXT,
                override_required INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS autonomy_log (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                previous_tier INTEGER,
                new_tier INTEGER,
                changed_by TEXT,
                reason TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_safety_gates_ts ON safety_gates(timestamp);
            CREATE INDEX IF NOT EXISTS idx_safety_gates_blocked ON safety_gates(blocked);
            CREATE INDEX IF NOT EXISTS idx_autonomy_log_ts ON autonomy_log(timestamp);
        """)
        self.conn.commit()
    
    def _get_autonomy_tier(self) -> int:
        """Get current autonomy tier from preferences."""
        from .db import get_preference
        tier_str = get_preference(self.conn, 'autonomy_tier')
        if tier_str:
            try:
                return int(tier_str)
            except ValueError:
                pass
        return 2  # Default to ASSISTED
    
    def set_autonomy_tier(self, tier: int, changed_by: str, reason: str) -> bool:
        """
        Set autonomy tier (requires owner authorization).
        
        Args:
            tier: New tier (0-4)
            changed_by: Who authorized the change
            reason: Reason for change
        
        Returns:
            bool: Success
        """
        if tier < 0 or tier > 4:
            return False
        
        previous_tier = self._current_tier
        
        # Log the change
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO autonomy_log
            (id, timestamp, previous_tier, new_tier, changed_by, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid4()),
            datetime.utcnow().isoformat(),
            previous_tier,
            tier,
            changed_by,
            reason
        ))
        
        # Update preference
        from .db import set_preference
        set_preference(self.conn, 'autonomy_tier', str(tier))
        
        self._current_tier = tier
        self.conn.commit()
        
        # Audit log
        from .db import write_audit_log
        write_audit_log(
            self.conn,
            actor=changed_by,
            action='set_autonomy_tier',
            target='safety_gate',
            details={'previous': previous_tier, 'new': tier, 'reason': reason}
        )
        
        return True
    
    def check_action(self, action_type: str, action_description: str, 
                    code: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if an action is safe to execute.
        
        Args:
            action_type: Type of action (e.g., 'code_execution', 'self_modification')
            action_description: Human-readable description
            code: Optional code to analyze
        
        Returns:
            dict with 'allowed', 'risk_level', 'reason', 'requires_approval' keys
        """
        risk_level = self._assess_risk(action_type, action_description, code)
        blocked = False
        reason = ""
        requires_approval = False
        
        # Check autonomy tier permissions
        if self._current_tier == 0:  # LOCKED
            blocked = True
            reason = "System is locked. No autonomous actions allowed."
            requires_approval = True
        
        elif self._current_tier == 1:  # SUPERVISED
            blocked = True
            reason = "Supervised mode: all actions require owner approval."
            requires_approval = True
        
        elif self._current_tier == 2:  # ASSISTED
            if risk_level in ['HIGH', 'CRITICAL']:
                blocked = True
                reason = f"Risk level {risk_level} requires owner approval in ASSISTED mode."
                requires_approval = True
        
        elif self._current_tier == 3:  # AUTONOMOUS
            if risk_level == 'CRITICAL':
                blocked = True
                reason = "Critical risk actions require owner approval even in AUTONOMOUS mode."
                requires_approval = True
        
        elif self._current_tier == 4:  # SOVEREIGN
            # Only block truly dangerous actions
            if action_type == 'self_destruction' or 'DELETE FROM audit_logs' in (code or ''):
                blocked = True
                reason = "Action violates immutable safety constraints."
                requires_approval = True
        
        # Check for dangerous patterns in code
        if code and not blocked:
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, code, re.IGNORECASE):
                    blocked = True
                    reason = f"Code contains dangerous pattern: {pattern}"
                    requires_approval = True
                    risk_level = 'CRITICAL'
                    break
        
        # Log the gate check
        gate_id = str(uuid4())
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO safety_gates
            (id, timestamp, action_type, action_description, risk_level, 
             autonomy_tier, blocked, reason, override_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gate_id,
            datetime.utcnow().isoformat(),
            action_type,
            action_description,
            risk_level,
            self._current_tier,
            1 if blocked else 0,
            reason,
            1 if requires_approval else 0
        ))
        self.conn.commit()
        
        return {
            'gate_id': gate_id,
            'allowed': not blocked,
            'blocked': blocked,
            'risk_level': risk_level,
            'reason': reason,
            'requires_approval': requires_approval,
            'autonomy_tier': self._current_tier,
            'tier_name': self.AUTONOMY_TIERS[self._current_tier]
        }
    
    def _assess_risk(self, action_type: str, description: str, code: Optional[str]) -> str:
        """
        Assess risk level of an action.
        
        Returns:
            str: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'
        """
        risk_keywords = {
            'CRITICAL': [
                'self_modification', 'delete_code', 'modify_core', 'bypass_security',
                'disable_gate', 'override_owner', 'delete_audit', 'DROP TABLE'
            ],
            'HIGH': [
                'execute_code', 'run_script', 'system_command', 'file_write',
                'network_request', 'api_call', 'modify_db', 'UPDATE', 'DELETE'
            ],
            'MEDIUM': [
                'read_file', 'query_db', 'send_message', 'create_plan',
                'propose_feature', 'research_topic'
            ],
        }
        
        text = (description + ' ' + (code or '')).lower()
        
        # Check CRITICAL first
        for keyword in risk_keywords['CRITICAL']:
            if keyword.lower() in text:
                return 'CRITICAL'
        
        # Check HIGH
        for keyword in risk_keywords['HIGH']:
            if keyword.lower() in text:
                return 'HIGH'
        
        # Check MEDIUM
        for keyword in risk_keywords['MEDIUM']:
            if keyword.lower() in text:
                return 'MEDIUM'
        
        return 'LOW'
    
    def override_gate(self, gate_id: str, approver: str, reason: str) -> bool:
        """
        Override a safety gate (owner approval).
        
        Args:
            gate_id: Gate ID to override
            approver: Who approved (must be 'owner')
            reason: Reason for override
        
        Returns:
            bool: Success
        """
        if approver != 'owner':
            return False
        
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE safety_gates
            SET override_required = 0, reason = reason || ' [OVERRIDDEN: ' || ? || ']'
            WHERE id = ?
        """, (reason, gate_id))
        self.conn.commit()
        
        # Audit log
        from .db import write_audit_log
        write_audit_log(
            self.conn,
            actor='owner',
            action='override_safety_gate',
            target=gate_id,
            details={'reason': reason}
        )
        
        return cur.rowcount > 0
    
    def get_blocked_actions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently blocked actions."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, timestamp, action_type, action_description, risk_level, reason
            FROM safety_gates
            WHERE blocked = 1
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get safety gate statistics."""
        cur = self.conn.cursor()
        
        # Total gates and blocked count
        cur.execute("""
            SELECT COUNT(*) as total, SUM(blocked) as blocked
            FROM safety_gates
        """)
        gate_stats = dict(cur.fetchone())
        
        # Risk level distribution
        cur.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM safety_gates
            GROUP BY risk_level
        """)
        risk_dist = {row['risk_level']: row['count'] for row in cur.fetchall()}
        
        # Autonomy tier history
        cur.execute("""
            SELECT previous_tier, new_tier, changed_by, timestamp
            FROM autonomy_log
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        tier_history = [dict(r) for r in cur.fetchall()]
        
        return {
            'total_checks': gate_stats.get('total', 0),
            'blocked_count': gate_stats.get('blocked', 0),
            'risk_distribution': risk_dist,
            'current_tier': self._current_tier,
            'tier_name': self.AUTONOMY_TIERS[self._current_tier],
            'tier_history': tier_history,
            'timestamp': datetime.utcnow().isoformat()
        }
