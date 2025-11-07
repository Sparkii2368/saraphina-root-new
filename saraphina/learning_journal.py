#!/usr/bin/env python3
"""
Learning Journal: Track learning events, strategies, outcomes, and context for meta-learning.
Features: Event logging, performance tracking, strategy analysis, growth metrics.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import sqlite3


@dataclass
class LearningEvent:
    """Single learning event with full context."""
    event_id: str
    timestamp: datetime
    event_type: str  # query, correction, feedback, discovery, failure, success
    input_data: Dict[str, Any]
    method_used: str
    result: Dict[str, Any]
    confidence: float
    success: bool
    feedback: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'input_data': self.input_data,
            'method_used': self.method_used,
            'result': self.result,
            'confidence': self.confidence,
            'success': self.success,
            'feedback': self.feedback,
            'context': self.context,
            'lessons_learned': self.lessons_learned
        }


@dataclass
class StrategyOutcome:
    """Outcome of using a specific strategy."""
    strategy_name: str
    success_count: int
    failure_count: int
    avg_confidence: float
    avg_duration_ms: float
    total_uses: int
    last_used: datetime
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.success_count / self.total_uses if self.total_uses > 0 else 0.0


class LearningJournal:
    """Main learning journal for tracking all learning events."""
    
    def __init__(self, db_path: str = 'ai_data/learning_journal.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        cur = self.conn.cursor()
        
        # Learning events table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS learning_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                input_data TEXT NOT NULL,
                method_used TEXT NOT NULL,
                result TEXT NOT NULL,
                confidence REAL NOT NULL,
                success BOOLEAN NOT NULL,
                feedback TEXT,
                context TEXT,
                lessons_learned TEXT
            )
        ''')
        
        # Strategy performance table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                strategy_name TEXT PRIMARY KEY,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                total_confidence REAL DEFAULT 0.0,
                total_duration_ms REAL DEFAULT 0.0,
                total_uses INTEGER DEFAULT 0,
                last_used TEXT,
                metadata TEXT
            )
        ''')
        
        # Growth metrics table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS growth_metrics (
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                context TEXT
            )
        ''')
        
        # Reflection notes table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                trigger TEXT NOT NULL,
                analysis TEXT NOT NULL,
                insights TEXT,
                proposed_changes TEXT
            )
        ''')
        
        self.conn.commit()
    
    def log_event(self, event: LearningEvent):
        """Log a learning event."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO learning_events 
            (event_id, timestamp, event_type, input_data, method_used, result, 
             confidence, success, feedback, context, lessons_learned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id,
            event.timestamp.isoformat(),
            event.event_type,
            json.dumps(event.input_data),
            event.method_used,
            json.dumps(event.result),
            event.confidence,
            event.success,
            json.dumps(event.feedback) if event.feedback else None,
            json.dumps(event.context),
            json.dumps(event.lessons_learned)
        ))
        self.conn.commit()
        
        # Update strategy performance
        self._update_strategy_performance(event)
    
    def _update_strategy_performance(self, event: LearningEvent):
        """Update strategy performance metrics."""
        cur = self.conn.cursor()
        
        # Get current stats
        cur.execute('SELECT * FROM strategy_performance WHERE strategy_name = ?', (event.method_used,))
        row = cur.fetchone()
        
        if row:
            success_count = row[1] + (1 if event.success else 0)
            failure_count = row[2] + (0 if event.success else 1)
            total_confidence = row[3] + event.confidence
            total_duration = row[4] + event.context.get('duration_ms', 0)
            total_uses = row[5] + 1
            
            cur.execute('''
                UPDATE strategy_performance 
                SET success_count = ?, failure_count = ?, total_confidence = ?,
                    total_duration_ms = ?, total_uses = ?, last_used = ?
                WHERE strategy_name = ?
            ''', (success_count, failure_count, total_confidence, total_duration, 
                  total_uses, event.timestamp.isoformat(), event.method_used))
        else:
            cur.execute('''
                INSERT INTO strategy_performance 
                (strategy_name, success_count, failure_count, total_confidence,
                 total_duration_ms, total_uses, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.method_used,
                1 if event.success else 0,
                0 if event.success else 1,
                event.confidence,
                event.context.get('duration_ms', 0),
                1,
                event.timestamp.isoformat()
            ))
        
        self.conn.commit()
    
    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None) -> List[LearningEvent]:
        """Get recent learning events."""
        cur = self.conn.cursor()
        
        if event_type:
            cur.execute('''
                SELECT * FROM learning_events 
                WHERE event_type = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (event_type, limit))
        else:
            cur.execute('''
                SELECT * FROM learning_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        events = []
        for row in cur.fetchall():
            events.append(LearningEvent(
                event_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                event_type=row[2],
                input_data=json.loads(row[3]),
                method_used=row[4],
                result=json.loads(row[5]),
                confidence=row[6],
                success=bool(row[7]),
                feedback=json.loads(row[8]) if row[8] else None,
                context=json.loads(row[9]) if row[9] else {},
                lessons_learned=json.loads(row[10]) if row[10] else []
            ))
        
        return events
    
    def get_strategy_performance(self, strategy_name: Optional[str] = None) -> Dict[str, StrategyOutcome]:
        """Get performance metrics for strategies."""
        cur = self.conn.cursor()
        
        if strategy_name:
            cur.execute('SELECT * FROM strategy_performance WHERE strategy_name = ?', (strategy_name,))
            rows = [cur.fetchone()]
        else:
            cur.execute('SELECT * FROM strategy_performance ORDER BY total_uses DESC')
            rows = cur.fetchall()
        
        outcomes = {}
        for row in rows:
            if row:
                outcomes[row[0]] = StrategyOutcome(
                    strategy_name=row[0],
                    success_count=row[1],
                    failure_count=row[2],
                    avg_confidence=row[3] / row[5] if row[5] > 0 else 0.0,
                    avg_duration_ms=row[4] / row[5] if row[5] > 0 else 0.0,
                    total_uses=row[5],
                    last_used=datetime.fromisoformat(row[6])
                )
        
        return outcomes
    
    def record_growth_metric(self, metric_name: str, value: float, context: Optional[Dict] = None):
        """Record a growth metric."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO growth_metrics (metric_name, value, timestamp, context)
            VALUES (?, ?, ?, ?)
        ''', (metric_name, value, datetime.utcnow().isoformat(), json.dumps(context) if context else None))
        self.conn.commit()
    
    def get_growth_timeline(self, metric_name: str, days: int = 30) -> List[Tuple[datetime, float]]:
        """Get growth timeline for metric."""
        cur = self.conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        cur.execute('''
            SELECT timestamp, value FROM growth_metrics
            WHERE metric_name = ? AND timestamp > ?
            ORDER BY timestamp ASC
        ''', (metric_name, cutoff))
        
        return [(datetime.fromisoformat(row[0]), row[1]) for row in cur.fetchall()]
    
    def add_reflection(self, trigger: str, analysis: str, insights: List[str], 
                      proposed_changes: List[str]) -> int:
        """Add a reflection note."""
        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO reflections (timestamp, trigger, analysis, insights, proposed_changes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.utcnow().isoformat(),
            trigger,
            analysis,
            json.dumps(insights),
            json.dumps(proposed_changes)
        ))
        self.conn.commit()
        return cur.lastrowid
    
    def get_reflections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reflections."""
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM reflections 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        reflections = []
        for row in cur.fetchall():
            reflections.append({
                'id': row[0],
                'timestamp': row[1],
                'trigger': row[2],
                'analysis': row[3],
                'insights': json.loads(row[4]) if row[4] else [],
                'proposed_changes': json.loads(row[5]) if row[5] else []
            })
        
        return reflections
    
    def get_learning_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of learning activity."""
        cur = self.conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Total events
        cur.execute('SELECT COUNT(*) FROM learning_events WHERE timestamp > ?', (cutoff,))
        total_events = cur.fetchone()[0]
        
        # Success rate
        cur.execute('''
            SELECT 
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                COUNT(*) as total
            FROM learning_events 
            WHERE timestamp > ?
        ''', (cutoff,))
        row = cur.fetchone()
        success_rate = row[0] / row[1] if row[1] > 0 else 0.0
        
        # Avg confidence
        cur.execute('SELECT AVG(confidence) FROM learning_events WHERE timestamp > ?', (cutoff,))
        avg_confidence = cur.fetchone()[0] or 0.0
        
        # Event types
        cur.execute('''
            SELECT event_type, COUNT(*) 
            FROM learning_events 
            WHERE timestamp > ?
            GROUP BY event_type
        ''', (cutoff,))
        event_types = dict(cur.fetchall())
        
        # Top strategies
        cur.execute('''
            SELECT method_used, COUNT(*) 
            FROM learning_events 
            WHERE timestamp > ?
            GROUP BY method_used
            ORDER BY COUNT(*) DESC
            LIMIT 5
        ''', (cutoff,))
        top_strategies = dict(cur.fetchall())
        
        return {
            'period_days': days,
            'total_events': total_events,
            'success_rate': success_rate,
            'avg_confidence': avg_confidence,
            'event_types': event_types,
            'top_strategies': top_strategies
        }
    
    def detect_patterns(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """Detect patterns in learning events."""
        cur = self.conn.cursor()
        
        patterns = []
        
        # Pattern: Repeated failures with same method
        cur.execute('''
            SELECT method_used, COUNT(*) as failures
            FROM learning_events
            WHERE success = 0
            GROUP BY method_used
            HAVING failures >= ?
            ORDER BY failures DESC
        ''', (min_occurrences,))
        
        for row in cur.fetchall():
            patterns.append({
                'type': 'repeated_failure',
                'method': row[0],
                'count': row[1],
                'severity': 'high' if row[1] > 10 else 'medium'
            })
        
        # Pattern: Declining confidence over time
        cur.execute('''
            SELECT method_used, AVG(confidence) as avg_conf
            FROM learning_events
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY method_used
        ''')
        
        recent_confidence = dict(cur.fetchall())
        
        cur.execute('''
            SELECT method_used, AVG(confidence) as avg_conf
            FROM learning_events
            WHERE timestamp BETWEEN datetime('now', '-14 days') AND datetime('now', '-7 days')
            GROUP BY method_used
        ''')
        
        older_confidence = dict(cur.fetchall())
        
        for method, recent_conf in recent_confidence.items():
            if method in older_confidence:
                decline = older_confidence[method] - recent_conf
                if decline > 0.1:  # 10% decline
                    patterns.append({
                        'type': 'confidence_decline',
                        'method': method,
                        'decline': decline,
                        'severity': 'high' if decline > 0.2 else 'medium'
                    })
        
        return patterns
    
    def close(self):
        """Close database connection."""
        self.conn.close()
