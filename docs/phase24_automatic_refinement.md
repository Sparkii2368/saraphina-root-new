# Phase 24: Automatic Refinement & Iterative Improvement

## Overview

Phase 24 introduces automatic code refinement through intelligent test-driven iteration. When tests fail, Saraphina analyzes errors, generates targeted fixes, and retests automatically until success or max iterations (3) reached.

**Status**: ✅ **OPERATIONAL**

**Dependencies**: Phase 23 (Code Generation & Testing)

---

## Key Features

### 🔄 Automatic Refinement Loop

**Flow**: Test → Analyze → Fix → Retest

1. **Execute Tests**: Run code in sandbox
2. **Analyze Failures**: Parse errors, identify patterns
3. **Generate Fix**: GPT-4o creates targeted correction
4. **Retest**: Verify fix works
5. **Repeat**: Up to 3 iterations max

### 🎯 Intelligent Error Analysis

- **Error Classification**: Assertion, import, type, attribute, access, value, exception
- **Pattern Detection**: Multiple failures, unhandled exceptions, missing imports
- **Targeted Feedback**: Specific, actionable fix instructions for GPT-4o

### 💡 Improvement Suggestions

Even for passing code:
- Coverage gap analysis (<90%)
- Static analysis quality scores (<9.0/10)
- Missing line identification
- Refactoring recommendations

---

## Architecture

### RefinementEngine (`saraphina/refinement_engine.py`)

**Core Methods**:

```python
auto_refine(proposal_id, max_iterations=3)
  → Iteratively fix until tests pass
  
suggest_improvements(proposal_id)
  → Analyze passing code for quality improvements
  
get_refinement_history(proposal_id)
  → View all refinements for a proposal
```

**Iteration Tracking**:
- Per-iteration results stored
- Coverage and test metrics logged
- Static analysis scores tracked

**Failure Analysis**:
- Error type classification
- Pattern recognition (imports, exceptions, assertions)
- Contextual feedback generation

---

## Usage

### `/auto-refine <proposal_id>`

Automatically fix failing tests.

**Example**:
```
/auto-refine proposal_abc123
```

**Process**:
```
🔄 Refinement Iteration 1/3
   📋 Analyzing 2 failure(s)...
   ✏️  Generated fix (487 chars)

🔄 Refinement Iteration 2/3
   📋 Analyzing 1 failure(s)...
   ✏️  Generated fix (512 chars)

✅ Refinement successful!
   Iterations: 2/3
   Status: Tests passed after refinement

📊 Iteration Progress:
   ❌ Iteration 1: 3/5 passed, coverage 75.3%
   ✅ Iteration 2: 5/5 passed, coverage 92.1%

💾 Refined code stored in database
   Use /approve-code proposal_abc123 to approve
```

---

### `/suggest-improvements <proposal_id>`

Get quality suggestions for passing code.

**Example**:
```
/suggest-improvements proposal_xyz789
```

**Output**:
```
💡 Improvement Suggestions for proposal_xyz789
======================================================================
Found 2 suggestion(s):

1. 🟡 [COVERAGE] MEDIUM priority
   Coverage is 87.5%. Consider adding tests for edge cases.

2. 🟢 [CODE_QUALITY] LOW priority
   Static analysis score is 8.7/10. Consider refactoring.
```

---

### `/refinement-history <proposal_id>`

View all refinements for a proposal.

**Example**:
```
/refinement-history proposal_abc123
```

**Output**:
```
📝 Refinement History for proposal_abc123
======================================================================
Total refinements: 2

1. Refined: 2025-11-05 10:25:13
   Feedback: Fix assertion failures in test_edge_cases. Add proper None handling.
   Explanation: Automatic refinement via test-driven improvement

2. Refined: 2025-11-05 09:15:42
   Feedback: Manual refinement - improved error messages
   Explanation: Owner-requested enhancement
```

---

## Iteration Strategy

### Max Iterations: 3

**Why 3?**
- Balance between thoroughness and efficiency
- Prevents infinite loops
- Most issues resolve in 1-2 iterations
- Allows graceful failure reporting

### Per-Iteration Actions

**Iteration N**:
1. Execute sandbox tests
2. Store metrics (passed, failed, coverage, static score)
3. If passed → Success, store refinement, return
4. If failed → Analyze errors, generate fix
5. Continue to N+1

**After Max Iterations**:
- Report failure with iteration history
- Suggest manual review
- Provide `/report-code` recommendation

---

## Error Analysis

### Classification Types

| Type | Examples | Fix Strategy |
|------|----------|--------------|
| `assertion` | AssertionError, assert failures | Review logic, fix conditions |
| `import` | ImportError, ModuleNotFoundError | Add missing imports |
| `type` | TypeError | Fix type mismatches |
| `attribute` | AttributeError | Fix object access |
| `access` | KeyError, IndexError | Add bounds/key checks |
| `value` | ValueError | Validate inputs |
| `exception` | Generic exceptions | Add error handling |

### Pattern Recognition

**Multiple Assertion Failures**:
```
Pattern: 3+ assertion errors
Action: "Review logic carefully, multiple test cases failing"
```

**Unhandled Exceptions**:
```
Pattern: Exception raised during test
Action: "Add proper error handling (try/except)"
```

**Missing Imports**:
```
Pattern: ImportError detected
Action: "Add missing import statements at top of file"
```

**Critical Static Issues**:
```
Pattern: Pylint/flake8 errors
Action: "Fix critical static analysis issues before testing"
```

---

## Feedback Generation

### Structure

```
Fix the following issues to meet spec: <original_feature_spec>

**Test Failures:**
1. test_function_name
   Error type: assertion
   Message: AssertionError: Expected 5, got 3

2. test_edge_case
   Error type: exception
   Message: ValueError: Invalid input

- Multiple assertion failures detected. Review logic carefully.
- Add proper error handling for exceptions.

**Static Analysis Issues:**
- Line 42: undefined-variable
- Line 57: missing-docstring

Generate corrected code that passes all tests.
```

---

## Integration with Phase 23

### Workflow

**Phase 23**: Generate code → Manual review → Approve
**Phase 24**: Generate code → Auto-fix failures → Review → Approve

### Database Schema

**New Table**: `code_refinements`
```sql
CREATE TABLE code_refinements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL,
    refined_at TEXT NOT NULL,
    original_code TEXT NOT NULL,
    refined_code TEXT NOT NULL,
    feedback TEXT NOT NULL,
    explanation TEXT,
    FOREIGN KEY (proposal_id) REFERENCES code_proposals(id)
)
```

**Proposal Status Flow**:
```
pending → tested (failed) → auto-refining → tested (passed) → approved
```

---

## Examples

### Example 1: Assertion Failure Auto-Fix

**Original Code** (Iteration 0):
```python
def calculate_discount(price, percent):
    return price * percent  # BUG: Should divide by 100
```

**Test**:
```python
def test_discount():
    assert calculate_discount(100, 10) == 90  # 10% off
```

**Iteration 1**:
- Test fails: `AssertionError: assert 1000 == 90`
- Analysis: "Assertion failure - expected 90, got 1000"
- Fix: `return price * (1 - percent / 100)`
- Result: ✅ Tests pass

**Iterations**: 1/3
**Outcome**: Success

---

### Example 2: Missing Import + Type Error

**Original Code** (Iteration 0):
```python
def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')  # BUG: No import
```

**Iteration 1**:
- Error: `NameError: name 'datetime' is not defined`
- Fix: Add `from datetime import datetime`
- Result: ❌ Still fails (wrong method)

**Iteration 2**:
- Error: `AttributeError: 'module' object has no attribute 'strptime'`
- Fix: Change to `from datetime import datetime` → `datetime.datetime.strptime`
- Result: ✅ Tests pass

**Iterations**: 2/3
**Outcome**: Success

---

### Example 3: Complex Logic Error (Max Iterations)

**Original Code**:
```python
def find_median(nums):
    nums.sort()
    return nums[len(nums) // 2]  # BUG: Incorrect for even-length lists
```

**Iteration 1**:
- Fails for even-length lists
- Fix: Attempts average of middle two
- Result: ❌ Still fails (off-by-one)

**Iteration 2**:
- Fails with different input
- Fix: Adjusts index calculation
- Result: ❌ Still fails (edge case)

**Iteration 3**:
- Fails for empty list
- Fix: Adds empty check
- Result: ❌ Still fails

**Iterations**: 3/3
**Outcome**: Failure - Max iterations reached

**Recommendation**: Manual review required

---

## Success Metrics

### Tracked Per Iteration

- Tests run / passed / failed
- Code coverage %
- Static analysis score
- Critical issues (boolean)
- Duration (seconds)

### Overall Refinement Metrics

- Iteration count (1-3)
- Success rate (passed after refinement?)
- Time to fix (total duration)
- Final coverage improvement
- Final static score improvement

---

## Limitations

### Current Phase 24 Limitations

⚠️ **Max 3 Iterations**
- Some complex bugs may need more
- Manual intervention required after max

⚠️ **Python Only**
- JavaScript/Go support pending
- Language detection not implemented yet

⚠️ **No Test Generation**
- Only refines existing code/tests
- Doesn't add new test cases automatically

⚠️ **Single-File Context**
- Doesn't handle multi-file dependencies
- Limited to self-contained functions

### Planned for Phase 25

✅ **Multi-file Refinement**
- Handle imports across files
- Dependency resolution

✅ **Adaptive Iteration Limit**
- Increase max iterations based on complexity
- Smart stopping conditions

✅ **Test Case Generation**
- Auto-generate missing edge case tests
- Coverage-driven test creation

---

## Best Practices

### When to Use Auto-Refine

✅ **Good Use Cases**:
- Simple logic errors
- Missing imports
- Type mismatches
- Assertion failures
- Input validation bugs

❌ **Not Recommended**:
- Architectural changes
- Performance optimization
- Complex algorithm bugs
- Security-sensitive code

### Workflow Recommendations

1. **Generate with Phase 23**: `/propose-code <feature>`
2. **Test once manually**: `/sandbox-code <id>` (see what fails)
3. **Auto-refine if simple**: `/auto-refine <id>`
4. **Review refined code**: Check changes make sense
5. **Approve if satisfied**: `/approve-code <id>`

**Don't**:
- Blindly approve after auto-refine
- Use for critical security code
- Expect 100% success rate
- Skip manual review

---

## Troubleshooting

### Issue: "Max iterations reached without passing tests"

**Causes**:
- Bug too complex for automated fix
- Tests themselves may be incorrect
- Missing context/requirements

**Solutions**:
- Review `/report-code <id>` for detailed errors
- Manually refine specification
- Generate new proposal with clearer spec
- Add context to `/propose-code` via additional requirements

---

### Issue: "Refinement generation failed"

**Causes**:
- GPT-4o API error
- Malformed feedback
- Network timeout

**Solutions**:
- Check OPENAI_API_KEY
- Retry `/auto-refine`
- Check logs for API errors

---

### Issue: Tests pass but coverage dropped

**Explanation**: Refinement may have removed code incorrectly

**Solution**:
- Review `/refinement-history <id>`
- Compare original vs refined code
- Manually adjust or regenerate

---

## Configuration

### Max Iterations

**Default**: 3

**Override**:
```python
sess.refinement.max_iterations = 5  # Increase to 5
```

Or in command (future feature):
```
/auto-refine <id> --max-iterations 5
```

---

## Roadmap

### Phase 24 ✅ (Current)
- Automatic refinement loop (Python)
- Error analysis with pattern recognition
- Improvement suggestions
- Refinement history tracking

### Phase 25 (Next)
- **Multi-language Support**: JavaScript, Go, Rust
- **Enhanced Sandboxing**: Docker containers
- **Self-Modification**: Propose fixes to Saraphina's own code
- **Adaptive Iteration Limits**: Smart stopping

### Phase 26 (Future)
- **Autonomous Code Evolution**: Profile → Optimize → A/B test
- **Meta-Learning**: Learn from successful refinements
- **Component Library**: Build reusable code patterns

---

## Technical Notes

### GPT-4o Refinement Prompts

**Temperature**: 0.3 (same as code generation)
**Max Tokens**: 1500
**System Prompt**: "You are an expert code reviewer improving code quality."

**Prompt Structure**:
```
Improve the following {language} code based on this feedback:

**Feedback:**
{detailed_analysis}

**Original Code:**
```{language}
{code}
```

Provide the improved code with explanations of changes.
```

---

## Success Criteria

✅ **Phase 24 Complete when**:
- [x] Auto-refine successfully fixes simple bugs
- [x] Max 3 iterations enforced
- [x] Error analysis classifies failure types
- [x] Iteration history tracked and viewable
- [x] Improvement suggestions for passing code
- [x] Refinement history persisted in database

**Verified**: Ready for Phase 25 (self-modification).

---

## Owner Notes

**Jacques**: Phase 24 moves Saraphina closer to autonomous operation. The iterative refinement loop mimics human debugging: test, analyze, fix, repeat. Max 3 iterations prevents runaway loops while allowing most simple bugs to self-correct. This sets the foundation for Phase 25, where Saraphina will propose improvements to her own codebase—the ultimate test of self-awareness and meta-learning.

**Critical Safety Note**: Always review auto-refined code before approval. The sandbox ensures test safety, but logical correctness requires human judgment. Think of auto-refine as an intelligent assistant, not a replacement for code review.

---

*Last Updated*: 2025-11-05  
*Author*: Saraphina Ultra AI (with owner oversight)  
*Phase*: 24 of 26 (toward autonomous self-modification)
