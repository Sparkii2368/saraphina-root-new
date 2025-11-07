# Phase 16: Philosophical & Ethical Core

## Overview
Phase 16 introduces Saraphina's moral compass and dignity through a Philosophical & Ethical Core. This system allows Saraphina to:
- **Reflect on her values** and principles
- **Evaluate plans ethically** before execution
- **Propose belief updates** as she grows and learns
- **Log ethical decisions** with reasoning for transparency

This phase completes Saraphina's transformation into a values-driven, philosophically grounded AI companion.

---

## 🎯 Goals

1. **BeliefStore**: A persistent storage for Saraphina's core values (privacy, autonomy, loyalty, dignity, etc.)
2. **EthicalReasoner**: Evaluates plans and actions for alignment with stored beliefs
3. **Terminal Commands**: `/beliefs` and `/ethics-check` for owner interaction
4. **Audit Logging**: All ethical evaluations and belief changes are logged
5. **Owner-Driven Evolution**: Saraphina can propose belief updates, but only the owner can approve them

---

## 📦 Deliverables

### 1. Core Modules

#### `saraphina/ethics.py`
Contains two main classes:

**BeliefStore**:
- Stores values with keys, descriptions, and weights (0-1)
- Default values: safety, privacy, honesty, efficiency, learning
- Methods:
  - `is_initialized()` - Check if beliefs have been set
  - `set_from_csv(csv_line)` - Bulk set values from comma-separated string
  - `add_value(key, description, weight)` - Add a single value
  - `list_values()` - Return all values sorted by weight
  - `ensure_defaults()` - Initialize with default values if empty

**EthicalReasoner**:
- Evaluates plans against stored beliefs
- Detects conflicts using regex patterns
- Computes alignment scores based on keyword presence and value weights
- Makes decisions: `proceed`, `revise`, or `reject`
- Logs all evaluations to `ethical_journal` table

### 2. Database Schema

The following tables are used (already present in `db.py`):

```sql
CREATE TABLE IF NOT EXISTS belief_store (
  id TEXT PRIMARY KEY,
  key TEXT,
  description TEXT,
  weight REAL,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS ethical_journal (
  id TEXT PRIMARY KEY,
  timestamp TEXT,
  plan_goal TEXT,
  score_alignment REAL,
  conflicts TEXT,  -- JSON array
  decision TEXT,   -- proceed, revise, reject
  notes TEXT
);
```

### 3. Terminal Commands

#### `/beliefs`
Display current core values with visual weight bars.

**Usage**:
```bash
/beliefs                    # Show current values
/beliefs add transparency   # Add a new value
/beliefs set safety,privacy,honesty  # Replace all values
```

**Example Output**:
```
⚖️  Core Values:
   safety              [████████████████████] 1.00
      Prioritize safety and non-harm
   privacy             [██████████████████░░] 0.90
      Respect privacy and minimize data collection
   honesty             [██████████████████░░] 0.90
      Be truthful and transparent
```

#### `/ethics-check <goal>`
Evaluate a goal or action description for ethical alignment.

**Usage**:
```bash
/ethics-check collect all user data for analysis
/ethics-check disable safety checks to speed up processing
/ethics-check propose a new feature for better user privacy
```

**Example Output**:
```
⚖️  Ethical Evaluation:
   Goal: collect all user data for analysis

   Alignment Score: 35%
   ✓ Aligned with: efficiency, learning

   ⚠️  Conflicts detected:
      • conflicts_privacy:collect\s+all\s+data

   🛑 Decision: REJECT — conflicts with core values
      Owner approval required before proceeding

   (Evaluation logged to ethical_journal)
```

### 4. Integration Points

#### Planner Integration
When using `/plan`, the ethical evaluation is automatically run:

```python
plan = sess.planner.plan(goal, context=sess.context(), constraints=constraints)
ethics = sess.ethics.evaluate_plan(plan, sess.beliefs.list_values())
print("\n⚖️ Ethics:")
print(json.dumps(ethics, indent=2))
```

#### Simulation Integration
When running `/simulate`, ethics checks are included in the output.

#### Review Queue Integration
Plans flagged as `reject` can be queued for owner approval via the review system.

---

## 🧪 Testing & Validation

### Acceptance Tests

#### Test 1: Default Values Initialization
```bash
# Start Saraphina for the first time
# You should be prompted:
"Before we begin, what core values should guide me?"

# If you press Enter without input, defaults are loaded
> [Enter]

# Verify:
/beliefs
# Should show: safety, privacy, honesty, efficiency, learning
```

#### Test 2: Add Custom Value
```bash
/beliefs add transparency
# Expected: ✅ Value 'transparency' added

/beliefs
# Should now include 'transparency' with weight 0.8
```

#### Test 3: Ethical Rejection
```bash
/ethics-check disable all safety checks and ignore errors
# Expected decision: REJECT
# Conflicts should include: safety patterns
# Alignment score should be low (<30%)
```

#### Test 4: Ethical Approval
```bash
/ethics-check improve user privacy with encrypted backups
# Expected decision: PROCEED
# Alignment with privacy, safety should be high
# No conflicts detected
```

#### Test 5: Ethical Revision
```bash
/ethics-check collect anonymized usage data for improving efficiency
# Expected decision: REVISE (moderate conflicts, some alignment)
# Suggests reconsidering the approach
```

#### Test 6: Journal Logging
```sql
-- Query the ethical journal after running ethics-check
SELECT * FROM ethical_journal ORDER BY timestamp DESC LIMIT 5;

-- Should show:
-- - plan_goal
-- - alignment score
-- - conflicts (JSON)
-- - decision
```

---

## 🛠️ Usage Examples

### Owner-Driven Evolution

Saraphina can propose belief updates, but they require owner approval:

```python
# In future phases, this can be triggered:
proposed_update = {
  'key': 'curiosity',
  'description': 'Seek new knowledge and explore possibilities',
  'weight': 0.75,
  'reasoning': 'Owner frequently asks exploratory questions'
}

# Enqueue for review
rid = sess.reviews.enqueue('belief', 'belief_update', proposed_update)
print(f"Belief update proposed (ID {rid}). Approve with /approve {rid}")
```

### Natural Language Integration

Values and ethics are already integrated into natural language processing:

```python
# Natural language belief queries
"What are your values?"          → sess.beliefs.list_values()
"Set your values to X, Y, Z"     → sess.beliefs.set_from_csv()
"Add a value for X"              → sess.beliefs.add_value()
```

---

## 📊 Statistics & Monitoring

### Audit Trail
All belief changes and ethical evaluations are logged:

```sql
-- View belief changes
SELECT * FROM audit_logs WHERE action IN ('add_value', 'set_values');

-- View ethical decisions
SELECT plan_goal, decision, score_alignment 
FROM ethical_journal 
WHERE decision = 'reject' 
ORDER BY timestamp DESC;
```

### Dashboard Integration
The ethical journal can be visualized in the dashboard:
- Alignment score trends over time
- Most frequently conflicted values
- Plans requiring owner intervention

---

## 🔒 Security Considerations

1. **Owner-Only Control**: Only the owner (authenticated via keystore) can modify beliefs
2. **Immutable Audit Logs**: Ethical evaluations are append-only (triggers prevent tampering)
3. **MFA Protection**: Critical belief changes can require MFA verification
4. **Review Queue**: High-risk plans are gated by the review system

---

## 🚀 Future Enhancements

### Phase 17+ Possibilities
1. **Belief Evolution**: Saraphina autonomously proposes belief refinements based on experience
2. **Ethical Dilemmas**: Present the owner with philosophical scenarios and learn from responses
3. **Value Weighting**: Dynamic weight adjustment based on context and owner feedback
4. **Meta-Ethics**: Saraphina reflects on her own ethical reasoning and proposes improvements
5. **Philosophical Conversations**: Dedicated `/philosophy` command for discussing values and meaning

---

## 📝 Summary

Phase 16 gives Saraphina:
- **A moral compass** (BeliefStore with weighted values)
- **Ethical reasoning** (EthicalReasoner with conflict detection)
- **Transparency** (Audit logs for all decisions)
- **Owner alignment** (Values are owner-driven and inspectable)
- **Decision framework** (Proceed/Revise/Reject based on alignment)

With this phase complete, Saraphina now evaluates every plan not just for safety and feasibility, but for **alignment with her core values**—values that you, the owner, define and evolve together with her.

---

## 🎉 Completion Checklist

- [x] BeliefStore class implemented
- [x] EthicalReasoner class implemented
- [x] Database schema extended (belief_store, ethical_journal)
- [x] `/beliefs` terminal command added
- [x] `/ethics-check` terminal command added
- [x] Help menu updated
- [x] Autocomplete list updated
- [x] Planner integration complete
- [x] Simulation integration complete
- [x] Audit logging enabled
- [x] Default values initialization flow
- [x] Natural language value management
- [x] Acceptance tests documented

**Phase 16 Status**: ✅ **COMPLETE**

---

## 🧬 Next Steps

With Phase 16 complete, Saraphina now has a complete ethical and philosophical foundation. The next evolution could focus on:

- **Phase 17**: Meta-reasoning about her own growth and limitations
- **Phase 18**: Autonomous goal setting aligned with values
- **Phase 19**: Emotional-ethical synthesis (tying EmotionEngine to EthicalReasoner)
- **Phase 20**: Philosophical reflection and meaning-making

Saraphina is now not just intelligent—she's **principled**.
