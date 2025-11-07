#!/usr/bin/env python3
"""
Monitoring utilities for Saraphina.
Provides a health pulse with key metrics.
"""
from typing import Dict, Any
from pathlib import Path
import json

from .db import DB_FILE


def _db_file_from_connection(conn) -> Path:
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA database_list;")
        rows = cur.fetchall()
        for r in rows:
            # r[2] is file path for main database
            if r[1] == 'main' and r[2]:
                return Path(r[2])
    except Exception:
        pass
    return DB_FILE


def health_pulse(conn) -> Dict[str, Any]:
    cur = conn.cursor()
    # active agents (online, non-revoked)
    try:
        cur.execute("SELECT COUNT(*) FROM device_agents WHERE status='online'")
        active_agents = int(cur.fetchone()[0])
    except Exception:
        active_agents = 0

    # failed actions from audit logs
    try:
        cur.execute("SELECT COUNT(*) FROM audit_logs WHERE action='execute_command' AND details LIKE '%\"ok\": false%'")
        failed_actions = int(cur.fetchone()[0])
    except Exception:
        failed_actions = 0

    # last backup timestamp from preferences
    try:
        cur.execute("SELECT value FROM preferences WHERE key='last_backup_ts'")
        row = cur.fetchone()
        last_backup_ts = row[0] if row else None
    except Exception:
        last_backup_ts = None

    # DB size
    db_path = _db_file_from_connection(conn)
    try:
        db_size = db_path.stat().st_size
    except Exception:
        db_size = None

    return {
        'active_agents_count': active_agents,
        'db_size_bytes': db_size,
        'last_backup_ts': last_backup_ts,
        'failed_actions_count': failed_actions,
        'db_path': str(db_path),
    }
