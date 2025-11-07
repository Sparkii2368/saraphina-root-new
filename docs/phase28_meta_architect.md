# Phase 28: MetaArchitect - Architectural Redesign

**Goal**: Saraphina learns to redesign her own architecture, not just patch code.

## Components

### MetaArchitect (saraphina/meta_architect.py)
- **analyze_module(module_name)**: AST-based analysis → lines, functions, classes, imports, complexity (McCabe), coupling
- **propose_refactor(module, type)**: GPT-4o generates architectural proposals
  - Types: microservice, abstraction, pattern, auto
  - Returns: JSON with title, rationale, proposed_design (approach, components, benefits, risks), risk_score, complexity_score, estimated_effort_hours
- **list_analyzable_modules()**: scans saraphina/ for .py files

### SimulationSandbox (saraphina/simulation_sandbox.py)
- **simulate_refactor(proposal_id, proposed_design)**:
  1. Clone codebase to temp sandbox (shutil.copytree)
  2. Apply refactor (stub: validates proposal structure; real: would generate code)
  3. Run tests (pytest if available)
  4. Measure metrics: coupling, complexity, modularity before/after
  5. Calculate improvement score
- Returns: success, tests_passed/failed, metrics_before/after, improvement (overall_score, coupling_reduction, complexity_reduction, modularity_improved)

### ArchitectureDB (saraphina/architecture_db.py)
- **architecture_proposals table**: id, type, scope, title, rationale, proposed_design (JSON), simulation_results (JSON), status (pending→simulated→promoted), risk_score, complexity_score, estimated_effort_hours
- Methods: create_proposal, update_simulation, set_status, get_proposal, list_proposals

## Commands

- **/propose-architecture \<module\> [type]**: Analyze module, generate architectural proposal via GPT-4o, store in DB
- **/simulate-arch \<id\>**: Clone codebase, apply refactor, run tests, measure metrics, update DB
- **/promote-arch \<id\>**: Mark architecture as approved for implementation (requires simulation success)
- **/list-architectures [status]**: List proposals with status filter

## Acceptance Test

**Example: KnowledgeEngine micro-service split**

1. Propose refactor:
   ```
   /propose-architecture knowledge_engine microservice
   ```
   - GPT-4o analyzes: 173 lines, KnowledgeEngine class, 10 imports, complexity 17.3
   - Proposes: split into `knowledge_store` (CRUD), `knowledge_query` (recall), `knowledge_graph` (links)
   - Output: proposal ID `arch_20251105_131701`

2. Simulate:
   ```
   /simulate-arch arch_20251105_131701
   ```
   - Clones saraphina/ to temp sandbox
   - Validates proposed_design structure
   - Measures metrics before/after (stub: no actual code generation yet)
   - Records: coupling reduction, complexity reduction, modularity improvement
   - Status → simulated

3. Promote:
   ```
   /promote-arch arch_20251105_131701
   ```
   - Confirms simulation success
   - Marks status → promoted
   - Suggests next steps: use /propose-code to generate modules, test, apply

## Design Philosophy

- **Analyze-Propose-Simulate-Promote**: structured workflow with safety gates
- **Metrics-driven**: quantify coupling, complexity, modularity improvements
- **Sandbox isolation**: test architectural changes in temp environment without affecting production
- **GPT-4o augmented**: leverage LLM for high-level design reasoning
- **Future**: integrate with CodeFactory to auto-generate refactored code from proposed_design

## Future Enhancements

- Auto-generate code for promoted architectures (parse proposed_design.components, create stubs, refactor references)
- Docker/containerized simulation for full integration tests
- Visual architecture diagrams (PlantUML/Mermaid generation)
- Continuous architectural health monitoring (trigger proposals when coupling/complexity thresholds exceeded)
