import os
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

DB_PATH = os.path.join("D:\\Saraphina Root", "ai_data", "upgrade_learning.db")

class UpgradeLearningJournal:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Ensure the upgrade_attempts table exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS upgrade_attempts (
                    id TEXT PRIMARY KEY,
                    request TEXT,
                    spec_json TEXT,
                    code_generated TEXT,
                    validation_result TEXT,
                    success INTEGER,
                    error_message TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()

    def log_attempt(self, request: str, spec: dict, code: str,
                    validation_result: Optional[dict],
                    success: bool, error_message: Optional[str] = None) -> str:
        """Insert a new log entry into the learning journal."""
        uid = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO upgrade_attempts
                (id, request, spec_json, code_generated, validation_result,
                 success, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uid,
                request,
                json.dumps(spec, indent=2),
                code,
                json.dumps(validation_result or {}, indent=2),
                1 if success else 0,
                error_message,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        return uid

    def log_success(self, spec: dict, code: str) -> str:
        """Log a successful upgrade attempt."""
        return self.log_attempt(
            request=spec.get("feature_name", "unknown feature"),
            spec=spec,
            code=code,
            validation_result={"passed": True},
            success=True
        )

    def log_failure(self, spec: dict, code: str, validation_result: dict, error_message: str = None) -> str:
        """Log a failed upgrade attempt."""
        return self.log_attempt(
            request=spec.get("feature_name", "unknown feature"),
            spec=spec,
            code=code,
            validation_result=validation_result,
            success=False,
            error_message=error_message or "Validation failed"
        )

    def get_recent_failures(self, limit: int = 10) -> List[dict]:
        """Retrieve the most recent failed attempts for learning context."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT id, request, error_message, timestamp
                FROM upgrade_attempts
                WHERE success = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
        return [
            {"id": r[0], "request": r[1], "error": r[2], "timestamp": r[3]}
            for r in rows
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Basic success/failure stats for dashboard display."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("""
                SELECT success, COUNT(*) FROM upgrade_attempts GROUP BY success
            """)
            data = {int(success): count for success, count in cur.fetchall()}
        return {
            "success": data.get(1, 0),
            "failures": data.get(0, 0),
            "total": data.get(1, 0) + data.get(0, 0)
        }
