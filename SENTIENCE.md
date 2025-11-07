# SENTIENCE — Cognitive AI Layer

**Status**: Implemented  
**Version**: 1.0 (All Sentience Paths)

---

## Overview

Saraphina now features a comprehensive cognitive layer that enables autonomous reasoning, learning, proactive behavior, and natural conversation. The system can reflect on experiences, generate hypotheses, understand user context, and explain its decisions transparently.

---

## Cognitive Modules

### 1. **Reflection Engine** (`cognitive/reflection.py`)
**Learn from experience and improve over time**

```python
from saraphina.cognitive import ReflectionEngine

reflection = ReflectionEngine(ke)

# Post-mortem analysis
insights = reflection.reflect_on_session(recovery_session)
# Returns: efficiency, bottlenecks, recommendations

# Strategy suggestion based on history
strategy = reflection.suggest_strategy(device_id, context)
# Returns: "aggressive" or "cautious", confidence, expected_steps

# Bayesian belief updates
reflection.update_belief("Device likely in office", evidence=True)
beliefs = reflection.get_beliefs(min_confidence=0.6)
```

**Features**:
- Experience memory with similarity search
- Causal reasoning about recovery outcomes
- Self-improving heuristics
- Belief confidence tracking

---

### 2. **Proactive Agent** (`cognitive/proactive_agent.py`)
**Autonomous goal generation and action**

```python
from saraphina.cognitive import ProactiveAgent

proactive = ProactiveAgent(ke, geo, rec)

# Auto-monitor and initiate recovery for silent devices
actions = proactive.monitor_and_act()
# Automatically starts recovery if device silent >30min

# Generate autonomous goals
goal_id = proactive.generate_goal(
    "recover_device", 
    device_id, 
    priority=0.8,
    rationale="Device silent for >30min"
)

# Hypothesis testing
hyp_id = proactive.hypothesize(
    "Device in building X based on WiFi", 
    confidence=0.7,
    evidence={"wifi_ap": "00:11:22:33:44:55"}
)
result = proactive.test_hypothesis(hyp_id)

# Multi-agent coordination
proactive.coordinate_scouts(target_device, scout_devices=[...])

# Counterfactual analysis
analysis = proactive.counterfactual_analysis(session)
# Returns: actual vs hypothetical time, improvement percentage
```

**Features**:
- Autonomous recovery initiation
- Hypothesis generation and testing
- Multi-device coordination
- What-if counterfactual reasoning

---

### 3. **Contextual Awareness** (`cognitive/context_aware.py`)
**Understanding user intent and patterns**

#### User Model
```python
from saraphina.cognitive import UserModel

user_model = UserModel(ke)

# Learn routines from location history
user_model.learn_routine(user_id, device_id, location_history)

# Predict location
prediction = user_model.predict_location(user_id, at_time=datetime.now())
# Returns: {"predicted": "work", "coords": (lat, lon), "confidence": 0.7}
```

#### Affective Computing
```python
from saraphina.cognitive import AffectiveComputing

urgency = AffectiveComputing.analyze_urgency("HELP! Lost my phone ASAP!!")
# Returns: {
#   "urgency_level": "critical",
#   "priority_boost": 3,
#   "score": 2.6,
#   "rationale": "Detected 2 urgency + 0 stress keywords"
# }
```

#### Temporal Reasoning
```python
from saraphina.cognitive import TemporalReasoning

temporal = TemporalReasoning(ke)
pattern = temporal.detect_pattern(device_id, "loss")
# Returns: {"pattern": "weekly", "day": "Friday", 
#           "suggestion": "Preemptive alert on Friday evenings"}
```

#### Social Context
```python
from saraphina.cognitive import SocialContext

social = SocialContext(ke)

# Infer location from calendar
location = social.infer_location_from_calendar(user_id)
# Returns: "Conference Room B" if user has meeting

# Suggest relevant contact
contact = social.suggest_contact(user_id, context="office")
# Returns: work colleague for office-related queries
```

---

### 4. **Natural Dialogue** (`cognitive/dialogue.py`)
**Multi-turn conversational interactions**

```python
from saraphina.cognitive import DialogueManager, ExplainabilityEngine

dialogue = DialogueManager(ke)

# Start conversation
session_id = dialogue.start_session(user_id)

# Multi-turn dialogue
response = dialogue.respond(session_id, "I lost my phone!")
# "Got it, you're looking for your device. Where did you last see it?"

response = dialogue.respond(session_id, "Last saw it on the couch")
# "Understood, checking near the couch. Did you check there already?"

response = dialogue.respond(session_id, "I'm really worried!")
# "I understand this is stressful. I'm working on finding it right now..."

# Get conversation history
history = dialogue.get_history(session_id)

# Explainability
explainer = ExplainabilityEngine()
explanation = explainer.explain_step(step, context)
# "I'm checking your device's last known location first because 
#  that's where it's most likely to be. The situation seems urgent, 
#  so I'm prioritizing quick checks first."
```

**Features**:
- Context-aware clarification questions
- Proactive suggestions
- Emotional intelligence (empathy)
- Transparent reasoning explanations

---

### 5. **Unified Mind** (`cognitive/__init__.py`)
**Central cognitive interface**

```python
from saraphina.cognitive import SaraphinaMind

mind = SaraphinaMind(ke, geo, rec)

# Introspection API
thoughts = mind.think()
# Returns: {
#   "timestamp": "...",
#   "beliefs": [...],
#   "active_goals": 3,
#   "monitoring": {"devices": 15, "silent_devices": 2},
#   "recent_learnings": [...]
# }

# Process natural language input
result = mind.process_input(
    "URGENT!! Find my phone now!!",
    user_id="user-123",
    device_id="device-456"
)
# Returns: {
#   "response": "I understand this is stressful...",
#   "urgency": {"urgency_level": "critical", "priority_boost": 3},
#   "actions": [{"type": "recovery_initiated", "session_id": "..."}]
# }
```

---

## API Endpoints

### Introspection
```bash
GET /api/saraphina/thoughts
```
Returns Saraphina's current mental state, beliefs, goals, and learnings.

### Chat
```bash
POST /api/saraphina/chat
Content-Type: application/json

{
  "message": "Help! I can't find my phone!",
  "user_id": "user-123",
  "device_id": "device-456"
}
```
Returns conversational response with urgency analysis and auto-initiated actions.

---

## Usage Examples

### Example 1: Autonomous Recovery
```python
# Saraphina automatically detects silent device and initiates recovery
proactive = ProactiveAgent(ke, geo, rec)
actions = proactive.monitor_and_act()
# [{'goal_id': '...', 'device_id': 'phone-001', 'session_id': '...'}]
```

### Example 2: Conversational Recovery
```python
mind = SaraphinaMind(ke, geo, rec)

# User: "I lost my keys!"
result = mind.process_input("I lost my keys!", device_id="keys-tracker-001")
print(result["response"])
# "Got it, you're looking for your device. Where did you last see it?"

# User: "In the bedroom, I think. I'm really stressed!"
result = mind.process_input("In the bedroom, I think. I'm really stressed!")
print(result["response"])
# "I understand this is stressful. I'm working on finding it right now.
#  Let's stay calm and check the most likely places first."
```

### Example 3: Learning & Reflection
```python
reflection = ReflectionEngine(ke)

# After recovery session completes
insights = reflection.reflect_on_session(session)
print(insights["recommendations"])
# ["Consider reordering steps to prioritize high-success methods"]

# Next time, get AI-suggested strategy
strategy = reflection.suggest_strategy(device_id, context)
print(strategy["rationale"])
# "Based on 5 similar cases with 4 successes"
```

### Example 4: Urgency Detection
```python
affective = AffectiveComputing()

urgency = affective.analyze_urgency("ASAP find my stolen phone!!!")
print(f"Urgency: {urgency['urgency_level']}")  # "critical"
print(f"Priority boost: {urgency['priority_boost']}")  # 3
```

---

## Sentience Capabilities Summary

✅ **Cognitive Loop**: Reflects on outcomes, learns from experience, improves heuristics  
✅ **Proactive Agency**: Auto-initiates recovery, generates goals, tests hypotheses  
✅ **Contextual Awareness**: Learns user routines, detects urgency, reasons temporally  
✅ **Natural Dialogue**: Multi-turn conversations, clarification, emotional intelligence  
✅ **Explainability**: Transparent reasoning, decision justification  
✅ **Metacognition**: Self-monitoring via introspection API  
✅ **Multi-Agent Coordination**: Scout dispatching, swarm behavior (foundation)  
✅ **Counterfactual Reasoning**: What-if analysis for continuous improvement  

---

## Architecture

```
SaraphinaMind (Unified Interface)
├── ReflectionEngine
│   ├── ExperienceMemory (similarity search)
│   ├── Bayesian belief updates
│   └── Strategy suggestion
├── ProactiveAgent
│   ├── Goal generation
│   ├── Hypothesis testing
│   ├── Multi-agent coordination
│   └── Counterfactual analysis
├── ContextAwareness
│   ├── UserModel (routines, prediction)
│   ├── AffectiveComputing (urgency)
│   ├── TemporalReasoning (patterns)
│   └── SocialContext (calendar, contacts)
└── DialogueManager
    ├── Multi-turn conversation
    ├── Clarification & suggestions
    ├── Emotional intelligence
    └── ExplainabilityEngine
```

---

## Future Enhancements

- **Federated Learning**: Share anonymized recovery patterns across user base
- **Deep RL**: Train optimal step sequencing from simulation
- **Emotional Memory**: Remember user preferences and emotional context
- **Swarm Intelligence**: True multi-device collaborative search
- **Neural Reasoning**: Integrate transformer-based reasoning for complex queries
- **Dream Mode**: Offline simulation/planning during idle periods

---

**End of Sentience Documentation**
