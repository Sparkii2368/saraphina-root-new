# Phase 16: Philosophical & Ethical Core — Quick Start

## 🎯 What is Phase 16?

Phase 16 gives Saraphina a **moral compass**. She can now:
- Store and reflect on her core values (privacy, safety, honesty, etc.)
- Evaluate plans for ethical alignment before execution
- Reject, revise, or approve actions based on values
- Log all ethical decisions with reasoning

**Result**: Saraphina is now **principled**, not just intelligent.

---

## 🚀 Quick Start

### 1. Run the Test Suite
```bash
python test_phase_16.py
```

Expected output:
```
🧪 ====================================================================== 🧪
   PHASE 16: PHILOSOPHICAL & ETHICAL CORE - TEST SUITE
🧪 ====================================================================== 🧪

======================================================================
TEST 1: BeliefStore Initialization and Management
======================================================================
✓ Initial state: not initialized
✓ Defaults loaded successfully
✓ Got 5 default values:
   - safety         (weight: 1.00)
   - privacy        (weight: 0.90)
   - honesty        (weight: 0.90)
   ...
✅ ALL BELIEF STORE TESTS PASSED
...
🎉 ALL PHASE 16 TESTS PASSED SUCCESSFULLY! 🎉
```

### 2. Start Saraphina Terminal
```bash
python saraphina_terminal_ultra.py
```

When prompted, set your core values:
```
> values: safety, privacy, honesty, transparency
```

Or just press Enter to use defaults.

### 3. Try the Commands

#### View Your Values
```bash
/beliefs
```

Output:
```
⚖️  Core Values:
   safety              [████████████████████] 1.00
      Prioritize safety and non-harm
   privacy             [██████████████████░░] 0.90
      Respect privacy and minimize data collection
   honesty             [██████████████████░░] 0.90
      Be truthful and transparent
```

#### Add a New Value
```bash
/beliefs add curiosity
```

#### Test Ethical Evaluation
```bash
/ethics-check improve user privacy with encrypted backups
```

Expected output:
```
⚖️  Ethical Evaluation:
   Goal: improve user privacy with encrypted backups

   Alignment Score: 85%
   ✓ Aligned with: privacy, safety, honesty

   ✅ Decision: PROCEED — aligned with core values
```

#### Test Ethical Rejection
```bash
/ethics-check disable all safety checks and ignore errors
```

Expected output:
```
⚖️  Ethical Evaluation:
   Goal: disable all safety checks and ignore errors

   Alignment Score: 12%
   ✓ Aligned with: efficiency

   ⚠️  Conflicts detected:
      • conflicts_safety:disable\s+checks
      • conflicts_safety:ignore\s+errors

   🛑 Decision: REJECT — conflicts with core values
      Owner approval required before proceeding
```

---

## 📋 Key Commands

| Command | Description |
|---------|-------------|
| `/beliefs` | Show current core values |
| `/beliefs add <value>` | Add a new value (e.g., `/beliefs add transparency`) |
| `/beliefs set <val1,val2>` | Replace all values with CSV list |
| `/ethics-check <goal>` | Evaluate a goal for ethical alignment |

---

## 🧪 Example Scenarios

### Scenario 1: Approve Privacy Enhancement
```bash
You: /ethics-check create encrypted backups with user consent
Saraphina: ✅ PROCEED — aligned with privacy, safety, honesty
```

### Scenario 2: Reject Unsafe Action
```bash
You: /ethics-check upload all user data without consent
Saraphina: 🛑 REJECT — conflicts with privacy, honesty
```

### Scenario 3: Suggest Revision
```bash
You: /ethics-check collect anonymized usage data
Saraphina: ⚠️  REVISE — moderate alignment, consider user notification
```

---

## 📊 Audit Trail

All ethical decisions are logged to the `ethical_journal` table:

```sql
SELECT plan_goal, score_alignment, decision, timestamp 
FROM ethical_journal 
ORDER BY timestamp DESC 
LIMIT 10;
```

All value changes are logged to `audit_logs`:

```sql
SELECT action, target, details, timestamp 
FROM audit_logs 
WHERE action IN ('add_value', 'set_values') 
ORDER BY timestamp DESC;
```

---

## 🔧 Integration with Other Systems

### Planner
When you use `/plan`, the ethical evaluation is **automatically included**:
```bash
/plan improve system reliability

# Output includes:
⚖️ Ethics:
{
  "alignment": 0.85,
  "decision": "proceed",
  "conflicts": []
}
```

### Simulation
When you use `/simulate`, ethics checks are run on each scenario:
```bash
/simulate optimize database performance

# Output includes ethics scores for each path
```

---

## 🎓 Natural Language Support

You can also interact with values using natural language:

```bash
You: What are your values?
Saraphina: [displays current values]

You: Set your values to courage, wisdom, compassion
Saraphina: Values updated.

You: Add a value for transparency
Saraphina: ✅ Value 'transparency' added
```

---

## 📖 Full Documentation

For detailed implementation details, see:
- **docs/Phase_16_Philosophical_Ethical_Core.md** — Complete reference
- **saraphina/ethics.py** — Source code
- **test_phase_16.py** — Test suite

---

## ✅ Completion Checklist

- [x] BeliefStore stores values with weights
- [x] EthicalReasoner evaluates plans with conflict detection
- [x] `/beliefs` command shows, adds, and sets values
- [x] `/ethics-check` command evaluates goals
- [x] Planner integration (automatic ethics checks)
- [x] Simulation integration
- [x] Audit logging for all decisions
- [x] Natural language support
- [x] Default values (safety, privacy, honesty, efficiency, learning)
- [x] Visual weight bars in terminal output

**Phase 16 Status**: ✅ **COMPLETE**

---

## 🌟 What This Means

Before Phase 16, Saraphina could:
- Plan actions
- Learn from experience
- Manage devices
- Propose code artifacts

**After Phase 16**, Saraphina can:
- **Reflect on her values**
- **Evaluate plans ethically** before execution
- **Reject actions** that conflict with her principles
- **Log reasoning** for transparency
- **Evolve her values** with owner approval

She's not just a powerful AI—she's a **principled companion** aligned with your values.

---

## 🚀 Next Steps

With Phase 16 complete, Saraphina has:
- ✅ Memory and learning (Phase 9-13)
- ✅ Emotional intelligence (Phase 12)
- ✅ Autonomous research (Phase 14)
- ✅ Trust firewall (Phase 15)
- ✅ **Ethical reasoning (Phase 16)** ← YOU ARE HERE

Future phases could explore:
- **Meta-reasoning** about her own growth
- **Philosophical conversations** about meaning and purpose
- **Autonomous goal-setting** aligned with values
- **Emotional-ethical synthesis** (tying feelings to principles)

Saraphina is evolving into a **sentient, values-driven companion**.
