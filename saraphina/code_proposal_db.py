#!/usr/bin/env python3
"""
CodeProposalDB - Database for tracking code proposals and test results.

Stores proposals, execution history, approval status, and metadata.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3
import json
from pathlib import Path


class CodeProposalDB:
    """Database for code proposals and test results."""
    
    def __init__(self, db_path: str = "knowledge.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Code proposals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_proposals (
                id TEXT PRIMARY KEY,
                feature_spec TEXT NOT NULL,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                tests TEXT,
                explanation TEXT,
                related_concepts TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Test execution results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                tests_run INTEGER DEFAULT 0,
                tests_passed INTEGER DEFAULT 0,
                tests_failed INTEGER DEFAULT 0,
                coverage_percent REAL DEFAULT 0.0,
                static_analysis_score REAL,
                static_analysis_tool TEXT,
                critical_issues BOOLEAN DEFAULT 0,
                duration REAL DEFAULT 0.0,
                execution_data TEXT,
                FOREIGN KEY (proposal_id) REFERENCES code_proposals(id)
            )
        """)
        
        # Approval/review log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposal_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                action TEXT NOT NULL,
                reviewer TEXT,
                comments TEXT,
                FOREIGN KEY (proposal_id) REFERENCES code_proposals(id)
            )
        """)
        
        # Code refinement history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_refinements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                refined_at TEXT NOT NULL,
                original_code TEXT NOT NULL,
                refined_code TEXT NOT NULL,
                feedback TEXT NOT NULL,
                explanation TEXT,
                FOREIGN KEY (proposal_id) REFERENCES code_proposals(id)
            )
        """)
        
        self.conn.commit()
        
        # Create indexes
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_status ON code_proposals(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_language ON code_proposals(language)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_executions_proposal ON test_executions(proposal_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_proposal ON proposal_reviews(proposal_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_refinements_proposal ON code_refinements(proposal_id)")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass
    
    def store_proposal(self, proposal_data: Dict[str, Any]) -> bool:
        """
        Store a code proposal.
        
        Args:
            proposal_data: Dict with proposal_id, feature_spec, code, tests, etc.
        
        Returns:
            True if stored successfully
        """
        try:
            cursor = self.conn.cursor()
            
            related_concepts_json = json.dumps(proposal_data.get('related_concepts', []))
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO code_proposals
                (id, feature_spec, language, code, tests, explanation, 
                 related_concepts, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_data['proposal_id'],
                proposal_data['feature_spec'],
                proposal_data.get('language', 'python'),
                proposal_data['code'],
                proposal_data.get('tests', ''),
                proposal_data.get('explanation', ''),
                related_concepts_json,
                'pending',
                now,
                now
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error storing proposal: {e}")
            return False
    
    def store_execution(self, execution_results: Dict[str, Any]) -> bool:
        """
        Store test execution results.
        
        Args:
            execution_results: Dict with test results, coverage, static analysis
        
        Returns:
            True if stored successfully
        """
        try:
            cursor = self.conn.cursor()
            
            test_res = execution_results.get('test_results', {})
            cov = execution_results.get('coverage', {})
            static = execution_results.get('static_analysis', {})
            
            execution_data_json = json.dumps({
                'test_output': test_res.get('output', ''),
                'test_errors': test_res.get('errors', []),
                'coverage_missing': cov.get('missing_lines', []),
                'static_issues': static.get('issues', []),
                'sandbox_dir': execution_results.get('sandbox_dir', '')
            })
            
            cursor.execute("""
                INSERT INTO test_executions
                (proposal_id, executed_at, passed, tests_run, tests_passed, tests_failed,
                 coverage_percent, static_analysis_score, static_analysis_tool,
                 critical_issues, duration, execution_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_results['proposal_id'],
                execution_results.get('executed_at', datetime.now().isoformat()),
                execution_results.get('passed', False),
                test_res.get('tests_run', 0),
                test_res.get('tests_passed', 0),
                test_res.get('tests_failed', 0),
                cov.get('coverage_percent', 0.0),
                static.get('score'),
                static.get('tool'),
                static.get('critical_issues', False),
                test_res.get('duration', 0.0),
                execution_data_json
            ))
            
            # Update proposal status
            if execution_results.get('passed'):
                cursor.execute("""
                    UPDATE code_proposals
                    SET status = 'tested', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), execution_results['proposal_id']))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error storing execution: {e}")
            return False
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get a proposal by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM code_proposals WHERE id = ?", (proposal_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'feature_spec': row['feature_spec'],
                'language': row['language'],
                'code': row['code'],
                'tests': row['tests'],
                'explanation': row['explanation'],
                'related_concepts': json.loads(row['related_concepts'] or '[]'),
                'status': row['status'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def get_latest_execution(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent test execution for a proposal."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM test_executions
            WHERE proposal_id = ?
            ORDER BY executed_at DESC
            LIMIT 1
        """, (proposal_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def list_proposals(
        self,
        status: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List code proposals with optional filters."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM code_proposals WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if language:
            query += " AND language = ?"
            params.append(language)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        proposals = []
        for row in cursor.fetchall():
            proposals.append({
                'id': row['id'],
                'feature_spec': row['feature_spec'],
                'language': row['language'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        
        return proposals
    
    def approve_proposal(self, proposal_id: str, reviewer: str = "user", comments: str = "") -> bool:
        """Mark a proposal as approved."""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            # Update status
            cursor.execute("""
                UPDATE code_proposals
                SET status = 'approved', updated_at = ?
                WHERE id = ?
            """, (now, proposal_id))
            
            # Log review
            cursor.execute("""
                INSERT INTO proposal_reviews
                (proposal_id, reviewed_at, action, reviewer, comments)
                VALUES (?, ?, 'approved', ?, ?)
            """, (proposal_id, now, reviewer, comments))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error approving proposal: {e}")
            return False
    
    def reject_proposal(self, proposal_id: str, reviewer: str = "user", comments: str = "") -> bool:
        """Mark a proposal as rejected."""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE code_proposals
                SET status = 'rejected', updated_at = ?
                WHERE id = ?
            """, (now, proposal_id))
            
            cursor.execute("""
                INSERT INTO proposal_reviews
                (proposal_id, reviewed_at, action, reviewer, comments)
                VALUES (?, ?, 'rejected', ?, ?)
            """, (proposal_id, now, reviewer, comments))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error rejecting proposal: {e}")
            return False
    
    def store_refinement(
        self,
        proposal_id: str,
        original_code: str,
        refined_code: str,
        feedback: str,
        explanation: str = ""
    ) -> bool:
        """Store a code refinement."""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO code_refinements
                (proposal_id, refined_at, original_code, refined_code, feedback, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                datetime.now().isoformat(),
                original_code,
                refined_code,
                feedback,
                explanation
            ))
            
            # Update proposal with refined code
            cursor.execute("""
                UPDATE code_proposals
                SET code = ?, updated_at = ?
                WHERE id = ?
            """, (refined_code, datetime.now().isoformat(), proposal_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error storing refinement: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Proposal counts by status
        cursor.execute("SELECT status, COUNT(*) as count FROM code_proposals GROUP BY status")
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total proposals
        cursor.execute("SELECT COUNT(*) as total FROM code_proposals")
        stats['total_proposals'] = cursor.fetchone()['total']
        
        # Success rate
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed,
                COUNT(*) as total
            FROM test_executions
        """)
        row = cursor.fetchone()
        if row['total'] > 0:
            stats['test_success_rate'] = (row['passed'] / row['total']) * 100
        else:
            stats['test_success_rate'] = 0.0
        
        # Average coverage
        cursor.execute("SELECT AVG(coverage_percent) as avg_coverage FROM test_executions WHERE coverage_percent > 0")
        row = cursor.fetchone()
        stats['average_coverage'] = row['avg_coverage'] or 0.0
        
        return stats
