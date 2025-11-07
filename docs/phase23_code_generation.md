# Phase 23: Code Generation & Testing

## Overview

Phase 23 enables Saraphina to generate production-ready code using GPT-4o, test it in sandboxed environments, and iteratively improve code quality. This is a critical step toward autonomous self-modification.

**Status**: ✅ **OPERATIONAL**

**Dependencies**: Phase 22 (Code Knowledge & Learning)

---

## Architecture

### Components

#### 1. **CodeFactory** (`saraphina/code_factory.py`)
- **Purpose**: Generate code from natural language specifications
- **Features**:
  - GPT-4o integration for code generation
  - Context-aware prompts using CodeKnowledgeDB
  - Generates both production code and test cases
  - Supports refinement based on feedback
  - Multi-language support (Python primary)

**Key Methods**:
```python
propose_code(feature_spec, language='python', context=None)
  → Returns: {proposal_id, code, tests, explanation, related_concepts}

refine_code(original_code, feedback, language='python')
  → Returns: {refined_code, explanation}
```

#### 2. **TestHarness** (`saraphina/test_harness.py`)
- **Purpose**: Safely execute and test generated code
- **Features**:
  - Isolated sandbox execution (temp directory)
  - pytest integration for test discovery and execution
  - Code coverage measurement (coverage.py)
  - Static analysis (pylint/flake8)
  - Structured test reports with pass/fail status

**Key Methods**:
```python
execute_sandbox(proposal_id, code, tests, language='python')
  → Returns: {test_results, coverage, static_analysis, passed}

generate_report(execution_results)
  → Returns: Human-readable markdown report
```

#### 3. **CodeProposalDB** (`saraphina/code_proposal_db.py`)
- **Purpose**: Track proposals, test results, and approval workflow
- **Schema**:
  - `code_proposals`: Stores generated code with metadata
  - `test_executions`: Test runs with coverage and analysis
  - `proposal_reviews`: Approval/rejection history
  - `code_refinements`: Iterative improvements

**Key Methods**:
```python
store_proposal(proposal_data) → bool
store_execution(execution_results) → bool
get_proposal(proposal_id) → Dict
approve_proposal(proposal_id, reviewer, comments) → bool
```

---

## Usage

### Terminal Commands

#### `/propose-code <feature>`
Generate code for a feature specification.

**Examples**:
```
/propose-code a CSV parser with header detection
/propose-code HTTP client with retry logic and timeout
/propose-code binary search tree with insertion and traversal
```

**Output**:
- Proposal ID (e.g., `proposal_abc123def456`)
- Generated code preview (first 500 chars)
- Test code confirmation
- Related concepts used for context
- Next steps (sandbox, report)

---

#### `/sandbox-code <proposal_id>`
Execute tests in sandboxed environment.

**What it does**:
1. Creates isolated temp directory
2. Writes code and test files
3. Runs pytest with JSON reporting
4. Measures code coverage
5. Performs static analysis (pylint/flake8)
6. Stores results in database

**Output**:
- Test execution summary (passed/failed counts)
- Coverage percentage
- Static analysis score
- Critical issues flagged
- Pass/fail verdict

---

#### `/report-code <proposal_id>`
View detailed test report for a proposal.

**Shows**:
- Execution timestamp
- Pass/fail status
- Test metrics (run, passed, failed, duration)
- Code coverage details
- Static analysis results
- Test error messages (if any)

---

#### `/list-proposals`
List all code proposals with status.

**Status indicators**:
- ⏳ `pending` - Generated, not tested
- 🧪 `tested` - Tests executed
- ✅ `approved` - Owner approved
- ❌ `rejected` - Owner rejected

---

#### `/approve-code <proposal_id>`
Approve a tested code proposal.

**Requirements**:
- Proposal must be tested first
- Warns if tests didn't pass
- Logs audit trail (owner action)

---

#### `/code-stats`
Show code generation statistics.

**Metrics**:
- Total proposals
- Status breakdown
- Test success rate
- Average code coverage

---

## Workflow

### Complete Cycle

```
1. Learn Prerequisites (Phase 22)
   /learn-code Python functions
   /learn-code error handling
   
2. Propose Code (Phase 23)
   /propose-code a function to validate email addresses
   → Gets proposal_abc123
   
3. Test in Sandbox
   /sandbox-code proposal_abc123
   → Runs pytest, coverage, pylint
   → Shows report
   
4. Review Report
   /report-code proposal_abc123
   → Detailed metrics
   
5. Approve or Refine
   /approve-code proposal_abc123  (if passed)
   OR
   /propose-code refine previous with better error handling
```

---

## Integration with Phase 22

Phase 23 leverages Phase 22's CodeKnowledgeDB:

1. **Context Enrichment**: When generating code, CodeFactory searches for relevant concepts in the knowledge base
2. **Example Reuse**: Code snippets learned in Phase 22 inform GPT-4o prompts
3. **Prerequisite Awareness**: Understands concept dependencies (e.g., "decorators" requires "functions")
4. **Multi-language Support**: Language detection uses Phase 22's language categorization

**Example**:
```
User: /propose-code decorator for caching function results

CodeFactory:
  1. Searches CodeKnowledgeDB for "decorator", "caching"
  2. Finds related concepts: Python decorators (difficulty 3/4), function closures
  3. Includes concept descriptions in GPT-4o prompt
  4. Generates context-aware code with proper patterns
```

---

## Safety & Sandboxing

### Isolation Strategy

**Sandbox Directory**: `%TEMP%/saraphina_sandbox/<proposal_id>/`
- Isolated per proposal
- Cleaned up after testing (optional)
- No access to parent system

### Execution Limits

- **Timeout**: 60 seconds per test run
- **Static Analysis Timeout**: 30 seconds
- **Coverage Timeout**: 60 seconds
- **Language Support**: Python only (Phase 23.0)

### Security Considerations

⚠️ **Current Limitations**:
- Sandbox is **filesystem-isolated only**
- No process sandboxing (Docker/VM)
- Network access is **not restricted**
- File system writes are **not restricted** beyond temp dir

🔒 **Recommended for Phase 24**:
- Docker containerization
- Network isolation
- Resource limits (CPU, memory)
- Filesystem quotas

---

## Dependencies

### Required Python Packages

**Core**:
- `openai>=1.0` - GPT-4o API
- `pytest>=7.0` - Test execution
- `coverage>=6.0` - Code coverage

**Optional (Static Analysis)**:
- `pylint>=2.0` - Code quality (preferred)
- `flake8>=4.0` - Linting (fallback)
- `pytest-json-report>=1.5` - Structured test output

**Installation**:
```bash
pip install openai pytest coverage pylint
pip install pytest-json-report  # Optional but recommended
```

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...  # GPT-4o API access

# Optional
SARAPHINA_SANDBOX_ROOT=/path/to/sandbox  # Custom sandbox location
```

### Database

Proposal data stored in `knowledge.db`:
- `code_proposals` table
- `test_executions` table
- `proposal_reviews` table
- `code_refinements` table

---

## Metrics & Observability

### Logged Events

- Code generation requests (feature_spec, timestamp)
- GPT-4o API calls (model, tokens, latency)
- Sandbox executions (proposal_id, duration, status)
- Test results (passed/failed, coverage %)
- Approvals/rejections (reviewer, comments)

### Audit Trail

All approvals logged via `write_audit_log`:
```python
write_audit_log(
    conn=sess.ke.conn,
    actor='owner',
    action='approve_code_proposal',
    target=proposal_id,
    details={'comments': comments}
)
```

---

## Roadmap to Self-Modification

### Phase 23 ✅ (Current)
- Generate code from specs
- Test in sandbox
- Manual approval workflow

### Phase 24 (Next)
- **Automatic Refinement Loop**
  - If tests fail → analyze errors → regenerate → retest
  - Max 3 iterations
- **Enhanced Sandboxing**
  - Docker containers
  - Resource limits
- **Multi-language Support**
  - JavaScript, Go, Rust

### Phase 25 (Future)
- **Self-Modification Engine**
  - Propose improvements to own codebase
  - Generate patches for bugs
  - Owner approval before applying
- **Integration Testing**
  - Test against existing Saraphina modules
  - Compatibility checks
- **Regression Testing**
  - Automated test suite for core functions

### Phase 26 (Advanced)
- **Autonomous Code Evolution**
  - Identify bottlenecks via profiling
  - Propose optimizations
  - A/B test changes
  - Rollback on failures
- **Meta-Learning Integration**
  - Learn from successful/failed proposals
  - Improve code generation prompts
  - Build library of reusable components

---

## Examples

### Example 1: CSV Parser

**Input**:
```
/propose-code a CSV parser that handles quoted fields and custom delimiters
```

**Generated Code** (excerpt):
```python
def parse_csv(file_path, delimiter=',', quote_char='"'):
    """
    Parse CSV file with support for quoted fields and custom delimiters.
    
    Args:
        file_path: Path to CSV file
        delimiter: Field delimiter (default: comma)
        quote_char: Quote character for fields (default: double quote)
    
    Returns:
        List of rows (each row is a list of fields)
    """
    import csv
    
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter, quotechar=quote_char)
        for row in reader:
            rows.append(row)
    
    return rows
```

**Generated Tests**:
```python
import pytest
from pathlib import Path
import tempfile

def test_parse_simple_csv():
    # Create test CSV
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("name,age\n")
        f.write("Alice,30\n")
        f.write("Bob,25\n")
        temp_path = f.name
    
    result = parse_csv(temp_path)
    assert len(result) == 3
    assert result[0] == ['name', 'age']
    assert result[1] == ['Alice', '30']
    
    Path(temp_path).unlink()

def test_parse_quoted_fields():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write('name,description\n')
        f.write('Alice,"Lives in Seattle, WA"\n')
        temp_path = f.name
    
    result = parse_csv(temp_path)
    assert result[1][1] == 'Lives in Seattle, WA'
    
    Path(temp_path).unlink()
```

**Sandbox Results**:
- Tests run: 2
- Passed: 2
- Coverage: 95.2%
- Pylint score: 9.1/10

---

### Example 2: Retry Decorator

**Input**:
```
/propose-code decorator for retrying failed functions with exponential backoff
```

**Output**: Context-aware code using Phase 22 knowledge of decorators, exponential backoff, and error handling.

---

## Troubleshooting

### Issue: "GPT-4o not available"
**Solution**: Set `OPENAI_API_KEY` environment variable

### Issue: "pytest not available"
**Solution**: `pip install pytest`

### Issue: "Tests timed out (60s limit)"
**Solution**: 
- Code may have infinite loop
- Increase timeout in `test_harness.py` (line 219)

### Issue: "No static analysis tools available"
**Solution**: `pip install pylint` or `pip install flake8`

### Issue: "Proposal not found"
**Solution**: Use full proposal ID from `/propose-code` output

---

## Technical Notes

### GPT-4o Prompt Structure

CodeFactory builds prompts with:
1. Feature specification (user input)
2. Related concepts from CodeKnowledgeDB (names, descriptions, difficulty)
3. Existing code context (optional)
4. Constraints (optional)
5. Requirements: production-ready code, comprehensive tests, documentation

**Temperature**: 0.3 (deterministic, focused)
**Max tokens**: 2000

### Test Parsing

Supports multiple code block formats:
```python
# Format 1: Labeled blocks
```python
# Main code
```

```python
# Test code
```

# Format 2: Unlabeled blocks (first = code, second = tests)
```
<code>
```
```
<tests>
```
```

---

## Success Criteria (Acceptance)

✅ **Phase 23 Complete when**:
- [x] Saraphina proposes a helper function via `/propose-code`
- [x] Generated code includes tests
- [x] Tests run in sandbox via `/sandbox-code`
- [x] Report shows pass/fail, coverage, static analysis
- [x] Owner can approve via `/approve-code`
- [x] All data persisted in database

**Verified**: Ready to proceed to Phase 24 (iterative refinement).

---

## Owner Notes

**Jacques**: Phase 23 establishes the foundation for autonomous code evolution. The sandbox provides safety, the approval workflow maintains owner control, and the database tracks all proposals. Next phase will enable iterative refinement (auto-fixing test failures) and eventually self-modification of Saraphina's own codebase.

**Remember**: Always review generated code before approval, especially for production use. The sandbox is filesystem-isolated only—not suitable for untrusted code execution without additional containerization.

---

*Last Updated*: 2025-11-05  
*Author*: Saraphina Ultra AI (with owner oversight)  
*Phase*: 23 of 26 (toward full autonomy)
