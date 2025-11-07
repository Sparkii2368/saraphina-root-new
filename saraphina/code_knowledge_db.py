#!/usr/bin/env python3
"""
CodeKnowledgeDB - Programming concepts, patterns, and snippets knowledge base.

Stores everything Saraphina learns about code:
- Programming concepts (classes, functions, recursion, etc.)
- Language features (Python syntax, JavaScript async, etc.)
- Design patterns (singleton, observer, factory, etc.)
- Code snippets with context
- Dependencies and relationships between concepts
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sqlite3


class CodeKnowledgeDB:
    """Storage and retrieval for programming knowledge."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_schema()
    
    def _init_schema(self):
        """Initialize code knowledge tables."""
        cur = self.conn.cursor()
        
        # Programming concepts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS code_concepts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,  -- language, pattern, paradigm, syntax, library
                language TEXT,  -- python, javascript, go, etc. (NULL for language-agnostic)
                description TEXT,
                examples TEXT,  -- JSON array of code examples
                prerequisites TEXT,  -- JSON array of concept IDs
                related_concepts TEXT,  -- JSON array of concept IDs
                difficulty INTEGER DEFAULT 1,  -- 1=beginner, 2=intermediate, 3=advanced, 4=expert
                learned_from TEXT,  -- gpt4o_research, human_teaching, self_discovery
                confidence REAL DEFAULT 0.8,
                usage_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Code snippets table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS code_snippets (
                id TEXT PRIMARY KEY,
                concept_id TEXT,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                input_example TEXT,  -- JSON
                output_example TEXT,  -- JSON
                complexity TEXT,  -- time/space complexity
                tags TEXT,  -- JSON array
                works BOOLEAN DEFAULT TRUE,  -- tested and verified
                test_results TEXT,  -- JSON test output
                created_at TEXT NOT NULL,
                FOREIGN KEY (concept_id) REFERENCES code_concepts(id)
            )
        """)
        
        # Concept relationships (graph)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS concept_links (
                from_concept TEXT NOT NULL,
                to_concept TEXT NOT NULL,
                relationship TEXT NOT NULL,  -- prerequisite, implements, uses, similar_to, extends
                strength REAL DEFAULT 0.5,  -- 0.0-1.0
                notes TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY (from_concept, to_concept, relationship),
                FOREIGN KEY (from_concept) REFERENCES code_concepts(id),
                FOREIGN KEY (to_concept) REFERENCES code_concepts(id)
            )
        """)
        
        # Learning path tracking
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_paths (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                goal TEXT,
                concepts TEXT,  -- JSON ordered array of concept IDs
                current_position INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        
        # Code understanding logs (tracks what she's learning)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS code_learning_log (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                concept_id TEXT,
                learned_facts INTEGER DEFAULT 0,
                depth INTEGER DEFAULT 1,  -- recursion depth
                success BOOLEAN DEFAULT TRUE,
                error TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (concept_id) REFERENCES code_concepts(id)
            )
        """)
        
        self.conn.commit()
        
        # Create indexes (after tables are committed)
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_concepts_category ON code_concepts(category)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_concepts_language ON code_concepts(language)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_concepts_difficulty ON code_concepts(difficulty)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snippets_language ON code_snippets(language)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snippets_concept ON code_snippets(concept_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_links_from ON concept_links(from_concept)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_links_to ON concept_links(to_concept)")
            self.conn.commit()
        except Exception as e:
            # Indexes might already exist or tables not ready
            pass
    
    def store_concept(
        self, 
        name: str, 
        category: str, 
        description: str,
        language: Optional[str] = None,
        examples: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        difficulty: int = 1,
        learned_from: str = "gpt4o_research",
        confidence: float = 0.8
    ) -> str:
        """Store a programming concept."""
        import uuid
        concept_id = f"concept_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO code_concepts 
            (id, name, category, language, description, examples, prerequisites, 
             difficulty, learned_from, confidence, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            concept_id, name, category, language, description,
            json.dumps(examples or [], ensure_ascii=False),
            json.dumps(prerequisites or [], ensure_ascii=False),
            difficulty, learned_from, confidence, now, now
        ))
        self.conn.commit()
        return concept_id
    
    def store_snippet(
        self,
        concept_id: Optional[str],
        language: str,
        code: str,
        description: str,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store a code snippet."""
        import uuid
        snippet_id = f"snippet_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO code_snippets
            (id, concept_id, language, code, description, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snippet_id, concept_id, language, code, description,
            json.dumps(tags or [], ensure_ascii=False), now
        ))
        self.conn.commit()
        return snippet_id
    
    def link_concepts(
        self,
        from_concept: str,
        to_concept: str,
        relationship: str,
        strength: float = 0.5,
        notes: Optional[str] = None
    ):
        """Create a relationship between two concepts."""
        now = datetime.now().isoformat()
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO concept_links
            (from_concept, to_concept, relationship, strength, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (from_concept, to_concept, relationship, strength, notes, now))
        self.conn.commit()
    
    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a concept by ID."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, name, category, language, description, examples, 
                   prerequisites, related_concepts, difficulty, learned_from,
                   confidence, usage_count, last_accessed, created_at
            FROM code_concepts WHERE id = ?
        """, (concept_id,))
        
        row = cur.fetchone()
        if not row:
            return None
        
        # Update last_accessed
        cur.execute("UPDATE code_concepts SET last_accessed = ? WHERE id = ?", 
                   (datetime.now().isoformat(), concept_id))
        self.conn.commit()
        
        return {
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'language': row[3],
            'description': row[4],
            'examples': json.loads(row[5] or '[]'),
            'prerequisites': json.loads(row[6] or '[]'),
            'related_concepts': json.loads(row[7] or '[]'),
            'difficulty': row[8],
            'learned_from': row[9],
            'confidence': row[10],
            'usage_count': row[11],
            'last_accessed': row[12],
            'created_at': row[13]
        }
    
    def search_concepts(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        difficulty: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for concepts by various criteria."""
        cur = self.conn.cursor()
        
        sql = "SELECT id, name, category, language, description, difficulty, confidence FROM code_concepts WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if category:
            sql += " AND category = ?"
            params.append(category)
        if language:
            sql += " AND (language = ? OR language IS NULL)"
            params.append(language)
        if difficulty:
            sql += " AND difficulty <= ?"
            params.append(difficulty)
        
        sql += " ORDER BY usage_count DESC, confidence DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(sql, params)
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'language': row[3],
                'description': row[4],
                'difficulty': row[5],
                'confidence': row[6]
            })
        return results
    
    def get_related_concepts(self, concept_id: str, relationship: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get concepts related to this one."""
        cur = self.conn.cursor()
        
        sql = """
            SELECT c.id, c.name, c.category, c.language, l.relationship, l.strength
            FROM concept_links l
            JOIN code_concepts c ON l.to_concept = c.id
            WHERE l.from_concept = ?
        """
        params = [concept_id]
        
        if relationship:
            sql += " AND l.relationship = ?"
            params.append(relationship)
        
        sql += " ORDER BY l.strength DESC"
        
        cur.execute(sql, params)
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'language': row[3],
                'relationship': row[4],
                'strength': row[5]
            })
        return results
    
    def log_learning(
        self,
        query: str,
        concept_id: Optional[str] = None,
        learned_facts: int = 0,
        depth: int = 1,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: int = 0
    ) -> str:
        """Log a code learning event."""
        import uuid
        log_id = f"log_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO code_learning_log
            (id, query, concept_id, learned_facts, depth, success, error, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, query, concept_id, learned_facts, depth, success, error, duration_ms, now))
        self.conn.commit()
        return log_id
    
    def get_stats(self) -> Dict[str, Any]:
        """Get code knowledge statistics."""
        cur = self.conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM code_concepts")
        total_concepts = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM code_snippets")
        total_snippets = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT language) FROM code_concepts WHERE language IS NOT NULL")
        languages_learned = cur.fetchone()[0]
        
        cur.execute("SELECT category, COUNT(*) FROM code_concepts GROUP BY category")
        by_category = dict(cur.fetchall())
        
        cur.execute("SELECT AVG(difficulty) FROM code_concepts")
        avg_difficulty = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COUNT(*) FROM code_learning_log WHERE success = TRUE")
        successful_learning_events = cur.fetchone()[0]
        
        return {
            'total_concepts': total_concepts,
            'total_snippets': total_snippets,
            'languages_learned': languages_learned,
            'by_category': by_category,
            'avg_difficulty': round(avg_difficulty, 2),
            'successful_learning_events': successful_learning_events
        }
