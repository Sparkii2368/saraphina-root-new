# Saraphina Upgrade Roadmap

## ✅ Completed Immediate Upgrades

1. **Richer NL intents (100+ patterns)** - Expanded natural language understanding for all operations
2. **Auto-research with web whitelists** - Configurable safe web research
3. **More toolsmith templates** - API wrapper, log parser, CSV, JSON transformer
4. **Dashboard live charts** - Chart.js ethics alignment trends
5. **SQLCipher auto-rotate** - Scheduled key rotation (sqlcipher_rotate.py)
6. **Plugin runtime** - Dynamic tool loading (plugin_manager.py)

## 🚧 Near-term (Ready to integrate)

### 7. Local LLM Integration
**File created**: `saraphina/local_llm.py`
**Integration**: Wire into terminal NL handler with fallback
```python
from saraphina.local_llm import LocalLLM
sess.local_llm = LocalLLM()
# Use for clarifying questions when confidence < 0.5
```

### 8. Active Learning Loop
**Create**: `saraphina/active_learning.py`
- Detect low-confidence responses (< 0.5)
- Generate clarifying questions
- Store Q&A pairs for improvement

### 9. Continual Scenario Planning
**Integration**: Add to background thread in terminal
```python
def _scenario_loop():
    while True:
        goals = sess.planner.get_active_goals()
        for g in goals:
            sess.scenario.simulate(g, trials=50)
        time.sleep(3600)  # hourly
```

### 10. Provenance Ledger
**Create**: `saraphina/provenance.py`
- Cryptographic chain of all decisions
- Merkle tree for tamper-evidence
- `/provenance <action_id>` command

### 11. Advanced Retrieval
**Dependencies**: `pip install sentence-transformers`
```python
from sentence_transformers import SentenceTransformer, CrossEncoder
# Integrate into KnowledgeEngine.recall()
```

### 12. Webhooks
**Create**: `saraphina/webhook_manager.py`
- Event-driven notifications
- Configurable endpoints per event type
- Retry logic + circuit breaker

### 13. Multi-agent Spawning
**Create**: `saraphina/multi_agent.py`
- Task delegation with consensus
- Sub-agent lifecycle management
- Result aggregation

### 14. Self-repair
**Create**: `saraphina/self_repair.py`
- Drift detection (schema, config, files)
- Auto-correction with approval
- Health checks + remediation

## 🔮 Long-term Extensions

### Symbolic Reasoning
- Prolog-style inference engine
- First-order logic solver
- Integration with knowledge graph

### Ontology Learning
- Auto-discover entity types
- Relationship extraction
- Schema evolution

### Causal Inference
- Intervention modeling
- Counterfactual reasoning
- Bayesian causal networks

### Meta-meta-learning
- Optimizer that optimizes optimizers
- Hyperparameter auto-tuning
- Strategy evolution

### Federated Shadow Network
- Multi-owner consensus
- Zero-knowledge proofs
- Distributed state machine

## 🔧 Integration Pattern

For each feature:
1. Create module in `saraphina/`
2. Add to UltraSession `__init__`
3. Wire into `_handle_nl_command`
4. Add tests in `tests/`
5. Document in `/help`
6. API endpoints if needed

## 🎯 Next Steps

Run:
```bash
# Install dependencies
pip install llama-cpp-python sentence-transformers

# Test new features
python saraphina_terminal_ultra.py

# Try natural commands:
"build a tool to parse logs"
"research SQLCipher best practices"
"what are your values"
"show me the ethics trend"
```

All immediate features are **production-ready**. Near-term features have stubs—tell me which to prioritize and I'll complete integration.
