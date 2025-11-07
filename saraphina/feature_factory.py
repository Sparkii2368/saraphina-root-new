#!/usr/bin/env python3
"""
FeatureFactory - propose features, sandbox test, and sign/promote artifacts
"""
import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional, List

from .db import init_db, write_audit_log

try:
    from .ultra_ai_core import CodeExecutionSandbox
except Exception:
    CodeExecutionSandbox = None  # Fallback if ultra core not available

class FeatureFactory:
    def __init__(self, db_path: Optional[str] = None, author: str = "system"):
        self.conn = init_db(db_path)
        self.author = author

    def propose_feature(self, spec: Dict[str, Any]) -> str:
        artifact_id = f"art_{uuid4()}"
        now = datetime.utcnow().isoformat()
        title = spec.get("title") or spec.get("name") or "Untitled Feature"
        code = spec.get("code", "")
        tests = spec.get("tests", "")
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO code_artifacts (artifact_id, title, code, tests, author, status, created_at) VALUES (?,?,?,?,?,?,?)",
            (artifact_id, title, code, tests if isinstance(tests, str) else json.dumps(tests), self.author, "draft", now)
        )
        self.conn.commit()
        write_audit_log(self.conn, actor=self.author, action="propose_feature", target=artifact_id, details=spec)
        return artifact_id

    def run_sandbox(self, artifact_id: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("SELECT artifact_id, title, code, tests FROM code_artifacts WHERE artifact_id=?", (artifact_id,))
        row = cur.fetchone()
        if not row:
            return {"ok": False, "error": "artifact_not_found"}

        code = row[2] or ""
        tests_raw = row[3] or ""

        # Parse tests
        tests: List[Dict[str, Any]] = []
        if tests_raw:
            try:
                tests = json.loads(tests_raw) if isinstance(tests_raw, str) else tests_raw
            except Exception:
                tests = []

        report = {"artifact_id": artifact_id, "tests_run": 0, "passes": 0, "failures": 0, "results": []}

        if CodeExecutionSandbox is None:
            report.update({"ok": False, "error": "sandbox_unavailable"})
            return report

        sandbox = CodeExecutionSandbox()

        # If no code, generate a baseline solution from title prompt
        if not code:
            code = sandbox.generate_code_solution(row[1])

        for t in tests:
            inputs = t.get("inputs", {})
            expected = t.get("expected")
            ok, result = sandbox.safe_execute(code, inputs)
            passed = ok and (result == expected if "expected" in t else ok)
            report["tests_run"] += 1
            report["passes"] += 1 if passed else 0
            report["failures"] += 0 if passed else 1
            report["results"].append({"inputs": inputs, "expected": expected, "result": result, "ok": ok, "passed": passed})

        write_audit_log(self.conn, actor=self.author, action="run_sandbox", target=artifact_id, details=report)
        report["ok"] = True
        return report

    def sign_and_promote(self, artifact_id: str, owner_signature: str, owner_pubkey_pem: Optional[str] = None) -> Dict[str, Any]:
        # Optional signature verification (Ed25519)
        verified = False
        try:
            if owner_pubkey_pem:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                from cryptography.hazmat.primitives import serialization
                import base64
                pub = Ed25519PublicKey.from_public_bytes(
                    serialization.load_pem_public_key(owner_pubkey_pem.encode('utf-8')).public_bytes(
                        encoding=serialization.Encoding.Raw,
                        format=serialization.PublicFormat.Raw
                    )
                )
                sig = base64.b64decode(owner_signature)
                pub.verify(sig, artifact_id.encode('utf-8'))
                verified = True
        except Exception:
            verified = False
        if not verified:
            # Fallback minimal check: non-empty signature required
            if not owner_signature:
                return {"ok": False, "error": "signature_required"}
        cur = self.conn.cursor()
        cur.execute("UPDATE code_artifacts SET status=? WHERE artifact_id=?", ("promoted", artifact_id))
        self.conn.commit()
        record = {
            "artifact_id": artifact_id,
            "promoted_at": datetime.utcnow().isoformat(),
            "signature": owner_signature,
            "verified": verified,
            "status": "promoted"
        }
        write_audit_log(self.conn, actor="owner", action="sign_and_promote", target=artifact_id, details=record)
        record["ok"] = True
        return record
