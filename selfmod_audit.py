#!/usr/bin/env python3
"""
Append-only signed audit helper for self-modification actions.

Writes JSONL entries:
  {"entry": { ... }, "hmac": "..."}
Uses SELF_MOD_SECRET (if present) to HMAC each record for tamper-evidence.
Ensures file permissions are restricted where possible.
"""
from __future__ import annotations
import os
import json
import hmac
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Default audit directory inside repository root (override via env SARAPHINA_ROOT)
ROOT = Path(os.getenv("SARAPHINA_ROOT", "."))  # operator can set
AUDIT_DIR = (ROOT / ".audit").resolve()
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_FILE = AUDIT_DIR / "selfmod.jsonl"

def _get_secret() -> Optional[bytes]:
    s = os.getenv("SELF_MOD_SECRET") or os.getenv("SELF_MOD_AUDIT_SECRET")
    return s.encode("utf-8") if s else None

def append_audit(entry: Dict[str, Any]) -> None:
    """
    Append an audit entry. The entry is augmented with timestamp and serialized.
    A HMAC is computed if SELF_MOD_SECRET (or SELF_MOD_AUDIT_SECRET) is present.
    """
    try:
        entry = dict(entry)  # copy to avoid mutation
        entry.setdefault('timestamp', datetime.utcnow().isoformat() + "Z")
        payload = json.dumps(entry, sort_keys=True, ensure_ascii=False).encode('utf-8')
        secret = _get_secret()
        sig = None
        if secret:
            sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        record = {'entry': entry, 'hmac': sig}
        # append atomically (best-effort)
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        try:
            os.chmod(AUDIT_FILE, 0o600)
        except Exception:
            # On Windows chmod may not be effective; operator must secure ACLs
            pass
    except Exception:
        # Audit must never raise — best-effort only
        import logging
        logging.getLogger("SelfModAudit").exception("Failed to append audit entry")

def read_all_audit(limit: int = 1000):
    """Return last up to `limit` audit entries as Python objects (oldest first)."""
    if not AUDIT_FILE.exists():
        return []
    out = []
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out