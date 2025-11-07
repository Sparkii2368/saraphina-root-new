# Phase 27: Continuous Improvement Loop

Goal
- Saraphina continuously proposes, tests, and integrates improvements.

Components
- ImprovementLoop (saraphina/improvement_loop.py)
  - run_once(): detect slow recall, propose SQL index patch, sandbox-test, auto-apply per policy
  - apply_patch(id): apply approved patch and audit
- AutoPatch
  - sample_recent_queries(), measure_recall_ms()
  - generate_index_patch(): propose indexes for facts and fact_aliases
  - test_index_patch_in_sandbox(): clone DB, apply SQL, measure gain
- ApprovalPolicy
  - Stored in preferences (keys: improve.auto_approve, improve.slow_ms, improve.min_gain_pct, improve.risk_threshold)
  - should_auto_approve(risk, gain_pct)
- ImprovementDB (saraphina/improvement_db.py)
  - improvement_patches table with status lifecycle: pending → approved → applied/failed

Commands
- /improve: run loop once; may create and apply a patch automatically
- /set-policy <k> <v>: update policy keys
- /review-patches: list and approve/apply patches

Acceptance Example
- Set policy to auto-approve safe patches:
  /set-policy auto_approve true
- Trigger improvement:
  /improve
  If recall avg > threshold (default 150ms), Saraphina proposes indexes:
    - CREATE INDEX IF NOT EXISTS idx_facts_conf_updated ON facts(confidence, updated_at)
    - CREATE INDEX IF NOT EXISTS idx_fact_aliases_alias ON fact_aliases(alias)
  It sandbox-tests, estimates gain, and auto-applies if gain >= min_gain_pct and low risk.
- Review status:
  /review-patches

Notes
- Safe by design: only SQL index patches are auto-applied.
- Future: extend AutoPatch to code refactors using CodeFactory and TestHarness.
