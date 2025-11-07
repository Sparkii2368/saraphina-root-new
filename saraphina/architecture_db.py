#!/usr/bin/env python3
"""
ArchitectureDB - Store and manage architectural redesign proposals.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sqlite3


class ArchitectureDB:
    """Persistence for architecture proposals and simulation results."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS architecture_proposals (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              type TEXT NOT NULL,              -- refactor, microservice, abstraction, pattern
              scope TEXT NOT NULL,             -- module names or 'system'
              title TEXT,
              rationale TEXT,
              proposed_design TEXT,            -- JSON or markdown spec
              simulation_results TEXT,         -- JSON metrics
              status TEXT NOT NULL,            -- pending, simulated, approved, rejected, promoted
              risk_score REAL DEFAULT 0.0,
              complexity_score REAL,
              estimated_effort_hours REAL,
              simulated_at TEXT,
              approved_at TEXT,
              promoted_at TEXT,
              reviewer TEXT
            )
            """
        )
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_arch_status ON architecture_proposals(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_arch_type ON architecture_proposals(type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_arch_scope ON architecture_proposals(scope)")
        except Exception:
            pass
        self.conn.commit()

    def create_proposal(self, proposal: Dict[str, Any]) -> str:
        cur = self.conn.cursor()
        proposal_id = proposal.get('id') or f"arch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        cur.execute(
            """
            INSERT INTO architecture_proposals
            (id, created_at, type, scope, title, rationale, proposed_design, status,
             risk_score, complexity_score, estimated_effort_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                datetime.utcnow().isoformat(),
                proposal['type'],
                proposal['scope'],
                proposal.get('title', ''),
                proposal.get('rationale', ''),
                json.dumps(proposal.get('proposed_design', {})),
                proposal.get('status', 'pending'),
                float(proposal.get('risk_score', 0.5)),
                float(proposal.get('complexity_score', 0.0)),
                float(proposal.get('estimated_effort_hours', 0.0))
            )
        )
        self.conn.commit()
        return proposal_id

    def update_simulation(self, proposal_id: str, results: Dict[str, Any]):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE architecture_proposals
            SET simulation_results = ?, simulated_at = ?, status = 'simulated'
            WHERE id = ?
            """,
            (json.dumps(results), datetime.utcnow().isoformat(), proposal_id)
        )
        self.conn.commit()

    def set_status(self, proposal_id: str, status: str, reviewer: Optional[str] = None):
        cur = self.conn.cursor()
        fields = ["status = ?"]
        params: List[Any] = [status]
        
        if status == 'approved':
            fields.append("approved_at = ?")
            params.append(datetime.utcnow().isoformat())
        elif status == 'promoted':
            fields.append("promoted_at = ?")
            params.append(datetime.utcnow().isoformat())
        
        if reviewer:
            fields.append("reviewer = ?")
            params.append(reviewer)
        
        params.append(proposal_id)
        cur.execute(
            f"UPDATE architecture_proposals SET {', '.join(fields)} WHERE id = ?",
            params
        )
        self.conn.commit()

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM architecture_proposals WHERE id = ?", (proposal_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d['proposed_design'] = json.loads(d['proposed_design'] or '{}')
        except Exception:
            pass
        try:
            d['simulation_results'] = json.loads(d['simulation_results'] or '{}')
        except Exception:
            d['simulation_results'] = {}
        return d

    def list_proposals(
        self,
        status: Optional[str] = None,
        proposal_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        query = "SELECT * FROM architecture_proposals WHERE 1=1"
        params: List[Any] = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if proposal_type:
            query += " AND type = ?"
            params.append(proposal_type)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        
        results: List[Dict[str, Any]] = []
        for row in cur.fetchall():
            d = dict(row)
            try:
                d['proposed_design'] = json.loads(d['proposed_design'] or '{}')
            except Exception:
                pass
            try:
                d['simulation_results'] = json.loads(d['simulation_results'] or '{}')
            except Exception:
                d['simulation_results'] = {}
            results.append(d)
        
        return results
