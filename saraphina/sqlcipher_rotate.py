#!/usr/bin/env python3
"""
SQLCipher auto-rotation: scheduled key rotation with seamless migration.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

from .db import sqlcipher_available, rekey_sqlcipher, get_preference, set_preference

def should_rotate(conn, interval_days: int = 90) -> bool:
    last = get_preference(conn, 'sqlcipher_last_rotation')
    if not last:
        return False
    try:
        dt = datetime.fromisoformat(last)
        return (datetime.utcnow() - dt).days >= interval_days
    except Exception:
        return False

def rotate_key(sec, conn, path: str) -> bool:
    """
    Rotate SQLCipher key: generate new key, rekey DB, store new key in keystore.
    Returns True on success.
    """
    if not sqlcipher_available():
        return False
    try:
        old_key = sec.get_secret('db_sqlcipher_key')
        if not old_key:
            return False
        # Generate new key
        import os, base64
        new_key = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
        # Rekey
        rekey_sqlcipher(path, old_key, new_key)
        # Update keystore
        sec.set_secret('db_sqlcipher_key', new_key)
        set_preference(conn, 'sqlcipher_last_rotation', datetime.utcnow().isoformat())
        return True
    except Exception:
        return False
