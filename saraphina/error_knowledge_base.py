#!/usr/bin/env python3
"""
Error Knowledge Base - Stores error patterns and fixes
Learns from every error to become more resilient
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger("ErrorKB")


class ErrorKnowledgeBase:
    """Database of errors and their fixes"""
    
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path("ai_data/errors.db")
        
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Initialize error database schema"""
        cur = self.conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                error_id TEXT PRIMARY KEY,
                subsystem TEXT NOT NULL,
                function TEXT NOT NULL,
                error_type TEXT NOT NULL,
                message TEXT NOT NULL,
                stack_trace TEXT,
                context TEXT,
                fix_code TEXT,
                fix_description TEXT,
                timestamp TEXT NOT NULL,
                last_occurrence TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                status TEXT DEFAULT 'new',
                auto_heal_success INTEGER DEFAULT 0,
                auto_heal_failure INTEGER DEFAULT 0,
                require_approval INTEGER DEFAULT 0
            )
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_subsystem ON errors(subsystem)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON errors(status)
        """)
        
        self.conn.commit()
    
    def record_error(self, error_event: Dict):
        """Record an error occurrence"""
        cur = self.conn.cursor()
        
        # Check if we've seen this error before
        cur.execute("SELECT * FROM errors WHERE error_id = ?", (error_event['error_id'],))
        existing = cur.fetchone()
        
        if existing:
            # Update existing error
            cur.execute("""
                UPDATE errors 
                SET last_occurrence = ?, 
                    occurrence_count = occurrence_count + 1,
                    stack_trace = ?,
                    context = ?
                WHERE error_id = ?
            """, (
                error_event['timestamp'],
                error_event.get('stack_trace', ''),
                json.dumps({
                    'args': error_event.get('args', ''),
                    'kwargs': error_event.get('kwargs', '')
                }),
                error_event['error_id']
            ))
            logger.info(f"Error {error_event['error_id']} occurred again (count: {existing['occurrence_count'] + 1})")
        else:
            # Insert new error
            cur.execute("""
                INSERT INTO errors (
                    error_id, subsystem, function, error_type, message, 
                    stack_trace, context, timestamp, last_occurrence, require_approval
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                error_event['error_id'],
                error_event['subsystem'],
                error_event['function'],
                error_event['error_type'],
                error_event['message'],
                error_event.get('stack_trace', ''),
                json.dumps({
                    'args': error_event.get('args', ''),
                    'kwargs': error_event.get('kwargs', '')
                }),
                error_event['timestamp'],
                error_event['timestamp'],
                1 if error_event.get('require_approval') else 0
            ))
            logger.info(f"New error recorded: {error_event['error_id']} in {error_event['subsystem']}")
        
        self.conn.commit()
    
    def get_fix(self, error_id: str) -> Optional[Dict]:
        """Get stored fix for an error"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM errors 
            WHERE error_id = ? AND fix_code IS NOT NULL
        """, (error_id,))
        
        row = cur.fetchone()
        if row:
            return dict(row)
        return None
    
    def store_fix(self, error_id: str, fix_code: str, fix_description: str):
        """Store a fix for an error"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE errors 
            SET fix_code = ?, 
                fix_description = ?, 
                status = 'fixed'
            WHERE error_id = ?
        """, (fix_code, fix_description, error_id))
        
        self.conn.commit()
        logger.info(f"Fix stored for error {error_id}")
    
    def record_heal_success(self, error_id: str):
        """Record successful auto-heal"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE errors 
            SET auto_heal_success = auto_heal_success + 1
            WHERE error_id = ?
        """, (error_id,))
        self.conn.commit()
    
    def record_heal_failure(self, error_id: str):
        """Record failed auto-heal attempt"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE errors 
            SET auto_heal_failure = auto_heal_failure + 1
            WHERE error_id = ?
        """, (error_id,))
        self.conn.commit()
    
    def get_unfixed_errors(self, limit: int = 10) -> List[Dict]:
        """Get errors that don't have fixes yet"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM errors 
            WHERE fix_code IS NULL 
            ORDER BY occurrence_count DESC, last_occurrence DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cur.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get error statistics"""
        cur = self.conn.cursor()
        
        stats = {}
        
        # Total errors
        cur.execute("SELECT COUNT(*) FROM errors")
        stats['total_errors'] = cur.fetchone()[0]
        
        # Fixed errors
        cur.execute("SELECT COUNT(*) FROM errors WHERE fix_code IS NOT NULL")
        stats['fixed_errors'] = cur.fetchone()[0]
        
        # Auto-heal success rate
        cur.execute("SELECT SUM(auto_heal_success), SUM(auto_heal_failure) FROM errors")
        row = cur.fetchone()
        total_heals = (row[0] or 0) + (row[1] or 0)
        stats['auto_heal_success_rate'] = (row[0] or 0) / total_heals if total_heals > 0 else 0
        
        # Most common errors
        cur.execute("""
            SELECT subsystem, COUNT(*) as count 
            FROM errors 
            GROUP BY subsystem 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['most_common_subsystems'] = [dict(row) for row in cur.fetchall()]
        
        return stats
    
    def apply_fix(self, fix: Dict, func, args, kwargs):
        """Apply a stored fix and retry the function"""
        # TODO: Implement fix application logic
        # For now, just retry the function
        return func(*args, **kwargs)
