"""
Enhanced Security Manager
Features: HSM integration, certificate pinning, audit logging, GDPR/CCPA compliance, tamper detection
"""
import hashlib
import hmac
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import secrets
from datetime import datetime, timedelta


class AuditEventType(Enum):
    """Audit event types"""
    LOGIN = "login"
    LOGOUT = "logout"
    DEVICE_ACCESS = "device_access"
    RECOVERY_START = "recovery_start"
    RECOVERY_COMPLETE = "recovery_complete"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    PERMISSION_CHANGE = "permission_change"
    SECURITY_ALERT = "security_alert"


class ComplianceRegulation(Enum):
    """Compliance regulations"""
    GDPR = "gdpr"  # Europe
    CCPA = "ccpa"  # California
    HIPAA = "hipaa"  # Healthcare
    PCI_DSS = "pci_dss"  # Payment card


@dataclass
class AuditLog:
    """Audit log entry"""
    log_id: str
    timestamp: float
    event_type: AuditEventType
    user_id: str
    ip_address: Optional[str]
    device_id: Optional[str]
    action: str
    details: Dict[str, Any]
    success: bool
    risk_score: float = 0.0


@dataclass
class DataRetentionPolicy:
    """Data retention policy for compliance"""
    regulation: ComplianceRegulation
    telemetry_days: int
    logs_days: int
    recovery_history_days: int
    deleted_data_grace_period_days: int


@dataclass
class TamperEvent:
    """Tamper detection event"""
    event_id: str
    device_id: str
    timestamp: float
    tamper_type: str  # jailbreak, root, debugger, modified_binary
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]


class SecurityManager:
    """Manages security, compliance, and auditing"""
    
    def __init__(self):
        self.audit_logs: List[AuditLog] = []
        self.tamper_events: List[TamperEvent] = []
        self.retention_policies: Dict[ComplianceRegulation, DataRetentionPolicy] = {}
        self.pinned_certificates: Dict[str, str] = {}  # domain -> cert_hash
        
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default retention policies"""
        self.retention_policies[ComplianceRegulation.GDPR] = DataRetentionPolicy(
            regulation=ComplianceRegulation.GDPR,
            telemetry_days=90,
            logs_days=365,
            recovery_history_days=180,
            deleted_data_grace_period_days=30
        )
        
        self.retention_policies[ComplianceRegulation.CCPA] = DataRetentionPolicy(
            regulation=ComplianceRegulation.CCPA,
            telemetry_days=365,
            logs_days=730,
            recovery_history_days=365,
            deleted_data_grace_period_days=30
        )
    
    # ============ Audit Logging ============
    
    def log_event(self, event_type: AuditEventType, user_id: str, action: str, 
                  details: Dict, success: bool = True, ip_address: Optional[str] = None,
                  device_id: Optional[str] = None) -> AuditLog:
        """Log audit event"""
        log = AuditLog(
            log_id=f"log-{secrets.token_hex(8)}",
            timestamp=time.time(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            device_id=device_id,
            action=action,
            details=details,
            success=success,
            risk_score=self._calculate_risk_score(event_type, details)
        )
        
        self.audit_logs.append(log)
        
        # Alert on high-risk events
        if log.risk_score > 0.7:
            self._trigger_security_alert(log)
        
        return log
    
    def _calculate_risk_score(self, event_type: AuditEventType, details: Dict) -> float:
        """Calculate risk score for event (0.0 to 1.0)"""
        base_scores = {
            AuditEventType.LOGIN: 0.2,
            AuditEventType.DATA_EXPORT: 0.6,
            AuditEventType.DATA_DELETE: 0.7,
            AuditEventType.PERMISSION_CHANGE: 0.5,
            AuditEventType.SECURITY_ALERT: 0.9,
        }
        
        score = base_scores.get(event_type, 0.1)
        
        # Increase score for suspicious patterns
        if details.get("failed_attempts", 0) > 3:
            score += 0.3
        if details.get("unusual_location", False):
            score += 0.2
        if details.get("unusual_time", False):
            score += 0.1
        
        return min(score, 1.0)
    
    def _trigger_security_alert(self, log: AuditLog):
        """Trigger security alert for high-risk events"""
        print(f"⚠️  SECURITY ALERT: {log.event_type.value} by {log.user_id}")
        print(f"   Risk Score: {log.risk_score:.2f}")
        print(f"   Details: {log.details}")
        # In production: send to SIEM, alert admins, etc.
    
    def get_audit_logs(self, user_id: Optional[str] = None, 
                       event_type: Optional[AuditEventType] = None,
                       since: Optional[float] = None) -> List[AuditLog]:
        """Retrieve audit logs with filters"""
        logs = self.audit_logs
        
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        if event_type:
            logs = [l for l in logs if l.event_type == event_type]
        if since:
            logs = [l for l in logs if l.timestamp >= since]
        
        return logs
    
    # ============ Certificate Pinning ============
    
    def pin_certificate(self, domain: str, cert_hash: str):
        """Pin SSL certificate for domain"""
        self.pinned_certificates[domain] = cert_hash
    
    def verify_certificate(self, domain: str, cert_hash: str) -> bool:
        """Verify certificate against pinned hash"""
        if domain not in self.pinned_certificates:
            return True  # No pin set
        
        expected = self.pinned_certificates[domain]
        if cert_hash != expected:
            self.log_event(
                AuditEventType.SECURITY_ALERT,
                "system",
                "certificate_mismatch",
                {"domain": domain, "expected": expected, "received": cert_hash},
                success=False
            )
            return False
        
        return True
    
    # ============ Tamper Detection ============
    
    def detect_tamper(self, device_id: str, checks: Dict[str, bool]) -> Optional[TamperEvent]:
        """Detect device tampering"""
        tamper_detected = False
        tamper_type = []
        
        if checks.get("is_jailbroken", False):
            tamper_detected = True
            tamper_type.append("jailbreak")
        
        if checks.get("is_rooted", False):
            tamper_detected = True
            tamper_type.append("root")
        
        if checks.get("debugger_attached", False):
            tamper_detected = True
            tamper_type.append("debugger")
        
        if checks.get("binary_modified", False):
            tamper_detected = True
            tamper_type.append("modified_binary")
        
        if not tamper_detected:
            return None
        
        # Determine severity
        severity = "critical" if len(tamper_type) > 1 else "high"
        
        event = TamperEvent(
            event_id=f"tamper-{secrets.token_hex(8)}",
            device_id=device_id,
            timestamp=time.time(),
            tamper_type=", ".join(tamper_type),
            severity=severity,
            details=checks
        )
        
        self.tamper_events.append(event)
        
        # Log security alert
        self.log_event(
            AuditEventType.SECURITY_ALERT,
            "system",
            "tamper_detected",
            {"device_id": device_id, "tamper_type": tamper_type, "severity": severity},
            success=False
        )
        
        return event
    
    # ============ GDPR/CCPA Compliance ============
    
    def request_data_export(self, user_id: str, regulation: ComplianceRegulation) -> Dict:
        """Handle user data export request (GDPR Article 20, CCPA)"""
        self.log_event(
            AuditEventType.DATA_EXPORT,
            user_id,
            "data_export_request",
            {"regulation": regulation.value}
        )
        
        # In production: collect all user data
        export_data = {
            "user_id": user_id,
            "exported_at": datetime.now().isoformat(),
            "regulation": regulation.value,
            "data": {
                "personal_info": "...",
                "devices": "...",
                "telemetry": "...",
                "recovery_history": "..."
            }
        }
        
        return export_data
    
    def request_data_deletion(self, user_id: str, regulation: ComplianceRegulation) -> str:
        """Handle right to be forgotten (GDPR Article 17, CCPA)"""
        policy = self.retention_policies.get(regulation)
        if not policy:
            raise ValueError(f"No policy for {regulation.value}")
        
        deletion_date = time.time() + (policy.deleted_data_grace_period_days * 86400)
        
        self.log_event(
            AuditEventType.DATA_DELETE,
            user_id,
            "data_deletion_request",
            {
                "regulation": regulation.value,
                "scheduled_deletion": deletion_date,
                "grace_period_days": policy.deleted_data_grace_period_days
            }
        )
        
        # In production: mark user for deletion, schedule cleanup
        return f"deletion-request-{secrets.token_hex(8)}"
    
    def cleanup_expired_data(self, regulation: ComplianceRegulation):
        """Clean up data exceeding retention period"""
        policy = self.retention_policies.get(regulation)
        if not policy:
            return
        
        now = time.time()
        
        # Clean audit logs
        cutoff_logs = now - (policy.logs_days * 86400)
        self.audit_logs = [l for l in self.audit_logs if l.timestamp >= cutoff_logs]
        
        # In production: clean telemetry, recovery history, etc.
        print(f"Cleaned data per {regulation.value} retention policy")
    
    def get_consent_status(self, user_id: str) -> Dict:
        """Get user consent status for compliance"""
        # In production: track granular consent
        return {
            "user_id": user_id,
            "consents": {
                "location_tracking": True,
                "data_processing": True,
                "marketing": False,
                "analytics": True
            },
            "last_updated": datetime.now().isoformat()
        }
    
    # ============ HSM Integration (Mock) ============
    
    def hsm_encrypt(self, data: bytes, key_id: str) -> bytes:
        """Encrypt data using HSM (mock)"""
        # In production: integrate with AWS CloudHSM, Azure Key Vault, etc.
        # For now, use standard encryption
        key = self._derive_key(key_id)
        return self._aes_encrypt(data, key)
    
    def hsm_decrypt(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data using HSM (mock)"""
        key = self._derive_key(key_id)
        return self._aes_decrypt(encrypted_data, key)
    
    def _derive_key(self, key_id: str) -> bytes:
        """Derive encryption key from key_id"""
        # Mock implementation
        return hashlib.sha256(f"saraphina-key-{key_id}".encode()).digest()
    
    def _aes_encrypt(self, data: bytes, key: bytes) -> bytes:
        """AES encryption (simplified)"""
        # In production: use cryptography library with proper AES-GCM
        return data  # Mock
    
    def _aes_decrypt(self, data: bytes, key: bytes) -> bytes:
        """AES decryption (simplified)"""
        return data  # Mock
    
    # ============ Security Monitoring ============
    
    def get_security_dashboard(self) -> Dict:
        """Get security overview dashboard"""
        now = time.time()
        last_24h = now - 86400
        
        recent_logs = [l for l in self.audit_logs if l.timestamp >= last_24h]
        high_risk_logs = [l for l in recent_logs if l.risk_score > 0.7]
        failed_logins = [l for l in recent_logs if l.event_type == AuditEventType.LOGIN and not l.success]
        
        return {
            "total_events_24h": len(recent_logs),
            "high_risk_events_24h": len(high_risk_logs),
            "failed_logins_24h": len(failed_logins),
            "tamper_events_total": len(self.tamper_events),
            "recent_alerts": [
                {
                    "timestamp": l.timestamp,
                    "type": l.event_type.value,
                    "user": l.user_id,
                    "risk_score": l.risk_score
                }
                for l in high_risk_logs[:10]
            ]
        }
