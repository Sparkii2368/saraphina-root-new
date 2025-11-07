#!/usr/bin/env python3
"""
Upgrade Learning Journal - Logs upgrade attempts and learns from failures

This is Saraphina's memory system for self-modification. She learns from:
1. Failed upgrades (what went wrong)
2. Successful upgrades (what patterns work)
3. Common mistakes (circular imports, wrong files, etc.)
"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger("LearningJournal")


@dataclass
class UpgradeAttempt:
    """Record of a single upgrade attempt"""
    request: str
    spec_json: str
    code_generated: str
    validation_result: str
    success: bool
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    artifact_id: Optional[str] = None
    patterns_learned: Optional[str] = None  # JSON list of learned patterns
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class UpgradeLearningJournal:
    """Logs and learns from upgrade attempts"""
    
    def __init__(self, db_path: str = "D:\\Saraphina Root\\data\\upgrade_journal.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        logger.info(f"Learning Journal initialized: {self.db_path}")
    
    def _init_database(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main upgrade attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upgrade_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request TEXT NOT NULL,
                spec_json TEXT,
                code_generated TEXT,
                validation_result TEXT,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                timestamp TEXT NOT NULL,
                artifact_id TEXT,
                patterns_learned TEXT
            )
        """)
        
        # Pattern library table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                times_seen INTEGER DEFAULT 1,
                last_seen TEXT NOT NULL,
                notes TEXT
            )
        """)
        
        # Indexes for fast lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_request 
            ON upgrade_attempts(request)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_success 
            ON upgrade_attempts(success)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_type 
            ON learned_patterns(pattern_type)
        """)
        
        conn.commit()
        conn.close()
    
    def log_attempt(self, attempt: UpgradeAttempt) -> int:
        """
        Log an upgrade attempt
        
        Returns:
            ID of the logged attempt
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO upgrade_attempts 
            (request, spec_json, code_generated, validation_result, success, 
             error_message, timestamp, artifact_id, patterns_learned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt.request,
            attempt.spec_json,
            attempt.code_generated,
            attempt.validation_result,
            attempt.success,
            attempt.error_message,
            attempt.timestamp,
            attempt.artifact_id,
            attempt.patterns_learned
        ))
        
        attempt_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        if attempt.success:
            logger.info(f"✓ Logged successful upgrade: {attempt_id}")
        else:
            logger.warning(f"✗ Logged failed upgrade: {attempt_id} - {attempt.error_message}")
        
        # Extract and learn patterns
        if not attempt.success:
            self._learn_from_failure(attempt)
        else:
            self._learn_from_success(attempt)
        
        return attempt_id
    
    def _learn_from_failure(self, attempt: UpgradeAttempt):
        """Extract patterns from failed attempts"""
        patterns = []
        
        # Parse error message for common issues
        if attempt.error_message:
            error_lower = attempt.error_message.lower()
            
            # Circular import
            if 'circular' in error_lower or 'import' in error_lower:
                patterns.append({
                    'type': 'error_pattern',
                    'pattern': 'circular_import',
                    'context': f"Request: {attempt.request[:100]}"
                })
            
            # Wrong file modified
            if 'wrong file' in error_lower or 'incorrect file' in error_lower:
                patterns.append({
                    'type': 'error_pattern',
                    'pattern': 'wrong_file_modified',
                    'context': f"Request: {attempt.request[:100]}"
                })
            
            # Missing dependencies
            if 'importerror' in error_lower or 'no module' in error_lower:
                patterns.append({
                    'type': 'error_pattern',
                    'pattern': 'missing_dependency',
                    'context': f"Request: {attempt.request[:100]}"
                })
        
        # Parse spec to learn what request wanted
        if attempt.spec_json:
            try:
                spec = json.loads(attempt.spec_json)
                
                # Learn request -> feature mapping
                patterns.append({
                    'type': 'request_to_feature',
                    'request': attempt.request[:200],
                    'feature': spec.get('feature_name', 'unknown'),
                    'modules': spec.get('modules', []),
                    'success': False
                })
                
            except:
                pass
        
        # Store patterns
        for pattern in patterns:
            self._record_pattern(
                pattern_type=pattern['type'],
                pattern_data=json.dumps(pattern),
                notes=f"Learned from failed attempt"
            )
    
    def _learn_from_success(self, attempt: UpgradeAttempt):
        """Extract patterns from successful attempts"""
        patterns = []
        
        # Parse spec to learn what works
        if attempt.spec_json:
            try:
                spec = json.loads(attempt.spec_json)
                
                # Learn request -> feature mapping
                patterns.append({
                    'type': 'request_to_feature',
                    'request': attempt.request[:200],
                    'feature': spec.get('feature_name', 'unknown'),
                    'modules': spec.get('modules', []),
                    'modifications': spec.get('modifications', []),
                    'success': True
                })
                
                # Learn module patterns
                for module in spec.get('modules', []):
                    patterns.append({
                        'type': 'module_pattern',
                        'module_name': module,
                        'feature': spec.get('feature_name', 'unknown'),
                        'requirements': spec.get('requirements', [])
                    })
                
            except:
                pass
        
        # Store patterns with higher confidence
        for pattern in patterns:
            self._record_pattern(
                pattern_type=pattern['type'],
                pattern_data=json.dumps(pattern),
                confidence=0.8,  # Higher confidence for successful attempts
                notes=f"Learned from successful attempt"
            )
    
    def _record_pattern(self, pattern_type: str, pattern_data: str, 
                       confidence: float = 0.5, notes: str = ""):
        """Record a learned pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if pattern already exists
        cursor.execute("""
            SELECT id, times_seen, confidence 
            FROM learned_patterns 
            WHERE pattern_type = ? AND pattern_data = ?
        """, (pattern_type, pattern_data))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing pattern
            pattern_id, times_seen, old_confidence = existing
            new_times_seen = times_seen + 1
            new_confidence = min(1.0, old_confidence + 0.1)  # Increase confidence
            
            cursor.execute("""
                UPDATE learned_patterns 
                SET times_seen = ?, confidence = ?, last_seen = ?
                WHERE id = ?
            """, (new_times_seen, new_confidence, datetime.now().isoformat(), pattern_id))
            
            logger.debug(f"Updated pattern {pattern_id}: confidence {new_confidence:.2f}, seen {new_times_seen}x")
        else:
            # Insert new pattern
            cursor.execute("""
                INSERT INTO learned_patterns 
                (pattern_type, pattern_data, confidence, times_seen, last_seen, notes)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (pattern_type, pattern_data, confidence, datetime.now().isoformat(), notes))
            
            logger.debug(f"Recorded new pattern: {pattern_type}")
        
        conn.commit()
        conn.close()
    
    def get_similar_attempts(self, request: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar past upgrade attempts
        
        Simple similarity: check if key words match
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract key words from request
        keywords = self._extract_keywords(request)
        
        # Search for attempts with similar keywords
        results = []
        
        for keyword in keywords:
            cursor.execute("""
                SELECT id, request, success, error_message, artifact_id, timestamp
                FROM upgrade_attempts
                WHERE request LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f'%{keyword}%', limit))
            
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'request': row[1],
                    'success': row[2],
                    'error_message': row[3],
                    'artifact_id': row[4],
                    'timestamp': row[5]
                })
        
        conn.close()
        
        # Remove duplicates, keep most recent
        unique_results = {}
        for r in results:
            if r['id'] not in unique_results:
                unique_results[r['id']] = r
        
        return list(unique_results.values())[:limit]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction
        important_words = [
            'voice', 'speech', 'audio', 'listen', 'hear', 'speak',
            'module', 'feature', 'upgrade', 'add', 'create', 'build',
            'gui', 'interface', 'window', 'button',
            'stt', 'tts', 'recognition', 'synthesis'
        ]
        
        text_lower = text.lower()
        keywords = [word for word in important_words if word in text_lower]
        
        return keywords
    
    def get_patterns(self, pattern_type: str = None, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Get learned patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute("""
                SELECT pattern_type, pattern_data, confidence, times_seen, last_seen, notes
                FROM learned_patterns
                WHERE pattern_type = ? AND confidence >= ?
                ORDER BY confidence DESC, times_seen DESC
            """, (pattern_type, min_confidence))
        else:
            cursor.execute("""
                SELECT pattern_type, pattern_data, confidence, times_seen, last_seen, notes
                FROM learned_patterns
                WHERE confidence >= ?
                ORDER BY confidence DESC, times_seen DESC
            """, (min_confidence,))
        
        patterns = []
        for row in cursor.fetchall():
            try:
                pattern_data = json.loads(row[1])
            except:
                pattern_data = row[1]
            
            patterns.append({
                'type': row[0],
                'data': pattern_data,
                'confidence': row[2],
                'times_seen': row[3],
                'last_seen': row[4],
                'notes': row[5]
            })
        
        conn.close()
        return patterns
    
    def get_stats(self) -> Dict[str, Any]:
        """Get journal statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total attempts
        cursor.execute("SELECT COUNT(*) FROM upgrade_attempts")
        total_attempts = cursor.fetchone()[0]
        
        # Successful attempts
        cursor.execute("SELECT COUNT(*) FROM upgrade_attempts WHERE success = 1")
        successful = cursor.fetchone()[0]
        
        # Failed attempts
        failed = total_attempts - successful
        
        # Total patterns learned
        cursor.execute("SELECT COUNT(*) FROM learned_patterns")
        total_patterns = cursor.fetchone()[0]
        
        # High confidence patterns
        cursor.execute("SELECT COUNT(*) FROM learned_patterns WHERE confidence >= 0.8")
        high_confidence = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_attempts': total_attempts,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_attempts if total_attempts > 0 else 0,
            'total_patterns': total_patterns,
            'high_confidence_patterns': high_confidence
        }
    
    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failed attempts for debugging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, request, error_message, timestamp, artifact_id
            FROM upgrade_attempts
            WHERE success = 0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        failures = []
        for row in cursor.fetchall():
            failures.append({
                'id': row[0],
                'request': row[1],
                'error': row[2],
                'timestamp': row[3],
                'artifact_id': row[4]
            })
        
        conn.close()
        return failures


# CLI for viewing journal
if __name__ == "__main__":
    import sys
    
    journal = UpgradeLearningJournal()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            stats = journal.get_stats()
            print("\n" + "="*60)
            print("LEARNING JOURNAL STATISTICS")
            print("="*60)
            print(f"Total Attempts: {stats['total_attempts']}")
            print(f"  Successful: {stats['successful']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            print(f"\nPatterns Learned: {stats['total_patterns']}")
            print(f"  High Confidence: {stats['high_confidence_patterns']}")
            print("="*60)
        
        elif command == "failures":
            failures = journal.get_recent_failures(limit=5)
            print("\n" + "="*60)
            print("RECENT FAILURES")
            print("="*60)
            for f in failures:
                print(f"\n[{f['timestamp']}] {f['request'][:80]}")
                print(f"  Error: {f['error'][:200]}")
            print("="*60)
        
        elif command == "patterns":
            patterns = journal.get_patterns(min_confidence=0.6)
            print("\n" + "="*60)
            print("LEARNED PATTERNS")
            print("="*60)
            for p in patterns[:10]:
                print(f"\n{p['type']} (confidence: {p['confidence']:.2f}, seen: {p['times_seen']}x)")
                print(f"  {p['data']}")
            print("="*60)
    else:
        print("Usage: python upgrade_learning_journal.py [stats|failures|patterns]")
