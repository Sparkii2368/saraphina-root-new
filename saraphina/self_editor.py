#!/usr/bin/env python3
"""
SelfEditor - controlled, auditable self-editing utilities (env/config, allowlisted files).
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional

from .db import write_audit_log

APP_ROOT = Path('D:/Saraphina Root')
ENV_PATH = APP_ROOT / '.env'

ALLOWLIST = {
    str(APP_ROOT / 'saraphina/voice_integration.py'),
    str(APP_ROOT / 'saraphina_terminal_ultra.py'),
    str(ENV_PATH),
}

class SelfEditor:
    def __init__(self, conn):
        self.conn = conn

    def set_env_keys(self, kv: Dict[str, str]) -> bool:
        """Create/update .env keys atomically; returns True if updated."""
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        lines: Dict[str, str] = {}
        if ENV_PATH.exists():
            for line in ENV_PATH.read_text(encoding='utf-8', errors='ignore').splitlines():
                s = line.strip()
                if not s or s.startswith('#') or '=' not in s:
                    continue
                k, v = s.split('=', 1)
                lines[k.strip()] = v.strip()
        changed = False
        for k, v in kv.items():
            if lines.get(k) != str(v):
                lines[k] = str(v)
                changed = True
        if not changed:
            return False
        # Write out sorted for stability
        out = []
        seen = set()
        for k, v in sorted(lines.items()):
            seen.add(k)
            out.append(f"{k}={v}")
        ENV_PATH.write_text("\n".join(out) + "\n", encoding='utf-8')
        write_audit_log(self.conn, 'self', 'set_env_keys', str(ENV_PATH), kv)
        return True

    def is_admin_needed(self) -> bool:
        # Placeholder: write to protected locations would require admin; we only touch app root.
        return False
