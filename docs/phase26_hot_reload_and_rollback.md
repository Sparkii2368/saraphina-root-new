# Phase 26: Hot-Reload & Rollback

Status: In Progress → Implemented core features (HotReloadManager + RollbackEngine + CLI commands)

Goal
- Apply safe code edits to Saraphina while running, without restart
- Auto-rollback to last stable version on errors

Components
- HotReloadManager (saraphina/hot_reload_manager.py)
  - can_hot_reload(module): pre-flight checks (module loaded, no C-extensions, dependency scan, active refs)
  - hot_reload_module(module, test_after_reload=True): importlib.reload + basic health tests + history
  - reload_dependencies(module): cascade reloading of dependents
  - get_reload_history(limit=10): recent attempts (success/failure, hashes, timings)
- RollbackEngine (saraphina/rollback_engine.py)
  - create_checkpoint(module, path, reason): snapshot file to versions_dir, log JSON entry
  - mark_stable(version_id): mark checkpoint stable after successful reload
  - get_last_stable_version(module): find most recent stable
  - rollback_to_version(version_id): restore snapshot, record pre-rollback backup
  - auto_rollback_on_error(module, error): convenience wrapper
  - get_version_history(module=None, limit=20), get_rollback_points(), cleanup_old_versions()

Integration
- UltraSession (saraphina_terminal_ultra.py)
  - self.hot_reload = HotReloadManager(Path("saraphina"))
  - self.rollback  = RollbackEngine(Path("saraphina/backups/hot_reload"))
  - New commands:
    - /apply-code <id>
      - Confirms target module (default: knowledge_engine)
      - Creates checkpoint → writes code (append/replace) → hot-reloads
      - Marks version stable on success; auto-rollback on failure
    - /rollback <version_id>
      - Restores a specific checkpoint and hot-reloads module
      - With no args: lists rollback points
    - /audit-code [module]
      - Shows version history and hot-reload history

Safety & Behavior
- Pre-flight: refuses C-extension modules and unloaded modules
- Version tracking via SHA256 of module source
- Post-reload validation: exports presence, class existence, callable check
- Automatic rollback path on failure with re-reload of prior version

Usage
1) Generate and test code (Phase 23+24)
   - /propose-code <feature>
   - /sandbox-code <proposal_id>
   - /approve-code <proposal_id>
2) Apply live with hot-reload
   - /apply-code <proposal_id>
   - Choose target module (default knowledge_engine)
   - Choose write mode (append/replace) → confirm → live reload
3) Inspect and manage
   - /audit-code [module]
   - /rollback <version_id>

Acceptance Test (example)
- Patch KnowledgeEngine live with a small helper and verify reload passes:
  - /propose-code "Add helper function ke_status() returning 'ok'"
  - /sandbox-code proposal_abc123 → ensure tests pass
  - /approve-code proposal_abc123
  - /apply-code proposal_abc123 → target module: knowledge_engine, mode: append
  - Call ke_status() in-session (or rely on HotReloadManager health check)
  - /audit-code knowledge_engine shows successful reload with new hash

Notes
- If the target module is not already loaded, hot-reload will refuse; import it first by using the session features that reference it (UltraSession does this for knowledge_engine).
- Append mode is safer for incremental helpers; replace mode should be used only for full-file updates.
- For complex multi-file changes, apply changes per-file with checkpoints and use reload_dependencies().

Next Steps
- Natural language triggers (e.g., "apply code changes live", "rollback changes") → guide to commands
- Automated selection of target module from proposal context (e.g., prompt annotations)
- Smoke-test suite per module (customizable) to enhance post-reload validation
- CI hooks for persistent version logs and rollback artifacts
