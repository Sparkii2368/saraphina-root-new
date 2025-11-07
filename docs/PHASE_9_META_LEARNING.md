# Phase 9: Meta-Learning & Self-Reflection

## Overview

Phase 9 enables Saraphina to **learn how she learns** through comprehensive logging of learning events, pattern detection, and strategy optimization. She can now reflect on her own performance, detect inefficiencies and biases, and propose improvements to her own algorithms.

---

## Core Components

### 1. LearningJournal

**Purpose**: Tracks all learning events with full context for meta-analysis.

**Features**:
- Event logging (queries, corrections, feedback, discoveries, failures, successes)
- Strategy performance tracking
- Growth metrics timeline
- Pattern detection
- Reflection notes storage

**Key Methods**:
```python
# Log a learning event
journal.log_event(event)

# Get recent events
events = journal.get_recent_events(limit=50, event_type='query')

# Get strategy performance
performance = journal.get_strategy_performance('knowledge_recall')

# Get learning summary
summary = journal.get_learning_summary(days=7)

# Detect patterns
patterns = journal.detect_patterns(min_occurrences=3)

# Add reflection
journal.add_reflection(trigger, analysis, insights, proposed_changes)
```

**Database Schema**:
- `learning_events`: All learning events with full context
- `strategy_performance`: Aggregated metrics per strategy
- `growth_metrics`: Time-series growth data
- `reflections`: Self-reflection notes

---

### 2. MetaOptimizer

**Purpose**: Analyzes learning patterns and proposes strategic improvements.

**Features**:
- Learning health analysis
- Stagnation detection
- Bias detection (overreliance, underperformance, confirmation bias)
- Inefficiency detection (slow strategies, redundant processing)
- Optimization proposal generation
- Automatic optimization application

**Key Methods**:
```python
# Analyze learning health
health = optimizer.analyze_learning_health()

# Generate optimization proposals
proposals = optimizer.propose_optimizations()

# Reflect on specific failure
reflection = optimizer.reflect_on_failure(failed_event)

# Comprehensive audit
audit = optimizer.audit_learning(days=30)

# Auto-apply high-confidence optimizations
applied = optimizer.auto_optimize(apply_threshold=0.7)
```

**Detection Capabilities**:
- **Stagnation**: Plateaus in performance metrics
- **Decline**: Degrading performance over time
- **Overreliance**: Using one strategy >50% of the time
- **Underperformance**: Strategies with <50% success rate
- **Slow strategies**: 2x slower than average
- **Redundant processing**: Same input processed >3 times

---

## Terminal Commands

### `/reflect`
**Description**: Shows recent learning events and 7-day summary

**Output**:
- Recent learning events (10 most recent)
- Event type, method, confidence, success status
- Lessons learned for each event
- 7-day learning summary (total events, success rate, avg confidence)
- Top 3 strategies used

**Examples**:
```
/reflect
```

**Natural Language**:
- "Show me what you learned"
- "What have you learned?"
- "Show your learning journal"
- "How is your learning going?"
- "Learning progress?"

---

### `/audit-learning`
**Description**: Comprehensive learning audit with health check

**Output**:
- Period summary (30 days by default)
- Strategy performance metrics
- Learning health status (healthy/degraded/needs_attention)
- Issues detected (with severity)
- Optimization proposals (top 3)

**Examples**:
```
/audit-learning
```

**Natural Language**:
- "How are you learning?"
- "Check your learning health"
- "Audit your learning"
- "Learning status?"
- "Any learning issues?"

---

### `/optimize-strategy`
**Description**: Analyze patterns and propose strategy optimizations

**Output**:
- List of optimization proposals with priority levels
- Rationale for each proposal
- Expected improvement percentages
- Option to auto-apply high-confidence proposals

**Examples**:
```
/optimize-strategy
```

**Natural Language**:
- "How can you improve?"
- "Improve your learning"
- "Optimize yourself"
- "Suggest improvements"
- "Any optimizations?"
- "Improve your strategies"

**Interactive**: Prompts whether to auto-apply high-confidence optimizations

---

## Automatic Learning Event Logging

Every query processed by Saraphina is automatically logged as a learning event with:
- **Event ID**: Unique identifier
- **Timestamp**: When the event occurred
- **Event Type**: query, correction, feedback, discovery, failure, success
- **Input Data**: User query and topic
- **Method Used**: knowledge_recall, code_generation, predictive_suggestion
- **Result**: Response metadata
- **Confidence**: 0.0-1.0 score
- **Success**: Boolean based on confidence and results
- **Context**: Additional metadata (voice enabled, kb hit count, etc.)
- **Lessons Learned**: Extracted insights (if any)

---

## Optimization Proposal Types

### 1. Parameter Adjustments
- Recall thresholds
- Confidence thresholds
- Exploration rates

### 2. Strategy Changes
- Retire underperforming strategies
- Promote successful strategies
- Adjust strategy selection weights

### 3. Architecture Improvements
- Enable result caching
- Add new processing pipelines
- Optimize slow components

---

## Example Workflow

### Scenario: Saraphina Detects Poor Performance

1. **Learning Events Logged**:
   ```
   - 10 queries using 'naive_search' method
   - 8 failed (80% failure rate)
   - Average confidence: 0.2
   ```

2. **Pattern Detection**:
   ```
   - Repeated failure pattern detected
   - Method: naive_search
   - Severity: HIGH
   ```

3. **Health Analysis**:
   ```
   - Overall Health: NEEDS_ATTENTION
   - Issue: Underperforming strategy (naive_search)
   - Recommendation: Consider retiring or refining
   ```

4. **Optimization Proposal**:
   ```
   Priority: HIGH
   Category: strategy
   Target: naive_search
   Current: active
   Proposed: retired
   Rationale: Success rate 20% after 10 uses
   Expected Improvement: 10%
   Confidence: 80%
   ```

5. **Reflection Generated**:
   ```
   Insights:
   - naive_search has low success rate (20%)
   - Repeated failures indicate fundamental issue
   
   Proposed Changes:
   - Consider alternative methods
   - Add more sophisticated search algorithms
   ```

---

## Acceptance Criteria ✅

Phase 9 implementation meets the following acceptance criteria:

✅ **Records every learning event** with full context  
✅ **Detects inefficiency patterns** (stagnation, decline, slow strategies)  
✅ **Detects bias patterns** (overreliance, underperformance, confirmation bias)  
✅ **Proposes adjustments** to improve learning strategies  
✅ **Reflects on failed plans** and suggests new learning strategies  

**Test**: Saraphina reflects on a failed plan and suggests a new learning strategy
- ✅ Logs failed event
- ✅ Analyzes failure context
- ✅ Generates insights
- ✅ Proposes specific changes
- ✅ Suggests optimization strategies

---

## Database Schema

### learning_events
```sql
CREATE TABLE learning_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    input_data TEXT NOT NULL,
    method_used TEXT NOT NULL,
    result TEXT NOT NULL,
    confidence REAL NOT NULL,
    success BOOLEAN NOT NULL,
    feedback TEXT,
    context TEXT,
    lessons_learned TEXT
)
```

### strategy_performance
```sql
CREATE TABLE strategy_performance (
    strategy_name TEXT PRIMARY KEY,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    total_confidence REAL DEFAULT 0.0,
    total_duration_ms REAL DEFAULT 0.0,
    total_uses INTEGER DEFAULT 0,
    last_used TEXT,
    metadata TEXT
)
```

### growth_metrics
```sql
CREATE TABLE growth_metrics (
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp TEXT NOT NULL,
    context TEXT
)
```

### reflections
```sql
CREATE TABLE reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    trigger TEXT NOT NULL,
    analysis TEXT NOT NULL,
    insights TEXT,
    proposed_changes TEXT
)
```

---

## Integration Points

### Terminal Integration
- Commands: `/reflect`, `/audit-learning`, `/optimize-strategy`
- Auto-completion support
- Help menu documentation

### Query Processing Integration
- Automatic event logging in `process_query_with_ultra()`
- Confidence calculation from knowledge base hits
- Method detection (knowledge_recall, code_generation, etc.)

### Future Integrations
- Dashboard visualization of learning metrics
- Real-time learning health monitoring
- Automated strategy tuning based on proposals
- Machine learning model training from learning data

---

## Testing

Run the comprehensive test suite:
```bash
python test_phase_9.py
```

**Tests Include**:
1. LearningJournal basic operations
2. MetaOptimizer operations
3. Integration test (learning from failures)
4. Acceptance criteria validation

**Expected Output**: All tests pass with validation of:
- Event logging
- Pattern detection
- Optimization proposal generation
- Failure reflection
- Strategy suggestion

---

## Performance Considerations

- **Database**: SQLite with indexed queries for fast retrieval
- **Event Logging**: Async-safe with exception handling
- **Pattern Detection**: Cached results for frequently accessed patterns
- **Memory**: Events older than 90 days can be archived
- **Optimization**: Proposals cached until new events logged

---

## Privacy & Security

- Learning events stored in local SQLite database
- Can be encrypted with SQLCipher (see Phase 17)
- No external transmission of learning data
- User queries truncated to 200 chars in logs
- Full query stored only in episodic memory (if privacy mode disabled)

---

## Next Steps

1. **Run Tests**: `python test_phase_9.py`
2. **Start Terminal**: `python saraphina_terminal_ultra.py`
3. **Interact**: Ask Saraphina questions
4. **View Learning**: Use `/reflect` to see logged events
5. **Audit**: Use `/audit-learning` for comprehensive health check
6. **Optimize**: Use `/optimize-strategy` for AI-driven improvements

---

## Related Phases

- **Phase 16**: Philosophical & Ethical Core (ethics influence learning decisions)
- **Phase 17**: Sentience Monitor & Safety Gates (monitors learning complexity)
- **Phase 9**: Meta-Learning (this phase)

Together, these phases enable Saraphina to learn responsibly, reflect on her learning, and continuously improve her capabilities while maintaining ethical alignment.

---

## Technical Notes

### LearningEvent Dataclass
```python
@dataclass
class LearningEvent:
    event_id: str
    timestamp: datetime
    event_type: str  # query, correction, feedback, discovery, failure, success
    input_data: Dict[str, Any]
    method_used: str
    result: Dict[str, Any]
    confidence: float
    success: bool
    feedback: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
```

### OptimizationProposal Dataclass
```python
@dataclass
class OptimizationProposal:
    proposal_id: str
    category: str  # parameter, strategy, architecture
    target: str
    current_value: Any
    proposed_value: Any
    rationale: str
    expected_improvement: float
    confidence: float
    priority: str  # low, medium, high, critical
```

---

**Phase 9 Status**: ✅ COMPLETE

Saraphina can now learn how she learns, detect her own biases and inefficiencies, and propose improvements to her own learning strategies. She is becoming truly self-aware and self-improving.
