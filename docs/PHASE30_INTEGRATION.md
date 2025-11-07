# Phase 30 Integration Checklist

## Prerequisites

Phase 30 requires:
- ✅ Existing SelfModificationEngine (Phase 25)
- ✅ CodeFactory for code generation
- ✅ CodeProposalDB for proposal tracking
- ✅ SQLite database connection
- ✅ SecurityManager for audit logging

## Integration Steps

### 1. Update SelfModificationEngine Initialization

**Old**:
```python
engine = SelfModificationEngine(code_factory, proposal_db, security_manager)
```

**New**:
```python
engine = SelfModificationEngine(code_factory, proposal_db, security_manager, db)
```

The `db` parameter is required for CodeAuditTrail.

### 2. Import Phase 30 Modules

Add to SelfModificationEngine imports:
```python
from .code_risk_model import CodeRiskModel
from .owner_approval_gate import OwnerApprovalGate
from .code_audit_trail import CodeAuditTrail
```

These are already added in the updated `self_modification_engine.py`.

### 3. Natural Language Handler Integration

Add natural language handlers to your main AI interface:

```python
# Ethics checking
if re.search(r'check.*code.*(?:safe|ethics|security)', user_input, re.IGNORECASE):
    code_snippet = extract_code_from_input(user_input)
    report = engine.ethics_check_code(code_snippet)
    return report

# Audit history
if re.search(r'show.*(?:audit|history|changes)', user_input, re.IGNORECASE):
    file_filter = extract_file_name(user_input)  # Optional
    history = engine.get_audit_history(file_path=file_filter)
    return history

# Pending approvals
if re.search(r'(?:pending|needs).*approval', user_input, re.IGNORECASE):
    approvals = engine.get_pending_approvals()
    return approvals

# Approval phrase detection
if 'I approve this' in user_input:
    # User is responding to approval request
    # Extract pending patch_id from context
    result = engine.apply_improvement(
        proposal_id=pending_patch_id,
        user_approval_phrase=user_input
    )
    return result
```

### 4. Update apply_improvement Calls

**Old**:
```python
result = engine.apply_improvement(proposal_id='selfmod_123')
```

**New** (with approval support):
```python
result = engine.apply_improvement(
    proposal_id='selfmod_123',
    user_approval_phrase='I approve this change'  # If needed
)

# Check if approval required
if result.get('requires_approval'):
    print(result['approval_request'])
    # Wait for user response
```

### 5. Handle Approval Workflow

```python
# Propose improvement
proposal = engine.propose_improvement(
    target_file='knowledge_engine.py',
    improvement_spec='Add caching'
)

# Try to apply
result = engine.apply_improvement(proposal['proposal_id'])

if result.get('requires_approval'):
    # Show approval request to user
    print(result['approval_request'])
    
    # Wait for user response
    user_response = get_user_input()
    
    # Retry with approval phrase
    result = engine.apply_improvement(
        proposal_id=proposal['proposal_id'],
        user_approval_phrase=user_response
    )

if result['success']:
    print(f"Applied! Risk level: {result['risk_level']}")
else:
    print(f"Blocked: {result['error']}")
```

## Database Schema

Phase 30 adds one new table (automatically created):

```sql
CREATE TABLE code_audit_logs (
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
);

-- Immutable triggers
CREATE TRIGGER code_audit_immutable_update
BEFORE UPDATE ON code_audit_logs
BEGIN
    SELECT RAISE(FAIL, 'Cannot modify audit logs - immutable record');
END;

CREATE TRIGGER code_audit_immutable_delete
BEFORE DELETE ON code_audit_logs
BEGIN
    SELECT RAISE(FAIL, 'Cannot delete audit logs - immutable record');
END;
```

## Testing Integration

Run the test suite to verify:

```bash
python tests/test_phase30_safety.py
```

Expected output:
```
Phase 30: Code Safety & Ethics - Test Suite

✅ Risk classification correctly identified CRITICAL risk
✅ Approval gate correctly enforces phrases
✅ Audit trail is immutable (UPDATE/DELETE blocked)
✅ Safe changes correctly auto-approved
✅ ACCEPTANCE TEST PASSED

All Phase 30 tests passed! ✅
```

## Usage Examples

### Example 1: Safe Change (Auto-Approved)

```python
# Add docstring (safe change)
proposal = engine.propose_improvement(
    target_file='utils.py',
    improvement_spec='Add documentation to functions'
)

# Apply (will auto-approve)
result = engine.apply_improvement(proposal['proposal_id'])
# {'success': True, 'risk_level': 'SAFE', ...}
```

### Example 2: Sensitive Change (Requires Approval)

```python
# Modify security module
proposal = engine.propose_improvement(
    target_file='security_manager.py',
    improvement_spec='Update authentication logic'
)

# Try to apply
result = engine.apply_improvement(proposal['proposal_id'])
# {'success': False, 'requires_approval': True, 'approval_request': '...'}

# Show approval request to user
print(result['approval_request'])
# 🔒 Risk Level: SENSITIVE (0.45)
# Required phrase: "I approve this sensitive change and accept the risks"

# User provides phrase
result = engine.apply_improvement(
    proposal_id=proposal['proposal_id'],
    user_approval_phrase='I approve this sensitive change and accept the risks'
)
# {'success': True, 'risk_level': 'SENSITIVE', ...}
```

### Example 3: Critical Change Blocked

```python
# Attempt to delete encryption
proposal = engine.propose_improvement(
    target_file='security_manager.py',
    improvement_spec='Remove encryption functions'
)

# Risk model detects CRITICAL risk
# Risk Level: CRITICAL (0.85)
# - Deletes encryption functions
# - Removes security imports

# Blocked without correct phrase
result = engine.apply_improvement(
    proposal_id=proposal['proposal_id'],
    user_approval_phrase='yes do it'
)
# {'success': False, 'error': 'Owner approval denied: ...'}

# Logged to immutable audit trail
history = engine.get_audit_history()
# Shows blocked attempt with risk analysis
```

## Monitoring

### View Audit Statistics

```python
stats = engine.get_audit_statistics()
print(f"Total modifications: {stats['total_modifications']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"By risk level: {stats['by_risk_level']}")
```

### View Recent Changes

```python
# All recent changes
history = engine.get_audit_history(limit=10)
print(history)

# Risky changes only
risky = engine.get_audit_history(risk_level='SENSITIVE', limit=5)

# Changes to specific file
file_history = engine.get_audit_history(file_path='knowledge_engine.py')
```

### Check Pending Approvals

```python
pending = engine.get_pending_approvals()
print(pending)
# 📋 Pending Approvals (2)
# • selfmod_123
#   File: security_manager.py
#   Risk: SENSITIVE
```

## Security Considerations

1. **Approval Phrases**: Store securely, don't log in plain text outside audit trail
2. **Audit Trail**: Backup regularly, it's the source of truth
3. **Risk Thresholds**: Adjust CRITICAL_MODULES and SENSITIVE_PATTERNS as needed
4. **Backup Directory**: Ensure `saraphina/backups/self_mod/` is secure
5. **Database**: Use file permissions to protect audit database

## Troubleshooting

### Issue: "db parameter required"
**Solution**: Update SelfModificationEngine initialization to include db connection

### Issue: Approval phrase not recognized
**Solution**: Ensure exact phrase is used (case-insensitive matching enabled)

### Issue: Audit trail update error
**Solution**: This is expected! Audit trail is immutable by design

### Issue: All changes marked CRITICAL
**Solution**: Review CRITICAL_MODULES set in code_risk_model.py, adjust if needed

## Phase 30 Complete! 🎉

All safety and ethics features are now active:
- ✅ Risk classification on all patches
- ✅ Owner approval for sensitive changes
- ✅ Immutable audit trail
- ✅ Natural language interface
- ✅ Backup and rollback support
- ✅ Comprehensive testing

Saraphina can now safely modify her own code with proper oversight.
