#!/usr/bin/env python3
"""
OwnerApprovalGate - Risk-based approval system for self-modifications.

Approval Phrases by Risk Level:
- SAFE: Auto-approved
- CAUTION: "I approve this change"
- SENSITIVE: "I approve this sensitive change and accept the risks"
- CRITICAL: "I approve this critical change with full awareness of system impact"
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path


class OwnerApprovalGate:
    """Manage risk-based approval requirements for code modifications."""

    # Required approval phrases by risk level
    APPROVAL_PHRASES = {
        'SAFE': None,  # Auto-approved
        'CAUTION': 'I approve this change',
        'SENSITIVE': 'I approve this sensitive change and accept the risks',
        'CRITICAL': 'I approve this critical change with full awareness of system impact'
    }

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pending_file = self.data_dir / 'pending_approvals.json'
        self.pending_approvals = self._load_pending()

    def _load_pending(self) -> Dict[str, Dict[str, Any]]:
        """Load pending approval requests."""
        if self.pending_file.exists():
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_pending(self):
        """Save pending approval requests."""
        with open(self.pending_file, 'w', encoding='utf-8') as f:
            json.dump(self.pending_approvals, f, indent=2)

    def request_approval(
        self,
        patch_id: str,
        risk_classification: Dict[str, Any],
        patch_details: Dict[str, Any]
    ) -> Optional[str]:
        """
        Request owner approval for a patch.
        
        Returns:
            Required approval phrase if approval needed, None if auto-approved
        """
        risk_level = risk_classification['risk_level']
        
        # Auto-approve SAFE changes
        if risk_level == 'SAFE':
            return None
        
        # Store pending approval
        self.pending_approvals[patch_id] = {
            'risk_classification': risk_classification,
            'patch_details': patch_details,
            'requested_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        self._save_pending()
        
        return self.APPROVAL_PHRASES[risk_level]

    def verify_approval(self, patch_id: str, user_response: str) -> Dict[str, Any]:
        """
        Verify owner approval response.
        
        Returns:
            Dict with approved: bool, reason: str
        """
        if patch_id not in self.pending_approvals:
            return {
                'approved': False,
                'reason': 'No pending approval found for this patch'
            }
        
        pending = self.pending_approvals[patch_id]
        risk_level = pending['risk_classification']['risk_level']
        required_phrase = self.APPROVAL_PHRASES[risk_level]
        
        # Check if user response contains required phrase
        if required_phrase and required_phrase.lower() in user_response.lower():
            pending['status'] = 'approved'
            pending['approved_at'] = datetime.now().isoformat()
            self._save_pending()
            return {
                'approved': True,
                'reason': 'Approval phrase verified'
            }
        else:
            return {
                'approved': False,
                'reason': f'Required phrase not found: "{required_phrase}"'
            }

    def deny_patch(self, patch_id: str, reason: str = 'Owner denied'):
        """Mark patch as denied."""
        if patch_id in self.pending_approvals:
            self.pending_approvals[patch_id]['status'] = 'denied'
            self.pending_approvals[patch_id]['denied_at'] = datetime.now().isoformat()
            self.pending_approvals[patch_id]['denial_reason'] = reason
            self._save_pending()

    def get_pending_approvals(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending approval requests."""
        return {
            k: v for k, v in self.pending_approvals.items()
            if v['status'] == 'pending'
        }

    def clear_pending(self, patch_id: str):
        """Clear a pending approval (after applied or rejected)."""
        if patch_id in self.pending_approvals:
            del self.pending_approvals[patch_id]
            self._save_pending()

    def format_approval_request(
        self,
        patch_id: str,
        risk_classification: Dict[str, Any],
        patch_details: Dict[str, Any]
    ) -> str:
        """Format approval request message for user."""
        from .code_risk_model import CodeRiskModel
        
        risk_model = CodeRiskModel()
        risk_report = risk_model.format_risk_report(risk_classification)
        
        risk_level = risk_classification['risk_level']
        required_phrase = self.APPROVAL_PHRASES[risk_level]
        
        message = f"📋 Approval Request for Patch {patch_id}\n\n"
        message += f"File: {patch_details.get('file_path', 'Unknown')}\n"
        message += f"Description: {patch_details.get('description', 'No description')}\n\n"
        message += risk_report
        message += f"\n\n⚠️  To approve, please say:\n"
        message += f'"{required_phrase}"\n'
        
        return message

    def get_approval_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent approval history."""
        history = []
        for patch_id, details in self.pending_approvals.items():
            if details['status'] in ['approved', 'denied']:
                history.append({
                    'patch_id': patch_id,
                    'status': details['status'],
                    'risk_level': details['risk_classification']['risk_level'],
                    'timestamp': details.get('approved_at') or details.get('denied_at'),
                    'file_path': details['patch_details'].get('file_path', 'Unknown')
                })
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history[:limit]
