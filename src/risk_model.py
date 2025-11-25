#!/usr/bin/env python3
"""
Universal Risk Model for Saraphina (Phase 5)
Merged & Upgraded: Handles both "Code Analysis" (Self-Mod) and "Action Planning" (Agent).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Risk:
    category: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str

class RiskModel:
    """
    Static analysis engine to assess risks in code or actions.
    """
    
    # Code Analysis Keywords
    CRITICAL_CODE_KEYWORDS = ["os.system", "subprocess.call", "eval(", "exec(", "shutil.rmtree", "format_drive"]
    HIGH_RISK_CODE_KEYWORDS = ["upload_user_data", "export_private_key", "disable_safety", "firewall_off"]
    
    # Action Planner Keywords
    SENSITIVE_COMMANDS = {"factory_reset", "delete", "format", "reboot", "flash_firmware"}

    # --- 1. Code Assessment (Used by Self-Modification Engine) ---
    @staticmethod
    def assess_code(code: str) -> List[Risk]:
        risks = []
        code_lower = code.lower()
        
        # Check for dangerous system calls
        for kw in RiskModel.CRITICAL_CODE_KEYWORDS:
            if kw in code_lower:
                risks.append(Risk(
                    category="SECURITY",
                    severity="CRITICAL",
                    description=f"Detected potentially unsafe system call: {kw}"
                ))

        # Check for privacy/safety violations
        for kw in RiskModel.HIGH_RISK_CODE_KEYWORDS:
            if kw in code_lower:
                risks.append(Risk(
                    category="PRIVACY_SAFETY",
                    severity="HIGH",
                    description=f"Potential safety violation detected: {kw}"
                ))

        return risks

    # --- 2. Action Assessment (Used by Planner/Agent) ---
    @staticmethod
    def assess(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Return a small risk descriptor:
        - level: "low" | "medium" | "high"
        - reasons: list[str]
        """
        reasons = []
        score = 0.0
        for s in steps:
            cmd = str(s.get("action", {}).get("command", "")).lower()
            if cmd in RiskModel.SENSITIVE_COMMANDS:
                reasons.append(f"sensitive command: {cmd}")
                score += 3.0
            if s.get("adapter") == "network" and cmd in ("on", "off", "send"):
                score += 0.3
            if s.get("adapter") == "wifi" and cmd == "connect":
                score += 0.5

        level = "low"
        if score >= 3.0:
            level = "high"
        elif score >= 1.0:
            level = "medium"
            
        return {"level": level, "score": score, "reasons": reasons}

    # --- 3. Unified Check ---
    @staticmethod
    def is_safe(risks: List[Risk]) -> bool:
        """Returns False if any CRITICAL or HIGH risks are present."""
        return not any(r.severity in ["CRITICAL", "HIGH"] for r in risks)