#!/usr/bin/env python3
"""
RecursiveCodeMiner - Endlessly expand programming knowledge via GPT-4o.

Queries for new concepts, languages, frameworks, paradigms and recursively
explores prerequisites and related topics until knowledge is comprehensive.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import os
import time
import json

from .code_knowledge_db import CodeKnowledgeDB


class RecursiveCodeMiner:
    """Continuously mine programming knowledge using GPT-4o."""

    def __init__(self, code_kb: CodeKnowledgeDB):
        self.code_kb = code_kb
        self.gpt4_available = self._check_gpt4()
        self.explored_concepts: Set[str] = set()
        self.exploration_queue: List[str] = []

    def _check_gpt4(self) -> bool:
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                return True
        except Exception:
            pass
        return False

    def seed_topics(self) -> List[str]:
        """Core programming topics to seed exploration."""
        return [
            # Paradigms
            "object-oriented programming", "functional programming", "procedural programming",
            "declarative programming", "reactive programming",
            
            # Languages
            "Python", "JavaScript", "TypeScript", "Go", "Rust", "C++", "Java", "C#",
            "Ruby", "PHP", "Swift", "Kotlin", "Scala", "Haskell", "Elixir",
            
            # Core concepts
            "data structures", "algorithms", "design patterns", "SOLID principles",
            "concurrency", "asynchronous programming", "memory management",
            
            # Frameworks/Ecosystems
            "React", "Vue", "Angular", "Django", "Flask", "FastAPI", "Express",
            "Spring", "ASP.NET", "Rails", "Laravel",
            
            # Databases
            "SQL", "NoSQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            
            # DevOps
            "Docker", "Kubernetes", "CI/CD", "AWS", "Azure", "GCP",
            "Terraform", "Ansible",
            
            # Advanced topics
            "distributed systems", "microservices", "event-driven architecture",
            "CQRS", "domain-driven design", "clean architecture"
        ]

    def expand_all(
        self,
        max_concepts: int = 100,
        max_depth: int = 3,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Recursively expand knowledge base.
        
        Args:
            max_concepts: Max new concepts to learn in this session
            max_depth: Max recursion depth for prerequisites
            focus_areas: Specific topics to focus on (None = all topics)
        
        Returns:
            Summary of what was learned
        """
        if not self.gpt4_available:
            return {'success': False, 'error': 'GPT-4o not available'}

        start_time = time.time()
        
        # Initialize queue with seed topics or focus areas
        if focus_areas:
            self.exploration_queue = focus_areas.copy()
        else:
            self.exploration_queue = self.seed_topics().copy()
        
        concepts_learned = []
        concepts_explored = 0

        try:
            while self.exploration_queue and concepts_explored < max_concepts:
                topic = self.exploration_queue.pop(0)
                
                if topic.lower() in self.explored_concepts:
                    continue
                
                self.explored_concepts.add(topic.lower())
                
                # Learn about this topic
                result = self._learn_topic(topic, current_depth=0, max_depth=max_depth)
                
                if result.get('success'):
                    concepts_learned.append({
                        'topic': topic,
                        'concepts_created': result.get('concepts_created', 0),
                        'depth_explored': result.get('depth_explored', 0)
                    })
                    concepts_explored += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            duration = time.time() - start_time
            
            return {
                'success': True,
                'concepts_explored': concepts_explored,
                'concepts_learned': concepts_learned,
                'duration_seconds': duration,
                'queue_remaining': len(self.exploration_queue)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'concepts_explored': concepts_explored,
                'duration_seconds': time.time() - start_time
            }

    def _learn_topic(
        self,
        topic: str,
        current_depth: int,
        max_depth: int
    ) -> Dict[str, Any]:
        """
        Learn about a single topic via GPT-4o, recursively exploring prerequisites.
        """
        if current_depth >= max_depth:
            return {'success': True, 'concepts_created': 0, 'depth_explored': current_depth}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Query GPT-4o for comprehensive knowledge
            prompt = f"""Explain the programming concept: {topic}

Provide:
1. Clear definition
2. Key characteristics
3. Common use cases
4. Prerequisites (what you need to know first)
5. Related concepts
6. Difficulty level (1=beginner, 2=intermediate, 3=advanced, 4=expert)
7. Programming language (if language-specific, otherwise "language-agnostic")
8. Simple code example (if applicable)

Format as JSON:
{{
  "name": "{topic}",
  "category": "language|pattern|paradigm|syntax|library|framework|tool",
  "language": "python|javascript|etc or null",
  "description": "...",
  "prerequisites": ["concept1", "concept2"],
  "related_concepts": ["concept1", "concept2"],
  "difficulty": 1-4,
  "example": "code snippet or null"
}}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a programming knowledge expert. Provide accurate, concise explanations in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content or ""
            
            # Parse JSON response
            try:
                # Extract JSON from code blocks if present
                import re
                json_match = re.search(r'```(?:json)?\n(.+?)\n```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                
                concept_data = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback: manual parsing
                concept_data = {
                    'name': topic,
                    'category': 'concept',
                    'language': None,
                    'description': content[:500],
                    'prerequisites': [],
                    'related_concepts': [],
                    'difficulty': 2,
                    'example': None
                }

            # Store in database
            concept_id = self.code_kb.store_concept(
                name=concept_data.get('name', topic),
                category=concept_data.get('category', 'concept'),
                description=concept_data.get('description', ''),
                language=concept_data.get('language'),
                examples=[concept_data.get('example')] if concept_data.get('example') else None,
                prerequisites=concept_data.get('prerequisites', []),
                difficulty=concept_data.get('difficulty', 2),
                learned_from='gpt4o_recursive_mining'
            )

            # Link to related concepts
            for related in concept_data.get('related_concepts', []):
                # Note: we'll create placeholder IDs; they'll be resolved when we learn those concepts
                self.code_kb.link_concepts(
                    concept_id,
                    f"placeholder_{related.lower().replace(' ', '_')}",
                    'related_to',
                    strength=0.7
                )

            # Add prerequisites to exploration queue for recursive learning
            prerequisites = concept_data.get('prerequisites', [])
            if prerequisites and current_depth < max_depth - 1:
                for prereq in prerequisites:
                    if prereq.lower() not in self.explored_concepts:
                        self.exploration_queue.append(prereq)

            # Add related concepts to queue (lower priority)
            related = concept_data.get('related_concepts', [])
            for rel in related[:2]:  # Only add top 2 related
                if rel.lower() not in self.explored_concepts:
                    self.exploration_queue.append(rel)

            return {
                'success': True,
                'concept_id': concept_id,
                'concepts_created': 1,
                'depth_explored': current_depth,
                'prerequisites_queued': len(prerequisites)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'concepts_created': 0
            }

    def get_expansion_stats(self) -> Dict[str, Any]:
        """Get current knowledge expansion statistics."""
        cur = self.code_kb.conn.cursor()
        
        stats = {}
        
        # Total concepts by category
        cur.execute("SELECT category, COUNT(*) FROM code_concepts GROUP BY category")
        stats['by_category'] = dict(cur.fetchall())
        
        # Total concepts by language
        cur.execute("SELECT language, COUNT(*) FROM code_concepts WHERE language IS NOT NULL GROUP BY language")
        stats['by_language'] = dict(cur.fetchall())
        
        # Total concepts by difficulty
        cur.execute("SELECT difficulty, COUNT(*) FROM code_concepts GROUP BY difficulty")
        stats['by_difficulty'] = dict(cur.fetchall())
        
        # Total concepts
        cur.execute("SELECT COUNT(*) FROM code_concepts")
        stats['total_concepts'] = cur.fetchone()[0]
        
        # Total links
        cur.execute("SELECT COUNT(*) FROM concept_links")
        stats['total_links'] = cur.fetchone()[0]
        
        # Recent learning
        cur.execute("""
            SELECT COUNT(*) FROM code_concepts 
            WHERE datetime(created_at) > datetime('now', '-7 days')
        """)
        stats['learned_this_week'] = cur.fetchone()[0]
        
        return stats
