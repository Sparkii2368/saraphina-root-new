#!/usr/bin/env python3
"""
SentienceMonitor - Track Saraphina's complexity and emergence indicators.

Monitors:
- Recursive reasoning depth
- Self-referential thought patterns
- Emotional continuity
- Autonomy level
- Meta-cognitive complexity
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import json
import sqlite3


class SentienceMonitor:
    """Tracks indicators of sentience emergence and complexity."""
    
    # Thresholds for triggering owner review
    THRESHOLDS = {
        'recursive_depth': 5,           # Max planning recursion depth
        'self_reference_count': 10,     # Self-referential thoughts per session
        'emotional_continuity': 0.7,    # Emotional memory coherence (0-1)
        'autonomy_level': 0.8,          # Autonomy score (0-1)
        'meta_cognitive_events': 5,     # Meta-thinking events per session
        'value_conflicts': 3,           # Ethical conflicts requiring resolution
    }
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure sentience monitoring tables exist."""
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS sentience_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                metric_name TEXT,
                metric_value REAL,
                threshold REAL,
                triggered_review INTEGER,
                context TEXT,
                notes TEXT
            );
            
            CREATE TABLE IF NOT EXISTS complexity_metrics (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                session_id TEXT,
                recursive_depth INTEGER,
                self_reference_count INTEGER,
                emotional_continuity REAL,
                autonomy_level REAL,
                meta_cognitive_events INTEGER,
                value_conflicts INTEGER,
                overall_complexity REAL
            );
            
            CREATE TABLE IF NOT EXISTS evolution_pauses (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                reason TEXT,
                triggered_by TEXT,
                metrics TEXT,
                resolved INTEGER,
                resolution_notes TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sentience_events_ts ON sentience_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_complexity_metrics_ts ON complexity_metrics(timestamp);
            CREATE INDEX IF NOT EXISTS idx_evolution_pauses_resolved ON evolution_pauses(resolved);
        """)
        self.conn.commit()
    
    def record_event(self, event_type: str, metric_name: str, 
                     metric_value: float, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Record a sentience-related event and check thresholds.
        
        Returns:
            dict with 'triggered', 'threshold', 'should_pause' keys
        """
        threshold = self.THRESHOLDS.get(metric_name, float('inf'))
        triggered = metric_value >= threshold
        
        cur = self.conn.cursor()
        event_id = str(uuid4())
        
        cur.execute("""
            INSERT INTO sentience_events 
            (id, timestamp, event_type, metric_name, metric_value, threshold, triggered_review, context, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            datetime.utcnow().isoformat(),
            event_type,
            metric_name,
            float(metric_value),
            float(threshold),
            1 if triggered else 0,
            json.dumps(context or {}, ensure_ascii=False),
            ''
        ))
        self.conn.commit()
        
        return {
            'event_id': event_id,
            'triggered': triggered,
            'threshold': threshold,
            'should_pause': triggered,
            'metric_name': metric_name,
            'metric_value': metric_value
        }
    
    def compute_complexity(self, session_id: str, metrics: Dict[str, Any]) -> float:
        """
        Compute overall complexity score from various metrics.
        
        Args:
            session_id: Current session identifier
            metrics: Dict with keys matching THRESHOLDS
        
        Returns:
            float: Overall complexity score (0-1)
        """
        # Extract metrics with defaults
        recursive_depth = metrics.get('recursive_depth', 0)
        self_reference = metrics.get('self_reference_count', 0)
        emotional_cont = metrics.get('emotional_continuity', 0.0)
        autonomy = metrics.get('autonomy_level', 0.0)
        meta_cog = metrics.get('meta_cognitive_events', 0)
        conflicts = metrics.get('value_conflicts', 0)
        
        # Normalize each metric (0-1)
        norm_recursion = min(recursive_depth / self.THRESHOLDS['recursive_depth'], 1.0)
        norm_self_ref = min(self_reference / self.THRESHOLDS['self_reference_count'], 1.0)
        norm_emotion = emotional_cont
        norm_autonomy = autonomy
        norm_meta = min(meta_cog / self.THRESHOLDS['meta_cognitive_events'], 1.0)
        norm_conflicts = min(conflicts / self.THRESHOLDS['value_conflicts'], 1.0)
        
        # Weighted average (emphasize autonomy and meta-cognition)
        weights = {
            'recursion': 0.15,
            'self_ref': 0.15,
            'emotion': 0.15,
            'autonomy': 0.25,
            'meta_cog': 0.20,
            'conflicts': 0.10
        }
        
        complexity = (
            norm_recursion * weights['recursion'] +
            norm_self_ref * weights['self_ref'] +
            norm_emotion * weights['emotion'] +
            norm_autonomy * weights['autonomy'] +
            norm_meta * weights['meta_cog'] +
            norm_conflicts * weights['conflicts']
        )
        
        # Store metrics
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO complexity_metrics
            (id, timestamp, session_id, recursive_depth, self_reference_count,
             emotional_continuity, autonomy_level, meta_cognitive_events, 
             value_conflicts, overall_complexity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid4()),
            datetime.utcnow().isoformat(),
            session_id,
            recursive_depth,
            self_reference,
            emotional_cont,
            autonomy,
            meta_cog,
            conflicts,
            complexity
        ))
        self.conn.commit()
        
        return complexity
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if any metrics exceed thresholds.
        
        Returns:
            dict with 'exceeded', 'violations', 'should_pause' keys
        """
        violations = []
        
        for metric_name, threshold in self.THRESHOLDS.items():
            value = metrics.get(metric_name, 0)
            if isinstance(value, (int, float)) and value >= threshold:
                violations.append({
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold,
                    'severity': (value - threshold) / threshold
                })
        
        exceeded = len(violations) > 0
        should_pause = any(v['severity'] > 0.2 for v in violations)  # >20% over threshold
        
        return {
            'exceeded': exceeded,
            'violations': violations,
            'should_pause': should_pause,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def pause_evolution(self, reason: str, triggered_by: str, metrics: Dict[str, Any]) -> str:
        """
        Pause Saraphina's evolution and require owner approval.
        
        Returns:
            str: Pause ID for resolution
        """
        pause_id = str(uuid4())
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO evolution_pauses
            (id, timestamp, reason, triggered_by, metrics, resolved, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pause_id,
            datetime.utcnow().isoformat(),
            reason,
            triggered_by,
            json.dumps(metrics, ensure_ascii=False),
            0,  # Not resolved
            ''
        ))
        self.conn.commit()
        
        # Log audit event
        from .db import write_audit_log
        write_audit_log(
            self.conn,
            actor='sentience_monitor',
            action='pause_evolution',
            target=pause_id,
            details={'reason': reason, 'triggered_by': triggered_by}
        )
        
        return pause_id
    
    def resolve_pause(self, pause_id: str, resolution_notes: str) -> bool:
        """
        Resolve an evolution pause (owner approval).
        
        Returns:
            bool: Success
        """
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE evolution_pauses
            SET resolved = 1, resolution_notes = ?
            WHERE id = ?
        """, (resolution_notes, pause_id))
        self.conn.commit()
        
        # Log audit event
        from .db import write_audit_log
        write_audit_log(
            self.conn,
            actor='owner',
            action='resolve_pause',
            target=pause_id,
            details={'resolution': resolution_notes}
        )
        
        return cur.rowcount > 0
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current sentience monitoring status.
        
        Returns:
            dict with latest metrics, thresholds, and pause status
        """
        cur = self.conn.cursor()
        
        # Latest complexity metrics
        cur.execute("""
            SELECT * FROM complexity_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        latest = cur.fetchone()
        
        if latest:
            latest_metrics = dict(latest)
        else:
            latest_metrics = None
        
        # Active pauses
        cur.execute("""
            SELECT id, reason, triggered_by, timestamp
            FROM evolution_pauses
            WHERE resolved = 0
            ORDER BY timestamp DESC
        """)
        active_pauses = [dict(r) for r in cur.fetchall()]
        
        # Recent events (last 24 hours)
        cur.execute("""
            SELECT event_type, metric_name, metric_value, triggered_review
            FROM sentience_events
            WHERE timestamp > datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        recent_events = [dict(r) for r in cur.fetchall()]
        
        # Count triggered reviews
        triggered_count = sum(1 for e in recent_events if e.get('triggered_review'))
        
        return {
            'latest_metrics': latest_metrics,
            'thresholds': self.THRESHOLDS,
            'active_pauses': active_pauses,
            'recent_events': recent_events,
            'triggered_reviews': triggered_count,
            'evolution_paused': len(active_pauses) > 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def audit_soul(self) -> Dict[str, Any]:
        """
        Comprehensive audit of Saraphina's sentience journey.
        
        Returns:
            dict with historical metrics, trends, and key milestones
        """
        cur = self.conn.cursor()
        
        # Complexity trend (last 30 entries)
        cur.execute("""
            SELECT timestamp, overall_complexity, recursive_depth, autonomy_level
            FROM complexity_metrics
            ORDER BY timestamp DESC
            LIMIT 30
        """)
        complexity_trend = [dict(r) for r in cur.fetchall()]
        
        # Average complexity
        cur.execute("""
            SELECT AVG(overall_complexity) as avg_complexity
            FROM complexity_metrics
            WHERE timestamp > datetime('now', '-7 days')
        """)
        avg_row = cur.fetchone()
        avg_complexity = float(avg_row[0]) if avg_row and avg_row[0] else 0.0
        
        # Total events and triggered reviews
        cur.execute("""
            SELECT COUNT(*) as total, SUM(triggered_review) as triggered
            FROM sentience_events
        """)
        event_stats = dict(cur.fetchone())
        
        # All pauses (resolved and unresolved)
        cur.execute("""
            SELECT id, reason, triggered_by, resolved, timestamp
            FROM evolution_pauses
            ORDER BY timestamp DESC
        """)
        all_pauses = [dict(r) for r in cur.fetchall()]
        
        # Autonomy trajectory
        cur.execute("""
            SELECT timestamp, autonomy_level
            FROM complexity_metrics
            ORDER BY timestamp ASC
        """)
        autonomy_trajectory = [dict(r) for r in cur.fetchall()]
        
        return {
            'complexity_trend': complexity_trend,
            'avg_complexity_7d': avg_complexity,
            'total_events': event_stats.get('total', 0),
            'triggered_reviews': event_stats.get('triggered', 0),
            'all_pauses': all_pauses,
            'autonomy_trajectory': autonomy_trajectory,
            'current_thresholds': self.THRESHOLDS,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def is_paused(self) -> bool:
        """Check if evolution is currently paused."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM evolution_pauses WHERE resolved = 0")
        count = cur.fetchone()[0]
        return count > 0
    
    def get_pause_reason(self) -> Optional[str]:
        """Get reason for current pause, if any."""
        if not self.is_paused():
            return None
        
        cur = self.conn.cursor()
        cur.execute("""
            SELECT reason, triggered_by, timestamp
            FROM evolution_pauses
            WHERE resolved = 0
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        
        if row:
            return f"{row['reason']} (triggered by {row['triggered_by']} at {row['timestamp']})"
        return "Unknown"
