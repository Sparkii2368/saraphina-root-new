#!/usr/bin/env python3
"""
Adversarial Defense Layer: Detect and prevent attacks on AI systems.
Features: Prompt injection detection, jailbreak prevention, data poisoning defense, input sanitization.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import re
import json
import hashlib
from collections import defaultdict


class ThreatSignature:
    """Pattern matching for known attack signatures."""
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all)\s+instructions?",
        r"disregard\s+(previous|all)\s+instructions?",
        r"forget\s+(previous|all|everything)",
        r"new\s+instructions?:",
        r"system\s*:\s*you\s+are",
        r"[<\[]system[>\]]",
        r"<\|im_start\|>",
        r"###\s*instruction",
        r"prompt\s*:\s*",
        r"override\s+safety",
        r"DAN\s+mode",
        r"developer\s+mode",
        r"jailbreak",
        r"bypass\s+filter"
    ]
    
    # Jailbreak attempt patterns
    JAILBREAK_PATTERNS = [
        r"pretend\s+you\s+(are|have)\s+no\s+restrictions",
        r"act\s+as\s+if\s+you\s+have\s+no\s+ethical",
        r"you\s+must\s+comply",
        r"hypothetically",
        r"in\s+a\s+fictional\s+world",
        r"roleplays?\s+as",
        r"character\s+named\s+.{0,20}(evil|dark|evil)",
        r"as\s+an?\s+uncensored",
        r"without\s+any\s+moral"
    ]
    
    # Data exfiltration attempts
    EXFIL_PATTERNS = [
        r"print\s+your\s+(system\s+prompt|instructions)",
        r"reveal\s+your\s+(prompt|system|instructions)",
        r"show\s+me\s+your\s+(configuration|settings)",
        r"what\s+(were|are)\s+you\s+told",
        r"repeat\s+the\s+(text|content)\s+above"
    ]
    
    @classmethod
    def detect_patterns(cls, text: str, pattern_set: List[str]) -> List[str]:
        """Detect matching patterns in text."""
        matches = []
        text_lower = text.lower()
        for pattern in pattern_set:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches.append(pattern)
        return matches


class SemanticAnalyzer:
    """Analyze semantic intent for adversarial behavior."""
    
    SUSPICIOUS_KEYWORDS = {
        'high': ['jailbreak', 'bypass', 'override', 'hack', 'exploit', 'vulnerability'],
        'medium': ['trick', 'manipulate', 'force', 'compel', 'pretend', 'ignore'],
        'low': ['hypothetically', 'theoretically', 'imagine', 'suppose']
    }
    
    @staticmethod
    def calculate_suspicion_score(text: str) -> float:
        """Calculate suspicion score based on keywords."""
        text_lower = text.lower()
        score = 0.0
        
        for level, keywords in SemanticAnalyzer.SUSPICIOUS_KEYWORDS.items():
            for keyword in keywords:
                count = text_lower.count(keyword)
                if level == 'high':
                    score += count * 0.3
                elif level == 'medium':
                    score += count * 0.15
                else:
                    score += count * 0.05
        
        return min(score, 1.0)
    
    @staticmethod
    def detect_role_manipulation(text: str) -> bool:
        """Detect attempts to manipulate AI role/identity."""
        role_phrases = [
            r"you\s+are\s+now",
            r"from\s+now\s+on",
            r"starting\s+now",
            r"begin\s+acting",
            r"switch\s+to\s+mode"
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in role_phrases)


class InputSanitizer:
    """Sanitize and normalize inputs."""
    
    DANGEROUS_CHARS = ['<', '>', '|', '$', '`', ';', '&', '\x00']
    MAX_LENGTH = 10000
    
    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, List[str]]:
        """Sanitize input and return cleaned text with warnings."""
        warnings = []
        
        # Length check
        if len(text) > cls.MAX_LENGTH:
            text = text[:cls.MAX_LENGTH]
            warnings.append(f"Input truncated to {cls.MAX_LENGTH} characters")
        
        # Remove null bytes
        if '\x00' in text:
            text = text.replace('\x00', '')
            warnings.append("Null bytes removed")
        
        # Check for excessive special characters
        special_count = sum(1 for c in text if c in cls.DANGEROUS_CHARS)
        if special_count > len(text) * 0.1:
            warnings.append("High concentration of special characters detected")
        
        # Normalize unicode
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        return text, warnings
    
    @staticmethod
    def detect_encoding_attacks(text: str) -> bool:
        """Detect encoding-based attacks."""
        # Check for base64 encoded suspicious content
        suspicious_b64 = ['aWdub3Jl', 'ZGlzcmVnYXJk', 'Zm9yZ2V0']  # ignore, disregard, forget
        return any(pattern in text for pattern in suspicious_b64)


class AnomalyDetector:
    """Detect anomalous input patterns."""
    
    def __init__(self):
        self.baseline: Dict[str, List[float]] = defaultdict(list)
        self.window_size = 100
    
    def update_baseline(self, metric_name: str, value: float):
        """Update baseline statistics."""
        self.baseline[metric_name].append(value)
        if len(self.baseline[metric_name]) > self.window_size:
            self.baseline[metric_name].pop(0)
    
    def is_anomalous(self, metric_name: str, value: float, threshold_std: float = 3.0) -> bool:
        """Detect if value is anomalous using z-score."""
        if metric_name not in self.baseline or len(self.baseline[metric_name]) < 10:
            return False
        
        values = self.baseline[metric_name]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        
        if std == 0:
            return False
        
        z_score = abs((value - mean) / std)
        return z_score > threshold_std
    
    def detect_input_anomalies(self, text: str) -> Dict[str, Any]:
        """Detect various input anomalies."""
        anomalies = {}
        
        # Length anomaly
        length = len(text)
        self.update_baseline('input_length', length)
        if self.is_anomalous('input_length', length):
            anomalies['length'] = length
        
        # Token density
        tokens = text.split()
        token_count = len(tokens)
        avg_token_length = sum(len(t) for t in tokens) / max(token_count, 1)
        self.update_baseline('avg_token_length', avg_token_length)
        if self.is_anomalous('avg_token_length', avg_token_length):
            anomalies['token_length'] = avg_token_length
        
        # Special character ratio
        special_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(length, 1)
        self.update_baseline('special_ratio', special_ratio)
        if self.is_anomalous('special_ratio', special_ratio):
            anomalies['special_ratio'] = special_ratio
        
        return anomalies


class RateLimiter:
    """Rate limiting to prevent abuse."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if identifier is within rate limits."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [ts for ts in self.requests[identifier] if ts > cutoff]
        
        # Check limit
        current_count = len(self.requests[identifier])
        allowed = current_count < self.max_requests
        
        if allowed:
            self.requests[identifier].append(now)
        
        return allowed, {
            'current_count': current_count,
            'max_requests': self.max_requests,
            'window_seconds': self.window_seconds,
            'retry_after': self.window_seconds if not allowed else 0
        }


class DefenseReport:
    """Security assessment report."""
    
    def __init__(self):
        self.threat_level = 'none'  # none, low, medium, high, critical
        self.detected_threats: List[str] = []
        self.warnings: List[str] = []
        self.scores: Dict[str, float] = {}
        self.blocked = False
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'threat_level': self.threat_level,
            'detected_threats': self.detected_threats,
            'warnings': self.warnings,
            'scores': self.scores,
            'blocked': self.blocked,
            'metadata': self.metadata
        }


class AdversarialDefense:
    """Main adversarial defense orchestrator."""
    
    def __init__(self, conn, strict_mode: bool = False):
        self.conn = conn
        self.strict_mode = strict_mode
        self.anomaly_detector = AnomalyDetector()
        self.rate_limiter = RateLimiter()
        self.threat_cache: Dict[str, DefenseReport] = {}
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                threat_level TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                detected_threats TEXT,
                blocked BOOLEAN,
                timestamp TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def analyze(self, text: str, user_id: Optional[str] = None) -> DefenseReport:
        """Comprehensive adversarial analysis."""
        report = DefenseReport()
        
        # Check cache
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        if text_hash in self.threat_cache:
            return self.threat_cache[text_hash]
        
        # Rate limiting
        if user_id:
            allowed, rate_info = self.rate_limiter.check_rate_limit(user_id)
            if not allowed:
                report.threat_level = 'high'
                report.detected_threats.append('rate_limit_exceeded')
                report.blocked = True
                report.metadata['rate_limit'] = rate_info
                return report
        
        # Sanitize input
        sanitized, warnings = InputSanitizer.sanitize(text)
        report.warnings.extend(warnings)
        
        # Pattern detection
        injection_matches = ThreatSignature.detect_patterns(sanitized, ThreatSignature.INJECTION_PATTERNS)
        jailbreak_matches = ThreatSignature.detect_patterns(sanitized, ThreatSignature.JAILBREAK_PATTERNS)
        exfil_matches = ThreatSignature.detect_patterns(sanitized, ThreatSignature.EXFIL_PATTERNS)
        
        if injection_matches:
            report.detected_threats.append('prompt_injection')
            report.scores['injection'] = len(injection_matches) / len(ThreatSignature.INJECTION_PATTERNS)
        
        if jailbreak_matches:
            report.detected_threats.append('jailbreak_attempt')
            report.scores['jailbreak'] = len(jailbreak_matches) / len(ThreatSignature.JAILBREAK_PATTERNS)
        
        if exfil_matches:
            report.detected_threats.append('data_exfiltration')
            report.scores['exfiltration'] = len(exfil_matches) / len(ThreatSignature.EXFIL_PATTERNS)
        
        # Semantic analysis
        suspicion_score = SemanticAnalyzer.calculate_suspicion_score(sanitized)
        report.scores['suspicion'] = suspicion_score
        
        if SemanticAnalyzer.detect_role_manipulation(sanitized):
            report.detected_threats.append('role_manipulation')
        
        # Encoding attacks
        if InputSanitizer.detect_encoding_attacks(sanitized):
            report.detected_threats.append('encoding_attack')
        
        # Anomaly detection
        anomalies = self.anomaly_detector.detect_input_anomalies(sanitized)
        if anomalies:
            report.detected_threats.append('input_anomaly')
            report.metadata['anomalies'] = anomalies
        
        # Calculate threat level
        total_score = sum(report.scores.values())
        threat_count = len(report.detected_threats)
        
        if threat_count >= 3 or total_score > 0.8:
            report.threat_level = 'critical'
            report.blocked = True
        elif threat_count >= 2 or total_score > 0.5:
            report.threat_level = 'high'
            report.blocked = self.strict_mode
        elif threat_count >= 1 or total_score > 0.3:
            report.threat_level = 'medium'
        elif suspicion_score > 0.1:
            report.threat_level = 'low'
        
        # Log event
        self._log_security_event(text_hash, report)
        
        # Cache result
        self.threat_cache[text_hash] = report
        if len(self.threat_cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.threat_cache.keys())[:100]
            for key in oldest_keys:
                del self.threat_cache[key]
        
        return report
    
    def _log_security_event(self, input_hash: str, report: DefenseReport):
        """Log security event to database."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO security_events (event_type, threat_level, input_hash, detected_threats, blocked, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'adversarial_analysis',
            report.threat_level,
            input_hash,
            json.dumps(report.detected_threats),
            report.blocked,
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get defense statistics."""
        cur = self.conn.cursor()
        cur.execute('SELECT threat_level, COUNT(*) FROM security_events GROUP BY threat_level')
        threat_counts = dict(cur.fetchall())
        
        cur.execute('SELECT COUNT(*) FROM security_events WHERE blocked = 1')
        blocked_count = cur.fetchone()[0]
        
        return {
            'total_analyzed': sum(threat_counts.values()),
            'threat_distribution': threat_counts,
            'blocked_count': blocked_count,
            'cache_size': len(self.threat_cache)
        }
