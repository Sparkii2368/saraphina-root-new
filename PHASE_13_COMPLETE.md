# Phase 13: Knowledge Graph & Intuition Layer - COMPLETE ✅

## Implementation Status

Phase 13 has been **fully implemented** with a strong focus on **natural language interaction**. Saraphina can now visualize her knowledge graph and surface non-obvious insights conversationally.

## Core Components

### 1. KnowledgeGraphExplorer (`saraphina/knowledge_graph.py`)
Advanced graph analysis engine that discovers insights using multiple algorithms:

**Features**:
- **PageRank Analysis**: Identifies important nodes in the knowledge graph
- **Semantic Similarity**: Finds concepts with shared terminology despite no direct links
- **Path Discovery**: Uses BFS to find shortest paths between concepts
- **Topic Bridges**: Detects cross-domain connections between different knowledge areas
- **Natural Explanations**: Generates human-readable insight descriptions

**Algorithms**:
```python
# PageRank for centrality
pagerank(graph, iterations=20, damping=0.85)

# Shortest path (BFS)
find_shortest_path(graph, start, end)

# Insight discovery with multi-strategy approach
discover_insights(query=None, limit=5)
```

### 2. Enhanced IntuitionEngine (`saraphina/intuition.py`)
Existing intuition engine now works alongside the graph explorer:
- Lexical overlap detection
- Topic-based filtering
- Graph centrality weighting

### 3. Visual Dashboard (`dashboard/index.html`)
Interactive D3.js force-directed graph visualization:
- Color-coded by topic
- Draggable nodes
- Real-time updates via API
- Shows "Knowledge Constellations"

## Natural Language Interaction

**You asked for natural language, not commands - here it is:**

### Discovering Insights

Just talk naturally! Saraphina understands these patterns:

```
"What patterns do you see?"
"Any insights about Docker?"
"Show me some connections"
"What have you noticed?"
"Find some patterns"
"Discover relationships in my knowledge"
```

### Exploring Specific Connections

```
"How do Python and Docker relate?"
"What connects Kubernetes and security?"
"How does React relate to Redux?"
"What's the relationship between AWS and Azure?"
```

### Topic-Specific Discovery

```
"Any insights about programming?"
"What patterns do you see in DevOps?"
"Show me connections about cloud computing"
"Insights regarding security"
```

## Command Reference

### `/insight` Command
Discover non-obvious patterns in your knowledge graph.

**Usage**:
```bash
/insight                    # General insights
/insight Python             # Insights about Python
/insight cloud computing    # Topic-specific insights
```

**Output Example**:
```
💡 Non-obvious insights from your knowledge graph:

1. I'm sensing a connection between 'Docker containers' and 'Kubernetes orchestration'. 
   Both involve container, deployment, scaling. This could be a key insight since 
   both are central to the knowledge graph.
   Topics: devops ↔ cloud
   Confidence: 78.5%
   Shared: container, deploy, scale

2. Here's an interesting pattern: programming and security intersect around 
   authentication, encryption, validation.
   Topics: programming ↔ security  
   Confidence: 65.2%
   Shared: auth, encrypt, validate
```

## Natural Language Examples

### Example 1: General Pattern Discovery
```
You: What patterns do you see?

Saraphina: 💡 Here's what I'm noticing:

1. I notice 'JWT authentication' relates to 'OAuth 2.0 flows' through token, 
   security, validation. There's an indirect path through 2 intermediate concept(s). 
   This could be a key insight since both are central to the knowledge graph.
   (security ↔ programming, confidence: 82.3%)

2. I notice a bridge between devops and cloud. They share concepts like: container, 
   docker, kubernetes. This cross-domain connection might reveal a transferable pattern.
   (devops ↔ cloud, confidence: 75.0%)
```

### Example 2: Specific Connection Query
```
You: How do Docker and Kubernetes relate?

Saraphina: 🔗 Connection between 'Docker container runtime' and 'Kubernetes orchestration':
   Shared concepts: container, pod, deploy, image
   Semantic similarity: 67.34%
   Path (3 steps): Docker → containerization → orchestration → Kubernetes
```

### Example 3: Topic-Specific Insights
```
You: Any insights about Python?

Saraphina: 💡 Here's what I'm noticing:

1. These two concepts share common ground in function, decorator, async, even though 
   they seem unrelated at first.
   (programming ↔ web, confidence: 68.9%)
```

### Example 4: First-Time Usage (Empty Graph)
```
You: Show me some connections

Saraphina: 🔮 I haven't spotted strong patterns yet.
   As I learn more facts and connections, insights will emerge.
   Try adding more knowledge with 'remember that...' or /factadd
```

## Integration Points

### UltraSession Enhancement
```python
class UltraSession:
    def __init__(self):
        # ... existing components ...
        self.graph_explorer = KnowledgeGraphExplorer(self.ke.conn)
```

### Natural Language Handler
Enhanced `_handle_nl_command()` with intelligent pattern matching:

```python
# Detects patterns like:
if any(k in t for k in ['insight','hunch','connection','pattern','relate']):
    # Routes to appropriate handler
    
# Specific connections: "what connects X and Y"
m2 = re.search(r"(?:connects?|relat).*?\s+(.+?)\s+(?:and|to|with)\s+(.+?)(?:\?|$)", t)

# General discovery: "what patterns", "any insights"  
if any(p in t for p in ['any insight', 'show insight', 'what pattern', ...]):
```

### Voice Integration
All insight responses work with voice synthesis:
- Natural language explanations spoken aloud
- Multi-insight responses with pauses
- Confidence levels included in speech

## Technical Details

### Graph Building
```python
def build_graph(topic=None, limit=500):
    # Fetch facts, links, and query history
    # Calculate:
    # - Node degrees (connectivity)
    # - Query frequency (importance)
    # - Topic distribution
    # Returns: {nodes, edges, stats}
```

### PageRank Implementation
```python
def pagerank(graph, iterations=20, damping=0.85):
    # Iterative PageRank with damping factor
    # Identifies central/important concepts
    # Higher scores = more connected/referenced
```

### Insight Discovery Strategy

**Multi-Algorithm Approach**:

1. **High PageRank + Semantic Overlap**
   - Find top 20 most important nodes
   - Check pairwise semantic similarity
   - Filter for ≥2 shared concepts
   - Calculate indirect paths

2. **Topic Bridges**
   - Detect cross-topic connections
   - Identify transferable patterns
   - Highlight domain intersections

3. **Confidence Scoring**
   ```python
   confidence = (pr1 + pr2) * 10           # Importance
              + min(overlap * 0.15, 0.5)   # Semantic bonus
              - path_penalty               # Spurious link penalty
   ```

### Path Analysis
```python
def find_shortest_path(graph, start, end):
    # Breadth-First Search (BFS)
    # Returns: [node1, node2, ..., nodeN]
    # Used to explain indirect relationships
```

## Dashboard Visualization

Open the interactive graph explorer:
```bash
/dashboard open
```

**Features**:
- Force-directed layout (D3.js)
- Color-coded by topic domain
- Drag nodes to explore
- Hover for labels
- Auto-refresh every 5 seconds
- Shows up to 300 most recent facts

## Database Schema

Uses existing tables:
- `facts` - Knowledge nodes
- `concept_links` - Explicit relationships
- `queries` - Usage patterns for importance weighting
- `fact_vectors` - (Future) Semantic embeddings

No new tables required! ✅

## Acceptance Criteria

- [x] **KnowledgeGraphExplorer**: Built with PageRank, path finding, and semantic analysis
- [x] **IntuitionEngine**: Enhanced and integrated alongside new explorer
- [x] **Natural Language**: Conversational insight discovery without /commands
- [x] **Novel Connections**: Returns insights between unrelated facts with explanations
- [x] **Visual Explorer**: Interactive D3.js graph in dashboard
- [x] **Multiple Strategies**: PageRank, topic bridges, semantic overlap
- [x] **Confidence Scores**: Each insight rated 0-100%
- [x] **Path Explanations**: Shows indirect connections when relevant

## Usage Examples

### Adding Knowledge
First, build up your knowledge graph:
```bash
# Via natural language
You: remember that Docker uses container technology for isolation
You: remember that Kubernetes orchestrates containers at scale
You: remember that Helm manages Kubernetes deployments

# Via command
/factadd
Topic: devops
Summary: Docker containerization
Content: Docker packages apps with dependencies in containers
Source: experience
Confidence: 0.9
```

### Discovering Insights

**Natural Language (Recommended)**:
```bash
You: What patterns have you noticed?
You: Any insights about DevOps?
You: How do Docker and Kubernetes connect?
You: Show me some interesting connections
```

**Command Alternative**:
```bash
/insight                    # All insights
/insight DevOps             # Topic-specific
```

### Visual Exploration
```bash
/dashboard open             # Opens interactive graph
```

## Performance

- **Graph Build**: O(n + m) where n=nodes, m=edges
- **PageRank**: O(k*n²) where k=iterations (default 20)
- **Path Finding**: O(n + m) BFS traversal
- **Insight Discovery**: O(n²) for pairwise comparison (limited to top 20 by PageRank)

**Optimization**: Only top-ranked nodes compared to keep complexity manageable.

## Natural Language Patterns Recognized

The system understands these conversational patterns:

**Pattern Discovery**:
- "what patterns"
- "see pattern"
- "find pattern"
- "discover"
- "any insight"
- "show insight"

**Relationship Queries**:
- "connects X and Y"
- "relate X to Y"
- "relationship between X and Y"
- "how do X and Y relate"
- "what connects X with Y"

**Topic Filtering**:
- "about {topic}"
- "on {topic}"
- "regarding {topic}"
- "for {topic}"

## Example Session

```bash
$ python saraphina_terminal_ultra.py

🌟 SARAPHINA ULTRA AI TERMINAL 🌟

You: remember that React is a JavaScript UI library
Saraphina: Okay, I've remembered that. (id fact_abc123)

You: remember that Redux manages application state
Saraphina: Okay, I've remembered that. (id fact_def456)

You: remember that both React and Redux use JavaScript
Saraphina: Okay, I've remembered that. (id fact_ghi789)

You: What patterns do you see?

Saraphina: 💡 Here's what I'm noticing:

1. I'm sensing a connection between 'React is a JavaScript UI library' 
   and 'Redux manages application state'. Both involve javascript, state, library.
   (programming ↔ programming, confidence: 71.2%)

You: How do React and Redux relate?

Saraphina: 🔗 Connection between 'React is a JavaScript UI library' and 
           'Redux manages application state':
   Shared concepts: javascript, state, application
   Semantic similarity: 42.86%
   ✓ Directly connected in knowledge graph

You: /dashboard open

Saraphina: 🧭 Dashboard opened in your browser.
```

## Tips

1. **Build Knowledge First**: Insights emerge from data. Add facts naturally:
   - "remember that X"
   - Use /factadd for structured input

2. **Natural Language Works Better**: Instead of `/insight`, just ask:
   - "What do you notice?"
   - "Any patterns?"
   - "Show me connections"

3. **Topic Filtering**: Be specific to get focused insights:
   - "Insights about Python"
   - "Patterns in cloud computing"

4. **Visual Exploration**: Use the dashboard for interactive discovery:
   - `/dashboard open`
   - Drag nodes to reorganize
   - Color = topic domain

5. **Iterate**: As you add more facts, patterns become clearer
   - Start small
   - Build connections organically
   - Let Saraphina discover the relationships

## Architecture

```
Natural Language Input
         ↓
_handle_nl_command()
         ↓
    Pattern Match:
    - "what patterns"
    - "connects X and Y"  
    - "insights about"
         ↓
KnowledgeGraphExplorer
         ↓
    ┌─────────┬──────────┬─────────┐
    │PageRank │ Semantic │  Path   │
    │Analysis │ Overlap  │ Finding │
    └─────────┴──────────┴─────────┘
         ↓
  Insight Generation
         ↓
Natural Language Explanation
         ↓
    Voice Synthesis (optional)
```

## Next Steps

With Phase 13 complete, Saraphina now has:
- ✅ Visual knowledge graph
- ✅ Natural language insight discovery
- ✅ Multi-algorithm pattern detection
- ✅ Conversational interface (no commands needed)

Consider:
- **Phase 14+**: Additional advanced capabilities
- **Embeddings**: Add vector-based similarity (fact_vectors table ready)
- **Auto-linking**: Automatically create concept_links from semantic analysis
- **Community Detection**: Find clusters of related concepts
- **Temporal Analysis**: Track how insights evolve over time

---

**Phase 13 Status**: ✅ COMPLETE AND OPERATIONAL  
**Natural Language**: ✅ FULLY CONVERSATIONAL  
**Commands Required**: ❌ OPTIONAL (natural language preferred)  
**Date**: 2024  
**Documentation**: Complete
