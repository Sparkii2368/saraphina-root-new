#!/usr/bin/env python3
"""
Simple Planner prototype.

- Plans are small, inspectable step lists.
- Keeps an in-memory plan store so UI / CLI can reference a generated plan_id.
- Integrates with adapters at a high level (adapter chosen by step.adapter key).
"""

from __future__ import annotations

import uuid
import time
from typing import Dict, Any, List, Optional

from risk_model import RiskModel  # local small risk model
from system_adapters import SystemAdapter, NetworkAdapter, WiFiAdapter, BluetoothAdapter  # noqa: F401


class Planner:
    def __init__(self, core: Optional[Any] = None):
        self.core = core
        self._plans: Dict[str, Dict[str, Any]] = {}
        self.risk_model = RiskModel()

    def plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a simple plan for a textual goal.
        This is intentionally conservative and returns a human-reviewable plan.
        """
        context = context or {}
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        steps: List[Dict[str, Any]] = []

        g = goal.lower()
        if "light" in g or "lights" in g:
            steps = [
                {"id": "discover_lights", "adapter": "network", "action": {"command": "discover_lights"}},
                {"id": "identify_device", "adapter": "network", "action": {"command": "identify", "predicate": "bedroom"}},
                {"id": "send_command", "adapter": "network", "action": {"command": "on", "device_hint": "bedroom_light"}},
                {"id": "verify", "adapter": "network", "action": {"command": "verify_state", "expected": "on"}},
            ]
        elif "wifi" in g or "connect" in g:
            steps = [
                {"id": "scan_wifi", "adapter": "wifi", "action": {"command": "scan"}},
                {"id": "connect", "adapter": "wifi", "action": {"command": "connect", "ssid": context.get("ssid")}},
            ]
        else:
            # Default: a safe probe plan
            steps = [
                {"id": "probe", "adapter": "network", "action": {"command": "probe", "goal": goal}}
            ]

        risk = self.risk_model.assess(steps)
        rollback = self._generate_rollback(steps)

        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "context": context,
            "created_at": time.time(),
            "steps": steps,
            "risk": risk,
            "rollback": rollback,
            "status": "created",
        }

        self._plans[plan_id] = plan
        return plan

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        return self._plans.get(plan_id)

    def dryrun(self, plan_id: str, adapters: Dict[str, SystemAdapter]) -> Dict[str, Any]:
        plan = self.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "plan not found"}
        reports = []
        for s in plan["steps"]:
            adapter_name = s.get("adapter")
            adapter = adapters.get(adapter_name) if adapters else None
            if adapter:
                reports.append({"step": s["id"], "dryrun": adapter.dryrun(s["action"])})
            else:
                reports.append({"step": s["id"], "dryrun": f"No adapter '{adapter_name}' available"})
        return {"success": True, "reports": reports}

    def execute(self, plan_id: str, adapters: Dict[str, SystemAdapter]) -> Dict[str, Any]:
        """
        Execute steps sequentially using provided adapters.
        Returns aggregated result; operations are conservative — failures stop the plan.
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "plan not found"}

        results = []
        for s in plan["steps"]:
            adapter_name = s.get("adapter")
            adapter = adapters.get(adapter_name)
            if not adapter:
                results.append({"step": s["id"], "success": False, "error": f"Adapter '{adapter_name}' missing"})
                plan["status"] = "failed"
                break
            res = adapter.execute(s["action"])
            results.append({"step": s["id"], "result": res})
            if not res.get("success"):
                plan["status"] = "failed"
                break
        else:
            plan["status"] = "completed"

        plan["last_run_at"] = time.time()
        plan["last_results"] = results
        return {"success": plan["status"] == "completed", "plan": plan, "results": results}

    def _generate_rollback(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Basic conservative rollback: reverse send_command -> send inverse
        rollback = []
        for s in reversed(steps):
            if s["action"].get("command") == "on":
                rb = {"step_id": s["id"], "action": {"command": "off", "device_hint": s["action"].get("device_hint")}, "adapter": s["adapter"]}
                rollback.append(rb)
        return rollback