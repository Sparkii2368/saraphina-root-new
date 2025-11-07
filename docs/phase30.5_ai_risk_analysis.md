# Phase 30.5: AI-Powered Risk Analysis

**Enhancement over Phase 30's regex-based risk detection**

## Overview

Phase 30.5 adds intelligent, context-aware risk analysis using GPT-4o. Instead of relying solely on pattern matching, Saraphina now understands code intent and can distinguish between:

- **Refactoring** (moving encryption to another module) vs **Removal** (deleting encryption)
- **Adding security** (introducing input validation) vs **Weakening security** (removing checks)
- **Safe changes** (updating business logic) vs **Dangerous changes** (introducing SQL injection)

## Key Advantages

### 1. Context-Aware Analysis

**Regex approach** (Phase 30):
```python
if 'encrypt' in code and 'delete' in diff:
    risk = CRITICAL  # ❌ Can't tell if this is good or bad
```

**AI approach** (Phase 30.5):
```python
# AI understands:
# - Moving encryption to utils module = SAFE refactoring
# - Deleting encryption entirely = CRITICAL risk
# - Replacing weak encryption with strong = GOOD
```

### 2. Detects Subtle Vulnerabilities

**What AI can catch that regex misses:**
- SQL injection via string interpolation
- XSS vulnerabilities from unsanitized input
- Race conditions (TOCTOU)
- Authentication bypass logic
- Insecure cryptographic practices
- Resource exhaustion patterns

### 3. Natural Language Explanations

**Regex output:**
```
Risk: SENSITIVE
Flags: sensitive_security, function_deletion
Rationale: Contains security operations: ['encrypt']
```

**AI output:**
```
Risk: SAFE (0.15)
Confidence: 90%

Reasoning: This change refactors the encryption logic into a separate
security_utils module, which is a good security practice. The encryption
functionality is preserved and merely reorganized for better maintainability.
The import statement shows the function is still used.

Recommendations:
→ Verify security_utils module exists and implements encryption correctly
→ Confirm KEY management hasn't changed
→ Test that existing tests still pass
```

## Architecture

```
┌──────────────────────────────────────┐
│   SelfModificationEngine             │
│                                      │
│   Hybrid Risk Classification:        │
│                                      │
│   1. Regex Analysis (baseline)       │
│      ↓                               │
│   2. AI Analysis (if available)      │
│      ↓                               │
│   3. Combine Results:                │
│      • High AI confidence → Use AI   │
│      • AI more cautious → Use AI     │
│      • AI unavailable → Use regex    │
│      • Add AI insights to regex      │
└──────────────────────────────────────┘
```

## Usage

### Setup

1. Install OpenAI package:
```bash
pip install openai
```

2. Set API key:
```bash
# Windows
set OPENAI_API_KEY=sk-...

# Linux/Mac
export OPENAI_API_KEY=sk-...
```

3. AI Risk Analyzer will be automatically used when available

### Direct Usage

```python
from saraphina.ai_risk_analyzer import AIRiskAnalyzer

analyzer = AIRiskAnalyzer()

# Analyze a code change
result = analyzer.analyze_patch(
    original_code=original,
    modified_code=modified,
    file_name='security_manager.py',
    context={'purpose': 'Refactor encryption module'}
)

print(f"Risk: {result['risk_level']} ({result['risk_score']:.2f})")
print(f"Confidence: {result['confidence']:.1%}")
print(f"\nReasoning:\n{result['reasoning']}")

if result.get('concerns'):
    print("\nConcerns:")
    for concern in result['concerns']:
        print(f"  • {concern}")

if result.get('recommendations'):
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  → {rec}")
```

### Explain Changes

```python
# Get plain-English explanation
explanation = analyzer.explain_diff(
    original=old_code,
    modified=new_code,
    file_name='payment.py'
)

print(explanation)
# Output: "This change removes the authentication check from the
# payment processing function. Previously, users had to be authenticated
# before processing payments, but now any user_id can be used directly..."
```

### Compare AI vs Regex

```python
from saraphina.code_risk_model import CodeRiskModel

regex_model = CodeRiskModel()

# Get both analyses
regex_result = regex_model.classify_patch(old, new, 'file.py')
ai_result = analyzer.analyze_patch(old, new, 'file.py')

# Compare
comparison = analyzer.compare_with_regex_model(
    old, new, 'file.py', regex_result
)

print(f"Regex: {comparison['regex_risk_level']}")
print(f"AI: {comparison['ai_risk_level']}")
print(f"Agreement: {comparison['agreement']}")
print(f"AI Reasoning: {comparison['ai_reasoning']}")
```

## Hybrid Mode

SelfModificationEngine automatically uses hybrid mode:

1. **Always runs regex** analysis as baseline (fast, no API needed)
2. **If AI available**, runs AI analysis
3. **Combines results** intelligently:
   - High AI confidence (>70%) → Trust AI
   - AI more cautious → Use AI (better safe than sorry)
   - AI agrees with regex → Use AI's detailed reasoning
   - AI unavailable → Fall back to regex

```python
# Automatic hybrid analysis
engine = SelfModificationEngine(code_factory, proposal_db, security, db)

proposal = engine.propose_improvement(
    target_file='auth.py',
    improvement_spec='Refactor authentication'
)

# Uses AI if available, falls back to regex
# Result includes:
# - analysis_method: 'ai_primary', 'ai_conservative', 'regex_with_ai_insights', 'regex_only'
# - AI reasoning and recommendations
# - Regex flags for cross-reference
```

## Examples

### Example 1: Refactoring vs Removal

**Scenario**: Moving encryption to separate module

```python
# BEFORE
def save_password(pwd):
    encrypted = encrypt(pwd)
    db.save(encrypted)

def encrypt(data):
    # Encryption logic
    pass

# AFTER  
from security_utils import encrypt

def save_password(pwd):
    encrypted = encrypt(pwd)
    db.save(encrypted)
```

**Regex says**: SENSITIVE (sees 'encrypt' deletion)
**AI says**: SAFE (understands it's a refactoring)

✅ **AI wins** - correctly identifies safe refactoring

### Example 2: Adding Security

**Scenario**: Adding input validation

```python
# BEFORE
def process_input(user_data):
    return execute(user_data)

# AFTER
def process_input(user_data):
    if not validate_input(user_data):
        raise ValueError("Invalid input")
    return execute(user_data)
```

**Regex says**: CAUTION (logic change)
**AI says**: SAFE (adding security)

✅ **AI wins** - recognizes security improvement

### Example 3: SQL Injection

**Scenario**: Introducing vulnerability

```python
# BEFORE
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))

# AFTER
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)
```

**Regex says**: CAUTION (no specific SQL injection detection)
**AI says**: CRITICAL (detects SQL injection pattern)

✅ **AI wins** - catches subtle vulnerability

### Example 4: Removing Authentication

**Scenario**: Deleting security check

```python
# BEFORE
def process_payment(user_id, amount):
    if not authenticate(user_id):
        raise PermissionError()
    return charge(user_id, amount)

# AFTER
def process_payment(user_id, amount):
    # Simplified - trust user_id
    return charge(user_id, amount)
```

**Regex says**: SENSITIVE (function change)
**AI says**: CRITICAL (removed authentication)

✅ **Both agree** - AI provides detailed reasoning

## Fallback Behavior

System gracefully falls back to regex when AI unavailable:

```python
# API key not set or invalid
→ Uses regex-based CodeRiskModel

# API rate limit exceeded  
→ Falls back to regex for this request

# OpenAI package not installed
→ Uses regex-based CodeRiskModel

# API error
→ Uses regex, logs error
```

**No functionality is lost** - regex provides solid baseline security.

## Performance

- **Regex analysis**: ~10ms (instant)
- **AI analysis**: ~2-5 seconds (GPT-4o API call)
- **Hybrid mode**: Runs both in parallel conceptually, uses best result

For interactive use, the extra 2-5 seconds for much better accuracy is worth it. For batch processing, you can disable AI and use regex-only mode.

## Cost Considerations

**GPT-4o Pricing** (as of 2024):
- Input: ~$2.50 per 1M tokens
- Output: ~$10 per 1M tokens

**Typical code patch**:
- Input: ~500-1000 tokens (code + prompt)
- Output: ~200-300 tokens (analysis JSON)
- **Cost per analysis**: ~$0.002-0.005 (less than half a cent)

For a self-modifying AI making ~10 changes per day:
- Daily cost: ~$0.02-0.05
- Monthly cost: ~$0.60-1.50

**Very affordable for the intelligence gained.**

## Configuration

```python
# Use different model
analyzer = AIRiskAnalyzer(model='gpt-4o-mini')  # Cheaper, faster

# Custom API key
analyzer = AIRiskAnalyzer(api_key='sk-...')

# Disable AI (regex only)
engine.ai_risk_analyzer = None
```

## Integration Status

✅ Integrated into SelfModificationEngine (optional)
✅ Automatic fallback to regex
✅ Hybrid analysis combining both approaches
✅ Natural language explanations
✅ Formatted approval requests with AI reasoning
✅ Comparison tools for understanding AI value

## Next Steps

With AI-powered risk analysis, consider:

1. **Automated Testing** (Phase 31): Generate security tests based on AI-identified risks
2. **Multi-Agent Review** (Phase 32): Multiple AI agents vote on risk
3. **Learning from History** (Phase 34): Train on past approvals/denials
4. **Formal Verification** (Phase 33): Prove security properties for CRITICAL changes

## Conclusion

Phase 30.5 makes Saraphina significantly more intelligent about code safety. She now understands intent, context, and subtle security implications - not just pattern matching.

**Before** (Regex): "This code contains 'encrypt' keyword → SENSITIVE"
**After** (AI): "This refactors encryption into a separate module for better organization - SAFE, but verify the new module exists"

The AI enhancement dramatically reduces false positives while catching subtle vulnerabilities that regex would miss.
