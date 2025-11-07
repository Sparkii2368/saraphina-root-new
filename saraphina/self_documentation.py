#!/usr/bin/env python3
"""
Self-Documentation System - Saraphina documents her own changes.

Tracks:
- WHAT: What changed (files, functions, features)
- WHY: Why it changed (purpose, problem solved)
- HOW: How it was done (techniques, patterns, approach)
- LEARN: What she learned and can replicate
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib


class SelfDocumentation:
    """Automatically document all modifications."""
    
    def __init__(self, db):
        """Initialize self-documentation system."""
        self.db = db
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create modification_history table."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS modification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                phase TEXT,
                what TEXT NOT NULL,
                why TEXT NOT NULL,
                how TEXT NOT NULL,
                files_changed TEXT,
                techniques_used TEXT,
                patterns_applied TEXT,
                lessons_learned TEXT,
                can_replicate BOOLEAN DEFAULT 1,
                complexity_score REAL,
                success BOOLEAN DEFAULT 1,
                metadata TEXT
            )
        """)
        
        # Index for fast searching
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mod_history_phase
            ON modification_history(phase)
        """)
        
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mod_history_timestamp
            ON modification_history(timestamp DESC)
        """)
        
        self.db.commit()
    
    def document_change(
        self,
        what: str,
        why: str,
        how: str,
        phase: Optional[str] = None,
        files_changed: Optional[List[str]] = None,
        techniques: Optional[List[str]] = None,
        patterns: Optional[List[str]] = None,
        lessons: Optional[List[str]] = None,
        can_replicate: bool = True,
        complexity: float = 0.5,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Document a change Saraphina made.
        
        Args:
            what: What changed (high-level description)
            why: Why it changed (purpose, motivation)
            how: How it was implemented (approach, steps)
            phase: Phase identifier (e.g., "Phase 30")
            files_changed: List of files modified
            techniques: Programming techniques used
            patterns: Design patterns applied
            lessons: What was learned
            can_replicate: Whether Saraphina can do this herself next time
            complexity: Complexity score 0-1
            success: Whether change was successful
            metadata: Additional structured data
        
        Returns:
            Entry ID
        """
        timestamp = datetime.now().isoformat()
        
        # Serialize lists
        files_str = json.dumps(files_changed) if files_changed else None
        techniques_str = json.dumps(techniques) if techniques else None
        patterns_str = json.dumps(patterns) if patterns else None
        lessons_str = json.dumps(lessons) if lessons else None
        metadata_str = json.dumps(metadata) if metadata else None
        
        cursor = self.db.execute("""
            INSERT INTO modification_history (
                timestamp, phase, what, why, how,
                files_changed, techniques_used, patterns_applied,
                lessons_learned, can_replicate, complexity_score,
                success, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, phase, what, why, how,
            files_str, techniques_str, patterns_str,
            lessons_str, can_replicate, complexity,
            success, metadata_str
        ))
        
        self.db.commit()
        return cursor.lastrowid
    
    def get_history(
        self,
        phase: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get modification history."""
        if phase:
            query = "SELECT * FROM modification_history WHERE phase = ? ORDER BY timestamp DESC LIMIT ?"
            params = (phase, limit)
        else:
            query = "SELECT * FROM modification_history ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)
        
        rows = self.db.execute(query, params).fetchall()
        
        results = []
        for row in rows:
            entry = dict(row)
            # Deserialize JSON fields
            for field in ['files_changed', 'techniques_used', 'patterns_applied', 'lessons_learned', 'metadata']:
                if entry.get(field):
                    entry[field] = json.loads(entry[field])
            results.append(entry)
        
        return results
    
    def search_history(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search modification history."""
        sql = """
            SELECT * FROM modification_history
            WHERE what LIKE ? OR why LIKE ? OR how LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        """
        pattern = f'%{query}%'
        rows = self.db.execute(sql, (pattern, pattern, pattern, limit)).fetchall()
        
        results = []
        for row in rows:
            entry = dict(row)
            for field in ['files_changed', 'techniques_used', 'patterns_applied', 'lessons_learned', 'metadata']:
                if entry.get(field):
                    entry[field] = json.loads(entry[field])
            results.append(entry)
        
        return results
    
    def get_replicable_modifications(self) -> List[Dict[str, Any]]:
        """Get modifications Saraphina can replicate herself."""
        rows = self.db.execute("""
            SELECT * FROM modification_history
            WHERE can_replicate = 1 AND success = 1
            ORDER BY timestamp DESC
        """).fetchall()
        
        results = []
        for row in rows:
            entry = dict(row)
            for field in ['files_changed', 'techniques_used', 'patterns_applied', 'lessons_learned', 'metadata']:
                if entry.get(field):
                    entry[field] = json.loads(entry[field])
            results.append(entry)
        
        return results
    
    def get_techniques_used(self) -> Dict[str, int]:
        """Get frequency of techniques used."""
        techniques_count = {}
        
        rows = self.db.execute("""
            SELECT techniques_used FROM modification_history
            WHERE techniques_used IS NOT NULL
        """).fetchall()
        
        for row in rows:
            techniques = json.loads(row['techniques_used'])
            for technique in techniques:
                techniques_count[technique] = techniques_count.get(technique, 0) + 1
        
        return dict(sorted(techniques_count.items(), key=lambda x: x[1], reverse=True))
    
    def get_patterns_applied(self) -> Dict[str, int]:
        """Get frequency of design patterns applied."""
        patterns_count = {}
        
        rows = self.db.execute("""
            SELECT patterns_applied FROM modification_history
            WHERE patterns_applied IS NOT NULL
        """).fetchall()
        
        for row in rows:
            patterns = json.loads(row['patterns_applied'])
            for pattern in patterns:
                patterns_count[pattern] = patterns_count.get(pattern, 0) + 1
        
        return dict(sorted(patterns_count.items(), key=lambda x: x[1], reverse=True))
    
    def get_lessons_learned(self) -> List[str]:
        """Get all lessons learned."""
        lessons = []
        
        rows = self.db.execute("""
            SELECT lessons_learned, timestamp FROM modification_history
            WHERE lessons_learned IS NOT NULL
            ORDER BY timestamp DESC
        """).fetchall()
        
        for row in rows:
            lesson_list = json.loads(row['lessons_learned'])
            lessons.extend(lesson_list)
        
        return lessons
    
    def format_entry(self, entry: Dict[str, Any]) -> str:
        """Format single modification entry."""
        output = f"📝 {entry['what']}\n"
        output += f"   Phase: {entry.get('phase', 'unknown')}\n"
        output += f"   When: {entry['timestamp'][:19]}\n\n"
        
        output += f"❓ Why:\n   {entry['why']}\n\n"
        output += f"🔧 How:\n   {entry['how']}\n\n"
        
        if entry.get('files_changed'):
            output += f"📁 Files: {', '.join(entry['files_changed'][:3])}\n\n"
        
        if entry.get('techniques_used'):
            output += f"⚡ Techniques: {', '.join(entry['techniques_used'])}\n\n"
        
        if entry.get('patterns_applied'):
            output += f"🎯 Patterns: {', '.join(entry['patterns_applied'])}\n\n"
        
        if entry.get('lessons_learned'):
            output += f"💡 Lessons:\n"
            for lesson in entry['lessons_learned']:
                output += f"   • {lesson}\n"
            output += "\n"
        
        replicable = "✅ Yes" if entry.get('can_replicate') else "❌ No"
        output += f"🔄 Can Replicate: {replicable}\n"
        output += f"📊 Complexity: {entry.get('complexity_score', 0):.1f}/1.0\n"
        
        return output
    
    def generate_summary(self) -> str:
        """Generate summary of all modifications."""
        total = self.db.execute("SELECT COUNT(*) as cnt FROM modification_history").fetchone()['cnt']
        
        if total == 0:
            return "No modifications documented yet."
        
        successful = self.db.execute(
            "SELECT COUNT(*) as cnt FROM modification_history WHERE success = 1"
        ).fetchone()['cnt']
        
        replicable = self.db.execute(
            "SELECT COUNT(*) as cnt FROM modification_history WHERE can_replicate = 1 AND success = 1"
        ).fetchone()['cnt']
        
        # Get phases
        phases = self.db.execute("""
            SELECT phase, COUNT(*) as cnt FROM modification_history
            WHERE phase IS NOT NULL
            GROUP BY phase
            ORDER BY cnt DESC
        """).fetchall()
        
        output = "📊 Self-Modification Summary\n\n"
        output += f"Total Modifications: {total}\n"
        output += f"Successful: {successful} ({successful/total:.1%})\n"
        output += f"Replicable: {replicable} ({replicable/total:.1%})\n\n"
        
        if phases:
            output += "By Phase:\n"
            for phase_row in phases[:5]:
                output += f"  • {phase_row['phase']}: {phase_row['cnt']} changes\n"
            output += "\n"
        
        # Top techniques
        techniques = self.get_techniques_used()
        if techniques:
            output += "Top Techniques:\n"
            for tech, count in list(techniques.items())[:5]:
                output += f"  • {tech}: {count}x\n"
            output += "\n"
        
        # Top patterns
        patterns = self.get_patterns_applied()
        if patterns:
            output += "Top Patterns:\n"
            for pattern, count in list(patterns.items())[:5]:
                output += f"  • {pattern}: {count}x\n"
        
        return output
