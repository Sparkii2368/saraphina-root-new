#!/usr/bin/env python3
"""
Planner - generates executable plans with preconditions and rollback steps
"""
from typing import Dict, Any, List
from datetime import datetime

class Planner:
    def plan(self, goal: str, context: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            "analyze_goal",
            "gather_requirements",
            "design_solution",
            "implement_changes",
            "test_and_validate",
            "deploy_and_monitor"
        ]
        preconditions = ["access_ok", "permissions_ok", "backups_ready"]
        rollback = ["revert_changes", "restore_backup", "verify_stability"]

        # Confidence heuristic: start at 0.8 and reduce with constraints complexity
        complexity_penalty = 0.0
        if constraints:
            complexity_penalty = min(0.3, 0.05 * len(constraints))
        confidence = max(0.4, 0.8 - complexity_penalty)

        return {
            "goal": goal,
            "generated_at": datetime.utcnow().isoformat(),
            "steps": steps,
            "preconditions": preconditions,
            "rollback": rollback,
            "confidence": confidence,
        }

    def simulate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        # Naive simulation: success probability based on step count and confidence
        steps = plan.get("steps", [])
        confidence = float(plan.get("confidence", 0.5))
        success_probability = max(0.2, min(0.95, confidence - 0.02 * max(0, len(steps) - 4)))
        return {
            "success_probability": success_probability,
            "risks": ["unknowns", "resource_constraints"],
            "notes": "Simulation is heuristic-only"
        }
