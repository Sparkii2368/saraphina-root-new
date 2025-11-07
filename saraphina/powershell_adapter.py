#!/usr/bin/env python3
"""
PowerShell adapter (dry-run) for demonstration.
- discover(): returns mock LAN/Bluetooth/Wi-Fi candidates
- dryrun(): returns PowerShell commands that would be executed
- execute()/revert(): simulated no-op
"""
from typing import Any, Dict, List
from datetime import datetime

from .system_adapter import SystemAdapter

class PowerShellAdapter(SystemAdapter):
    def discover(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        return [
            {"id": "lan:PC-Alpha", "type": "LAN", "last_seen": now},
            {"id": "bt:Headset-1234", "type": "Bluetooth", "last_seen": now},
            {"id": "wifi:Pi-Lab", "type": "Wi-Fi", "last_seen": now},
        ]

    def dryrun(self, action_descriptor: Dict[str, Any]) -> List[str]:
        action = action_descriptor.get('action', 'unknown')
        target = action_descriptor.get('target', '')
        if action == 'ping':
            return [f"Test-Connection -ComputerName {target} -Count 2"]
        if action == 'service_restart':
            svc = action_descriptor.get('service', 'Spooler')
            return [f"Restart-Service -Name {svc} -Force"]
        if action == 'process_list':
            return ["Get-Process | Select-Object Name, Id, CPU | Sort-Object CPU -Descending | Select-Object -First 10"]
        return [f"# Unknown action: {action}"]

    def execute(self, action_descriptor: Dict[str, Any]) -> Dict[str, Any]:
        # Simulated only
        return {"ok": True, "executed": False, "note": "dry-run only"}

    def revert(self, action_id: str) -> Dict[str, Any]:
        return {"ok": True, "reverted": False}
