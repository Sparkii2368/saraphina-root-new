#!/usr/bin/env python3
"""
System adapters: abstract base + light, safe stubs for Bluetooth, WiFi and Network adapters.

Purpose:
- Provide a simple, safe interface that the Planner and UltraAICore can call.
- These are minimal, dependency-light implementations suitable for local testing
  and progressive enhancement (plug in bleak, nmcli, router APIs later).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import platform
import subprocess
import time


class SystemAdapter(ABC):
    """Abstract interface for adapters that can discover devices and execute actions."""

    @abstractmethod
    def discover(self) -> List[Dict[str, Any]]:
        """Discover devices / capabilities and return a list of metadata dicts."""
        raise NotImplementedError

    @abstractmethod
    def dryrun(self, action: Dict[str, Any]) -> str:
        """Return a textual description of what would be executed."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action and return a result dict (success, details)."""
        raise NotImplementedError


# ------------------------------
# Bluetooth adapter (light stub)
# ------------------------------
class BluetoothAdapter(SystemAdapter):
    def __init__(self, backend: Optional[str] = None):
        # backend hint: "bleak", "pybluez", or None for stub
        self.backend = backend

    def discover(self) -> List[Dict[str, Any]]:
        # Best-effort: try to use bleak if installed (non-blocking)
        try:
            if self.backend == "bleak":
                from bleak import BleakScanner  # type: ignore
                devices = BleakScanner.discover(timeout=3.0)
                return [{"id": d.address, "name": d.name or "BLE", "rssi": getattr(d, "rssi", None)} for d in devices]
        except Exception:
            pass

        # Fallback: empty list (safe)
        return []

    def dryrun(self, action: Dict[str, Any]) -> str:
        return f"[BluetoothAdapter] Would perform action: {json.dumps(action, ensure_ascii=False)}"

    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        # No direct device control implemented here — return a safe simulated result.
        time.sleep(0.1)
        return {"success": False, "error": "Bluetooth control not implemented in this adapter", "action": action}


# ------------------------------
# WiFi / Network adapter (light)
# ------------------------------
class WiFiAdapter(SystemAdapter):
    def __init__(self):
        self.platform = platform.system().lower()

    def discover(self) -> List[Dict[str, Any]]:
        # Try to call platform-specific discovery in a safe manner.
        try:
            if "linux" in self.platform:
                # Use nmcli to list Wi-Fi devices (if available)
                out = subprocess.run(["nmcli", "-t", "-f", "SSID,DEVICE,IN-USE", "device", "wifi", "list"], capture_output=True, timeout=3)
                if out.returncode == 0:
                    lines = out.stdout.decode("utf-8", errors="ignore").splitlines()
                    devices = []
                    for l in lines[:20]:
                        parts = l.split(":")
                        devices.append({"ssid": parts[0], "device": parts[1] if len(parts) > 1 else "", "active": parts[2] if len(parts) > 2 else ""})
                    return devices
        except Exception:
            pass

        # Fallback: no discovery
        return []

    def dryrun(self, action: Dict[str, Any]) -> str:
        return f"[WiFiAdapter] Dry-run: would run network action {action.get('command', action)}"

    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        # Example safe execution: if action is 'connect', just simulate.
        cmd = action.get("command")
        if cmd == "connect":
            ssid = action.get("ssid")
            return {"success": False, "error": "Connecting to WiFi not implemented, requires system integration", "ssid": ssid}
        return {"success": False, "error": "Unknown WiFi action", "action": action}


# ------------------------------
# Generic Network / HTTP adapter
# ------------------------------
class NetworkAdapter(SystemAdapter):
    def __init__(self, http_timeout: float = 5.0):
        self.http_timeout = http_timeout

    def discover(self) -> List[Dict[str, Any]]:
        # Network adapter isn't responsible for LAN discovery by default.
        return []

    def dryrun(self, action: Dict[str, Any]) -> str:
        return f"[NetworkAdapter] Dry-run: would perform network request: {action.get('url', action)}"

    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        # Safe simple HTTP GET/POST wrapper using requests if available
        try:
            import httpx  # type: ignore
            method = action.get("method", "GET").upper()
            url = action.get("url")
            if not url:
                return {"success": False, "error": "No URL provided"}
            if method == "GET":
                resp = httpx.get(url, timeout=self.http_timeout)
                return {"success": True, "status_code": resp.status_code, "text_preview": (resp.text[:400] if resp.text else "")}
            elif method == "POST":
                data = action.get("data", {})
                resp = httpx.post(url, json=data, timeout=self.http_timeout)
                return {"success": True, "status_code": resp.status_code, "text_preview": (resp.text[:400] if resp.text else "")}
            else:
                return {"success": False, "error": f"Unsupported method {method}"}
        except Exception as e:
            return {"success": False, "error": f"Network execute failed: {e}"}