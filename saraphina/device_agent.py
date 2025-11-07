#!/usr/bin/env python3
"""
DeviceAgent - on-device agent interface (DB-backed stubs)
"""
import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional

from .db import init_db, write_audit_log

class DeviceAgent:
    def __init__(self, device_id: Optional[str] = None, name: str = "Unnamed", platform: str = "unknown", owner: str = "unknown", db_path: Optional[str] = None):
        self.conn = init_db(db_path)
        self.device_id = device_id or f"dev_{uuid4()}"
        self.agent_id = f"agent_{uuid4()}"
        self.public_key = None
        self.name = name
        self.platform = platform
        self.owner = owner

    def register(self, token: str) -> str:
        # In real implementation, validate token and provision keys
        self.public_key = f"pk_{uuid4()}"
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        # Upsert device
        cur.execute(
            """
            INSERT OR REPLACE INTO devices (device_id, name, platform, owner, public_key, enrolled_at, last_seen, capabilities, last_location)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (self.device_id, self.name, self.platform, self.owner, self.public_key, now, now, json.dumps([]), "")
        )
        # Insert agent
        cur.execute(
            "INSERT OR REPLACE INTO device_agents (agent_id, device_id, public_key, heartbeat_ts, status) VALUES (?,?,?,?,?)",
            (self.agent_id, self.device_id, self.public_key, now, "online")
        )
        self.conn.commit()
        write_audit_log(self.conn, actor=self.device_id, action="register", target=self.agent_id, details={"token_used": bool(token)})
        return self.public_key

    def heartbeat(self) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        # Check current status
        cur.execute("SELECT status FROM device_agents WHERE agent_id=?", (self.agent_id,))
        row = cur.fetchone()
        current_status = (row[0] if row else "online")
        # Update heartbeat timestamp, preserve revoked status
        new_status = current_status if current_status == "revoked" else "online"
        cur.execute(
            "UPDATE device_agents SET heartbeat_ts=?, status=? WHERE agent_id=?",
            (now, new_status, self.agent_id)
        )
        cur.execute(
            "UPDATE devices SET last_seen=? WHERE device_id=?",
            (now, self.device_id)
        )
        self.conn.commit()
        write_audit_log(self.conn, actor=self.device_id, action="heartbeat", target=self.agent_id, details={"status": new_status})
        return {"status": new_status, "agent_id": self.agent_id, "ts": now}

    def execute_command(self, command: str) -> Dict[str, Any]:
        # Deny execution for revoked agents
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM device_agents WHERE agent_id=?", (self.agent_id,))
        row = cur.fetchone()
        status = (row[0] if row else "online")
        if status == 'revoked':
            result = {"ok": False, "error": "agent_revoked"}
            write_audit_log(self.conn, actor=self.device_id, action="execute_command", target=self.agent_id, details={"command": command, "result": result})
            return result
        # Policy enforcement (e.g., bed_time)
        cur.execute("SELECT policy_json FROM device_policies WHERE device_id=? ORDER BY created_at DESC LIMIT 1", (self.device_id,))
        row = cur.fetchone()
        if row and row[0]:
            try:
                import json as _json
                pol = _json.loads(row[0]) if isinstance(row[0], str) else row[0]
                bed = pol.get('bed_time')
                if bed:
                    from datetime import datetime as _dt
                    now_hm = _dt.now().strftime('%H:%M')
                    if now_hm >= str(bed):
                        result = {"ok": False, "error": "policy_blocked", "reason": "bed_time"}
                        write_audit_log(self.conn, actor=self.device_id, action="execute_command", target=self.agent_id, details={"command": command, "result": result})
                        return result
            except Exception:
                pass
        # Rate limit: max 10 commands/minute per device
        try:
            from datetime import datetime, timedelta
            threshold = datetime.utcnow() - timedelta(minutes=1)
            # Fetch recent logs and filter in Python due to timestamp format differences
            cur.execute("SELECT details, timestamp FROM audit_logs WHERE actor=? AND action='execute_command' ORDER BY timestamp DESC LIMIT 100", (self.device_id,))
            cnt = 0
            for det, ts in cur.fetchall():
                try:
                    tsdt = datetime.fromisoformat(ts)
                except Exception:
                    continue
                if tsdt >= threshold:
                    cnt += 1
            if cnt >= 10:
                result = {"ok": False, "error": "rate_limited"}
                write_audit_log(self.conn, actor=self.device_id, action="execute_command", target=self.agent_id, details={"command": command, "result": result})
                return result
        except Exception:
            pass
        # Safe, simulated execution only
        allowed = ["echo", "ping", "status"]
        result: Dict[str, Any]
        if command.startswith(tuple(allowed)):
            result = {"ok": True, "output": f"simulated: {command}"}
        else:
            result = {"ok": False, "error": "command_not_allowed"}
        write_audit_log(self.conn, actor=self.device_id, action="execute_command", target=self.agent_id, details={"command": command, "result": result})
        return result

    def report_telemetry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        write_audit_log(self.conn, actor=self.device_id, action="telemetry", target=self.agent_id, details=payload)
        return {"ack": True}
