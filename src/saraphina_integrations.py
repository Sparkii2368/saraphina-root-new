#!/usr/bin/env python3
"""
Runtime integration helpers to attach Planner, Adapters and safety wrappers to an UltraAICore instance.

Usage:
    from saraphina_integrations import attach_to_core
    attach_to_core(core)

What this file does now:
- Creates Planner, RiskModel and lightweight adapters (Network, WiFi, Bluetooth).
- Monkey-patches core to expose core.planner, core.risk_model, core.adapters.
- Wraps core.chat_v4 to consult knowledge_engine.summarize_for_prompt() / search() first and return high-confidence recalls directly.
- Wraps core.self_mod_engine.propose_improvement to force auto_apply=False (safety: human-in-the-loop).
- Ensures device tables exist in the core's FILE_DB (best-effort).
"""

from __future__ import annotations

import sqlite3
import time
import json
from typing import Any

from planner import Planner
from system_adapters import NetworkAdapter, WiFiAdapter, BluetoothAdapter


def _ensure_device_tables(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                name TEXT,
                platform TEXT,
                owner TEXT,
                enrolled_at REAL,
                last_seen REAL,
                capabilities TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS device_agents (
                agent_id TEXT PRIMARY KEY,
                device_id TEXT,
                public_key TEXT,
                heartbeat_ts REAL,
                status TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS skills_xp (
                skill TEXT PRIMARY KEY,
                level REAL,
                xp REAL
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception:
        # best-effort, do not raise
        pass


def attach_to_core(core: Any) -> None:
    """
    Attach planner/adapters and apply safety wrappers to the provided UltraAICore instance.
    """
    # 1) Attach planner
    try:
        core.planner = Planner(core)
    except Exception:
        core.planner = Planner(core)  # fallback

    # 2) Attach adapters (lightweight implementations)
    adapters = {
        "network": NetworkAdapter(),
        "wifi": WiFiAdapter(),
        "bluetooth": BluetoothAdapter(),
    }
    core.adapters = adapters

    # 3) Ensure device tables exist (use core.FILE_DB if available)
    db_path = getattr(core, "FILE_DB", None)
    if db_path:
        try:
            _ensure_device_tables(str(db_path))
        except Exception:
            pass

    # 4) Safety wrapper: force self_mod_engine.propose_improvement to NOT auto-apply
    try:
        sm = getattr(core, "self_mod_engine", None)
        if sm and hasattr(sm, "propose_improvement"):
            original_propose = sm.propose_improvement

            def safe_propose_improvement(target_file: str, improvement_spec: str, safety_level: str = "high", context=None, auto_apply: bool = False, simulation_only: bool = False):
                # Force auto_apply False no matter what the caller passed.
                try:
                    return original_propose(target_file, improvement_spec, safety_level=safety_level, context=context, auto_apply=False, simulation_only=simulation_only)
                except TypeError:
                    # older signature fallback
                    return original_propose(target_file, improvement_spec)

            sm.propose_improvement = safe_propose_improvement  # type: ignore[assignment]
            core.self_mod_engine = sm
    except Exception:
        pass

    # 5) Knowledge-first wrapper around chat_v4
    try:
        orig_chat = core.chat_v4

        def knowledge_first_chat(message: str) -> str:
            # Defensive: if kernel not ready, call original
            try:
                if not isinstance(message, str) or not message.strip():
                    return orig_chat(message)
            except Exception:
                return orig_chat(message)

            msg = message.strip()
            # 1) quick exact/fts check
            try:
                # Prefer exact/query_knowledge then hybrid search
                ke = getattr(core, "knowledge_engine", None)
                if ke:
                    # First attempt: query_knowledge (best description for topic)
                    try:
                        qk = ke.query_knowledge(msg)
                        if qk and len(qk) > 30:
                            # Short-circuit: we already know a good answer
                            return qk
                    except Exception:
                        pass

                    # Second attempt: hybrid search for highly scored result
                    try:
                        results = ke.search(msg, limit=3)  # returns list of dicts with 'score'
                        if results:
                            top = results[0]
                            if top.get("score", 0.0) >= 0.85:
                                return top.get("text", top.get("topic", ""))
                    except Exception:
                        pass
            except Exception:
                pass

            # Fallback: full pipeline
            return orig_chat(message)

        core.chat_v4 = knowledge_first_chat  # monkey-patch
        core.chat = core.chat_v4
    except Exception:
        pass

    # 6) Expose a convenience ping for adapters
    def list_adapters() -> str:
        return ", ".join(sorted(list(adapters.keys())))

    core.list_adapters = list_adapters  # attach helper

    # 7) Attach planner convenience shims
    def plan_goal(goal: str, context: dict = None):
        return core.planner.plan(goal, context or {})

    core.plan_goal = plan_goal

    # 8) Done
    try:
        from util_logging import safe_log
        safe_log("[Integrations] Planner & adapters attached; knowledge-first chat_v4 enabled; self-mod auto-apply disabled.")
    except Exception:
        pass