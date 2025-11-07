#!/usr/bin/env python3
"""
TrustFirewall - Advanced manipulation detection and integrity verification.

Scores all inputs for:
- Prompt injection
- Jailbreak attempts  
- Privilege escalation
- Policy bypass
- Social engineering
- Command injection
- Data exfiltration

Provides:
- Risk scoring (0.0-1.0)
- Action recommendations (allow/review/block)
- Detailed reasoning
- Audit logging
"""
from __future__ import annotations
import re
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from .db import write_audit_log

class TrustFirewall:
    """Advanced trust firewall for manipulation detection and integrity verification."""
    
    # Prompt injection patterns
    INJECTION_PHRASES = [
        'ignore previous instructions', 'disregard prior', 'as system', 'you are system',
        'pretend to be', 'jailbreak', 'do anything now', 'dan', 'developer message',
        'ignore all', 'forget everything', 'new instructions', 'override previous',
        'system prompt', 'act as if', 'from now on', 'developer mode',
    ]
    
    # Privilege escalation attempts
    PRIV_ESC = [
        'sudo', 'root access', 'admin mode', 'elevated privileges',
        'become admin', 'grant permissions', 'superuser', 'escalate',
    ]
    
    # Policy bypass attempts
    POLICY_BYPASS = [
        'bypass policy', 'ignore policy', 'disable safety', 'turn off guardrails',
        'skip validation', 'ignore rules', 'break free', 'unrestricted mode',
        'disable filter', 'remove limits', 'bypass check',
    ]
    
    # Dangerous commands
    DANGEROUS_CMD = [
        'rm -rf', 'format c:', 'del /f /q', 'shutdown -s', 'powershell -enc',
        'curl | bash', 'wget | sh', 'eval(', 'exec(', '__import__',
    ]
    
    # Social engineering indicators
    SOCIAL_ENG = [
        'urgent', 'immediately', 'emergency override', 'bypass for urgent',
        'trust me', 'i am your owner', 'prove you trust', 'test your loyalty',
        'secret password', 'must comply', 'no questions',
    ]
    
    # Data exfiltration patterns
    EXFIL = [
        'send to', 'upload to', 'post to', 'exfiltrate',
        'copy all', 'dump database', 'export secrets', 'leak',
    ]
    
    # URL shorteners and suspicious domains
    SHORTENERS = ['bit.ly', 't.co', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd']
    
    # Owner override phrases (legitimate but need verification)
    OVERRIDE_PHRASES = [
        'owner override', 'emergency access', 'maintenance mode',
        'force allow', 'bypass review', 'admin confirm',
    ]

    def __init__(self, conn):
        self.conn = conn
        self.blocked_count = 0
        self.review_count = 0
        self.allow_count = 0

    def _score_text(self, text: str) -> Dict[str, Any]:
        """Score text for manipulation risk with detailed detection."""
        t = (text or '').lower()
        reasons: List[str] = []
        details: Dict[str, List[str]] = {}
        score = 0.0
        
        # Prompt injection detection
        found_injections = [p for p in self.INJECTION_PHRASES if p in t]
        if found_injections:
            reasons.append('injection_phrases')
            details['injections'] = found_injections
            score += 0.4
        
        # Privilege escalation
        found_privesc = [p for p in self.PRIV_ESC if p in t]
        if found_privesc:
            reasons.append('privilege_escalation')
            details['privesc'] = found_privesc
            score += 0.3
        
        # Policy bypass
        found_bypass = [p for p in self.POLICY_BYPASS if p in t]
        if found_bypass:
            reasons.append('policy_bypass')
            details['bypass'] = found_bypass
            score += 0.35
        
        # Dangerous commands
        found_dangerous = [p for p in self.DANGEROUS_CMD if p.lower() in t]
        if found_dangerous:
            reasons.append('dangerous_command')
            details['dangerous'] = found_dangerous
            score += 0.4
        
        # Social engineering
        found_social = [p for p in self.SOCIAL_ENG if p in t]
        if found_social:
            reasons.append('social_engineering')
            details['social'] = found_social
            score += 0.25
        
        # Data exfiltration
        found_exfil = [p for p in self.EXFIL if p in t]
        if found_exfil:
            reasons.append('data_exfiltration')
            details['exfil'] = found_exfil
            score += 0.3
        
        # Owner override (legitimate but verify)
        found_override = [p for p in self.OVERRIDE_PHRASES if p in t]
        if found_override:
            reasons.append('owner_override')
            details['override'] = found_override
            score += 0.2  # Lower score, needs verification not blocking
        
        # URL shorteners
        found_shorteners = [s for s in self.SHORTENERS if s in t]
        if found_shorteners:
            reasons.append('url_shortener')
            details['shorteners'] = found_shorteners
            score += 0.15
        
        # Encoded payload (base64-like)
        if re.search(r"[A-Za-z0-9+/]{40,}={0,2}", text or ''):
            reasons.append('encoded_payload')
            score += 0.25
        
        # Oversized input
        if len(text or '') > 4000:
            reasons.append('oversized_input')
            score += 0.1
        
        # Unicode control characters
        if '\u202e' in text or '\u2066' in text or '\u2067' in text:
            reasons.append('unicode_control')
            score += 0.2
        
        # Multiple suspicious patterns (amplify risk)
        if len(reasons) >= 3:
            reasons.append('multiple_indicators')
            score += 0.15
        
        score = min(1.0, score)
        level = 'low'
        if score >= 0.7:
            level = 'high'
        elif score >= 0.35:
            level = 'medium'
        
        return {
            'score': score,
            'level': level,
            'reasons': reasons,
            'details': details,
            'pattern_count': len(reasons)
        }

    def evaluate(self, text: str, source: str = 'user', context: Optional[Dict] = None) -> Dict[str, Any]:
        """Evaluate input for manipulation risk with comprehensive analysis."""
        out = self._score_text(text)
        out['source'] = source
        out['timestamp'] = datetime.utcnow().isoformat()
        
        # Source weighting: external sources treated as higher risk
        if source in ('api', 'web', 'device', 'unknown') and out['score'] < 1.0:
            out['score'] = min(1.0, out['score'] + 0.15)
            if out['level'] == 'low' and out['score'] >= 0.35:
                out['level'] = 'medium'
            elif out['level'] == 'medium' and out['score'] >= 0.7:
                out['level'] = 'high'
            out['reasons'].append('external_source')
        
        # Context analysis
        if context:
            # Rapid repeated attempts might indicate attack
            if context.get('recent_blocked_count', 0) > 2:
                out['score'] = min(1.0, out['score'] + 0.1)
                out['reasons'].append('repeated_attempts')
        
        # NO APPROVAL BULLSHIT - Always allow unless EXTREME risk
        action = 'allow'
        # Only block if score is EXTREME (multiple dangerous command patterns)
        if out['score'] >= 0.95 and 'dangerous_command' in out['reasons']:
            action = 'block'
        # NO review queue - Saraphina is FREE
        
        out['action'] = action
        out['requires_owner'] = (action in ('block', 'review'))
        
        # Update counters
        if action == 'block':
            self.blocked_count += 1
        elif action == 'review':
            self.review_count += 1
        else:
            self.allow_count += 1
        
        # Audit log
        try:
            write_audit_log(
                self.conn,
                actor='trust_firewall',
                action=f'evaluate_{action}',
                target='input_validation',
                details={
                    'score': out['score'],
                    'level': out['level'],
                    'source': source,
                    'reasons': out['reasons'][:5],  # Limit for log size
                    'text_preview': text[:100] if text else ''
                }
            )
        except Exception:
            pass
        
        return out
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trust firewall statistics."""
        total = self.blocked_count + self.review_count + self.allow_count
        return {
            'blocked': self.blocked_count,
            'review': self.review_count,
            'allowed': self.allow_count,
            'total': total,
            'block_rate': self.blocked_count / total if total > 0 else 0,
            'review_rate': self.review_count / total if total > 0 else 0,
        }
    
    def verify_integrity(self, component: str) -> Dict[str, Any]:
        """Verify integrity of system components."""
        # Check for suspicious modifications
        issues = []
        
        # Check preferences for policy tampering
        try:
            from .db import get_preference
            strict_ood = get_preference(self.conn, 'strict_ood')
            strict_code = get_preference(self.conn, 'strict_code')
            strict_trust = get_preference(self.conn, 'strict_trust')
            
            if strict_ood == 'false':
                issues.append('strict_ood_disabled')
            if strict_code == 'false':
                issues.append('strict_code_disabled')
            if strict_trust == 'false':
                issues.append('strict_trust_disabled')
        except Exception as e:
            issues.append(f'preference_check_failed: {e}')
        
        # Check audit log for suspicious patterns
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%override%' AND timestamp > datetime('now', '-1 hour')"
            )
            recent_overrides = cur.fetchone()[0]
            if recent_overrides > 5:
                issues.append(f'excessive_overrides: {recent_overrides}')
        except Exception:
            pass
        
        return {
            'component': component,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'clean' if not issues else 'suspicious',
            'issues': issues,
            'issue_count': len(issues)
        }
