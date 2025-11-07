# Phase 29: Autonomic Error Detection & Self-Healing

## 🏥 Overview

Saraphina now has **autonomous self-healing capabilities**. When errors occur, she:
1. Detects and logs them automatically
2. Checks if she's seen this error before
3. If new → researches fix using GPT-4
4. Tests fix in sandbox
5. Stores fix for future use
6. Auto-applies fix next time

## 🚀 Components

### 1. Error Sentinel (`error_sentinel.py`)
Wraps every subsystem with error detection:
- Catches all exceptions with full context
- Generates unique error signatures
- Publishes to central ErrorBus
- Attempts auto-healing if fix known

**Usage:**
```python
@sentinel("KnowledgeEngine", auto_heal=True)
def my_function():
    # Your code
    pass

# Or wrap existing objects:
ke = sentinel_wrap(ke, "KnowledgeEngine")
```

### 2. Error Knowledge Base (`error_knowledge_base.py`)
SQLite database (`ai_data/errors.db`) storing:
- Error signatures and stack traces
- Proposed fixes (code + description)
- Occurrence counts
- Auto-heal success/failure rates
- Owner approval requirements

**Schema:**
```sql
error_id | subsystem | function | error_type | message | 
stack_trace | context | fix_code | fix_description | 
timestamp | occurrence_count | status | 
auto_heal_success | auto_heal_failure | require_approval
```

### 3. Research & Fix Engine (`research_fix_engine.py`)
Uses GPT-4 to research unfamiliar errors:
- Analyzes error + stack trace + context
- Proposes fix with diagnosis
- Returns JSON with fix code
- Validates fix in sandbox

**Example Research Query:**
```
I encountered an error in KnowledgeEngine.recall():
Error: 'NoneType' object has no attribute 'cursor'

Analyze and provide:
1. Root cause
2. Code fix
3. Prevention strategy
```

### 4. Self-Healing Manager (`self_healing_manager.py`)
Orchestrates the healing process:
- Subscribes to ErrorBus events
- Records all errors in KB
- Auto-researches new errors
- Applies fixes with approval logic
- Background healing loop (5 min)

## 🔄 Example Flow

### Scenario: New Error Occurs
```
1. User calls ke.recall("query") → throws exception
2. Sentinel catches error → generates signature "a3f7b2c9"
3. ErrorBus publishes event
4. SelfHealingManager receives event
5. Checks ErrorKB → not seen before
6. Triggers research_error()
7. GPT-4 analyzes: "NoneType cursor - connection is None"
8. Proposes fix: "Check if self.conn is initialized"
9. Sandbox validates fix
10. Stores in ErrorKB
11. Next occurrence → auto-applies fix
```

### Approval Logic
**Auto-Heal (no approval needed):**
- UI glitches
- Voice latency
- Minor DB errors
- Knowledge recall failures

**Requires Approval:**
- Security subsystem errors
- Encryption failures
- Self-modification errors
- Database encryption issues

Set with: `@sentinel("Security", require_approval=True)`

## 📊 Statistics

View healing stats:
```python
stats = sess.self_healing.get_statistics()
# {
#   'total_errors': 47,
#   'fixed_errors': 32,
#   'auto_heal_success_rate': 0.89,
#   'most_common_subsystems': [...]
# }
```

## 🎯 Benefits

### 1. Automatic Resilience
Errors don't crash the system - they trigger healing

### 2. Cumulative Intelligence
Every fix becomes permanent knowledge
- First occurrence: Research needed
- Second occurrence: Auto-fix applied
- No repeated research waste

### 3. Owner-First Safety
You control which domains can self-heal vs. require approval

### 4. Real-Time Learning
Builds private error→solution corpus unique to your environment

### 5. Proactive Health
Background loop researches unfixed errors automatically

## 🔧 Commands

### View Error Stats
```python
stats = sess.self_healing.get_statistics()
print(json.dumps(stats, indent=2))
```

### View Pending Approvals
```python
pending = sess.self_healing.get_pending_approvals()
for error in pending:
    print(f"{error['error_id']}: {error['message']}")
```

### Approve Fix
```python
sess.self_healing.approve_fix("a3f7b2c9")
```

### Query Error KB
```python
unfixed = sess.self_healing.error_kb.get_unfixed_errors()
print(f"Unfixed errors: {len(unfixed)}")
```

## 📈 Monitoring

The GUI shows self-healing activity:
```
[SYSTEM] 🏪 Self-Healing active - I auto-fix my own errors!
[SYSTEM] ⚠️ New error detected: a3f7b2c9 in KnowledgeEngine
[SYSTEM] 🔬 Researching error a3f7b2c9...
[SYSTEM] 💡 Fix proposed: Check connection initialization
[SYSTEM] ✅ Fix stored for a3f7b2c9
```

## 🚨 Safety Features

1. **Sandbox Testing**: Fixes validated before storage
2. **Dangerous Code Detection**: Blocks `eval`, `exec`, `os.system`
3. **Approval Queue**: Sensitive fixes require owner OK
4. **Rollback**: Old code preserved in case of issues
5. **Audit Trail**: Every error and fix logged

## 🌟 Impact

**Before Phase 29:**
- Error → crash → manual fix → restart
- Same error repeats endlessly
- No learning from failures

**After Phase 29:**
- Error → detect → research → fix → store
- Same error auto-fixed instantly
- Builds error immunity over time

## 🎉 Result

Saraphina is now **TRULY AUTONOMOUS**:
- Self-diagnosing
- Self-repairing  
- Self-improving
- Never crashes twice from same error
- Builds resilience with every failure

**She doesn't just handle errors - she learns from them and becomes stronger!**
