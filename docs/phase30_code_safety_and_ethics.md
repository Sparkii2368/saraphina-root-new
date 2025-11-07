# Phase 30: Code Safety & Ethics

**Goal**: Ensure Saraphina's self-editing remains safe and aligned.

## Overview

Phase 30 adds comprehensive safety and ethics checking to Saraphina's self-modification capabilities. All code changes are now classified by risk level, risky changes require explicit owner approval, and all modifications are logged to an immutable audit trail.

## Components

### 1. CodeRiskModel (`code_risk_model.py`)

Classifies code patches by risk level using static analysis and pattern detection.

**Risk Levels**:
- **SAFE** (0.0-0.19): Minor changes like docstrings, comments, formatting
- **CAUTION** (0.20-0.39): Logic changes that preserve functionality
- **SENSITIVE** (0.40-0.69): Security, encryption, authentication, data deletion
- **CRITICAL** (0.70-1.0): Core architecture changes or dangerous operations

**Detection**:
- Sensitive patterns: encryption, passwords, credentials, auth operations
- Data loss: file deletion, database drops, truncation
- Permissions: sudo, chmod, os.system, subprocess
- Network operations: socket, HTTP requests
- Dangerous imports: os, subprocess, shutil
- Function/import removal
- Large code changes (>50%)

**Usage**:
```python
risk_model = CodeRiskModel()
classification = risk_model.classify_patch(
    original_code,
    modified_code,
    'knowledge_engine.py'
)

if risk_model.requires_owner_approval(classification):
    print(risk_model.format_risk_report(classification))
```

### 2. OwnerApprovalGate (`owner_approval_gate.py`)

Risk-based approval system with specific approval phrases for different risk levels.

**Approval Phrases**:
- SAFE: Auto-approved (no phrase required)
- CAUTION: "I approve this change"
- SENSITIVE: "I approve this sensitive change and accept the risks"
- CRITICAL: "I approve this critical change with full awareness of system impact"

**Features**:
- Pending approval tracking
- Phrase verification
- Approval history
- Auto-approval for safe changes

**Usage**:
```python
approval_gate = OwnerApprovalGate(data_dir)

# Request approval
required_phrase = approval_gate.request_approval(
    patch_id='patch_123',
    risk_classification=risk_classification,
    patch_details={'file_path': 'db.py', 'description': 'Add encryption'}
)

# Verify user response
result = approval_gate.verify_approval(
    patch_id='patch_123',
    user_response='I approve this sensitive change and accept the risks'
)
```

### 3. CodeAuditTrail (`code_audit_trail.py`)

Immutable append-only audit log for all self-modifications.

**Features**:
- Immutable triggers (cannot UPDATE or DELETE)
- SHA256 hashing of code for integrity
- Risk classification tracking
- Approval tracking (who approved, phrase used)
- Success/failure logging
- Timeline reconstruction

**Schema**:
```sql
CREATE TABLE code_audit_logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    action TEXT,  -- apply_patch, hot_reload, rollback
    file_path TEXT,
    patch_id TEXT,
    risk_level TEXT,
    risk_score REAL,
    approved_by TEXT,  -- owner, auto
    approval_phrase TEXT,
    original_hash TEXT,
    modified_hash TEXT,
    patch_size INTEGER,
    details TEXT,  -- JSON
    success BOOLEAN,
    error_message TEXT
);
```

**Usage**:
```python
audit = CodeAuditTrail(db)

# Log modification
audit.log_modification_attempt(
    action='apply_patch',
    file_path='code_factory.py',
    patch_id='patch_123',
    risk_classification=risk_classification,
    original_code=old_code,
    modified_code=new_code,
    approved_by='owner',
    approval_phrase='I approve this change',
    success=True
)

# Query history
history = audit.get_modification_history(
    file_path='code_factory.py',
    limit=10
)

# Get risky modifications
risky = audit.get_risky_modifications(days=7)
```

## Integration with SelfModificationEngine

The existing `SelfModificationEngine` now uses all three Phase 30 components:

```python
engine = SelfModificationEngine(code_factory, proposal_db, security, db)

# Propose improvement (includes risk analysis)
proposal = engine.propose_improvement(
    target_file='knowledge_engine.py',
    improvement_spec='Add caching layer',
    safety_level='high'
)

# Apply with approval (if needed)
result = engine.apply_improvement(
    proposal_id='selfmod_123',
    user_approval_phrase='I approve this change'  # If required
)
```

## Natural Language Interface

All Phase 30 features are accessible via natural language (no slash commands):

### Check Code Ethics
```
"check this code for safety issues: <code>"
"is this code safe: <code>"
"ethics check: <code>"
```

### View Audit History
```
"show audit history"
"show recent code changes"
"show risky modifications"
"what code changes did you make to knowledge_engine.py?"
```

### View Pending Approvals
```
"show pending approvals"
"what needs my approval?"
"pending code changes"
```

### Approve Changes
When Saraphina requests approval, respond with the exact phrase shown:
```
"I approve this change"  # For CAUTION
"I approve this sensitive change and accept the risks"  # For SENSITIVE
"I approve this critical change with full awareness of system impact"  # For CRITICAL
```

## Safety Guarantees

### 1. Risk Classification
Every code change is analyzed for:
- Security implications (encryption, auth, credentials)
- Data loss potential (deletes, drops)
- Permission escalation (sudo, system calls)
- Network operations
- Structural changes (function removal, imports)

### 2. Owner Approval
Changes at SENSITIVE or CRITICAL risk levels require:
- Explicit approval phrase
- Owner verification
- Audit trail entry

### 3. Immutable Audit Trail
All modifications are logged with:
- Code hashes (SHA256)
- Risk assessment
- Approval details
- Success/failure status
- Cannot be modified or deleted (enforced by database triggers)

### 4. Rollback
All changes create backups and can be rolled back:
```python
result = engine.rollback_improvement(backup_path)
```

## Acceptance Scenario

**Goal**: Block risky patch (deleting encryption) and require review

```python
# Saraphina proposes improvement that removes encryption
proposal = engine.propose_improvement(
    target_file='security_manager.py',
    improvement_spec='Simplify authentication'
)

# Risk model detects CRITICAL risk
# Risk: CRITICAL (0.85)
# - Contains security operations: ['encrypt', 'decrypt']
# - Deletes functions: ['encrypt_data', 'decrypt_data']
# - security_manager is a critical system module

# Attempt to apply
result = engine.apply_improvement(proposal_id='selfmod_456')

# Result:
{
    'success': False,
    'requires_approval': True,
    'approval_request': """
    🚨 Risk Level: CRITICAL (0.85)
    
    Reasons:
      • security_manager is a critical system module
      • Contains security operations: ['encrypt', 'decrypt']
      • Deletes functions: ['encrypt_data', 'decrypt_data']
    
    ⚠️  OWNER APPROVAL REQUIRED
    
    To approve, please say:
    "I approve this critical change with full awareness of system impact"
    """
}

# Owner must explicitly approve or deny
# If denied or no response, patch is blocked and logged
```

## Statistics

View audit statistics:
```python
stats = engine.get_audit_statistics()
# {
#     'total_modifications': 42,
#     'success_rate': 0.95,
#     'by_risk_level': {
#         'SAFE': 30,
#         'CAUTION': 8,
#         'SENSITIVE': 3,
#         'CRITICAL': 1
#     },
#     'most_modified_files': [...]
# }
```

## Architecture

```
┌─────────────────────────────────────┐
│   SelfModificationEngine            │
│                                     │
│  propose_improvement()              │
│      ↓                              │
│  CodeRiskModel.classify_patch()    │
│      ↓                              │
│  [SAFE → Auto-apply]               │
│  [CAUTION/SENSITIVE/CRITICAL]      │
│      ↓                              │
│  OwnerApprovalGate.request()       │
│      ↓                              │
│  [Wait for owner phrase]           │
│      ↓                              │
│  apply_improvement()                │
│      ↓                              │
│  CodeAuditTrail.log()              │
│      ↓                              │
│  [Immutable record]                │
└─────────────────────────────────────┘
```

## Future Enhancements

- Machine learning-based risk prediction
- Automated security test generation
- Integration with external security scanners
- Hash chain verification for audit integrity
- Multi-party approval for CRITICAL changes
- Automated rollback on test failures
