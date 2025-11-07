#!/usr/bin/env python3
"""
RiskModel - classifies action risk level with heuristic rules
"""
from typing import Dict, Any, List

class RiskModel:
    SENSITIVE_KEYWORDS = [
        "delete", "format", "drop table", "shutdown", "reboot", "privilege",
        "admin", "root", "token", "secret", "key", "firewall", "registry"
    ]
    CAUTION_KEYWORDS = [
        "install", "write", "open port", "change config", "restart", "network"
    ]

    def assess(self, action: str) -> Dict[str, Any]:
        a = action.lower()
        reasons: List[str] = []
        level = "safe"
        if any(k in a for k in self.SENSITIVE_KEYWORDS):
            level = "sensitive"
            reasons.append("contains_sensitive_keyword")
        elif any(k in a for k in self.CAUTION_KEYWORDS):
            level = "caution"
            reasons.append("contains_caution_keyword")
        return {"level": level, "reasons": reasons}
