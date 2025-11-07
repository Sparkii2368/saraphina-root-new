#!/usr/bin/env python3
"""
CodeResearchAgent - Recursive GPT-4o code learning system.

Saraphina queries GPT-4o to learn about programming concepts, then stores
everything in her CodeKnowledgeDB. Supports recursive depth-first exploration.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import re
import time

from .code_knowledge_db import CodeKnowledgeDB


class CodeResearchAgent:
    """Autonomous code learning through GPT-4o queries."""
    
    def __init__(self, code_kb: CodeKnowledgeDB):
        self.code_kb = code_kb
        self.gpt4_available = self._check_gpt4()
    
    def _check_gpt4(self) -> bool:
        """Check if GPT-4o is available."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                return True
        except Exception:
            pass
        return False
    
    def learn_concept(
        self,
        concept_name: str,
        language: Optional[str] = None,
        depth: int = 1,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Learn about a programming concept recursively.
        
        Args:
            concept_name: What to learn (e.g., "Python classes", "recursion", "async/await")
            language: Specific language context (optional)
            depth: Current recursion depth
            max_depth: Maximum depth to explore
        
        Returns:
            Dict with concept_id, learned_facts, prerequisites, and subtopics
        """
        start_time = time.time()
        
        # Check if already learned
        existing = self.code_kb.search_concepts(query=concept_name, language=language, limit=1)
        if existing:
            return {
                'concept_id': existing[0]['id'],
                'already_known': True,
                'learned_facts': 0,
                'message': f"Already know about {concept_name}"
            }
        
        if not self.gpt4_available:
            return {
                'success': False,
                'error': 'GPT-4o not available',
                'learned_facts': 0
            }
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Build research prompt
            lang_context = f" in {language}" if language else ""
            prompt = f"""Research the programming concept: {concept_name}{lang_context}

Provide a comprehensive explanation with:

1. **Core Definition** (2-3 sentences)
   What is it? Why does it exist?

2. **Key Characteristics** (3-5 bullet points)
   Essential properties and features

3. **Code Examples** (2-3 examples)
   Practical working code with inline comments

4. **Prerequisites** (2-4 concepts)
   What should be learned first?

5. **Related Concepts** (3-5 concepts)
   What else is connected to this?

6. **Difficulty Level**
   Beginner (1), Intermediate (2), Advanced (3), Expert (4)

7. **Common Use Cases** (2-3 examples)
   When and why to use this

Format clearly with headers."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a programming educator providing structured, accurate information for an AI learning to code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content or ""
            
            # Parse the structured response
            parsed = self._parse_concept_response(content, concept_name)
            
            # Store the concept
            concept_id = self.code_kb.store_concept(
                name=concept_name,
                category=parsed['category'],
                description=parsed['description'],
                language=language,
                examples=parsed['examples'],
                prerequisites=parsed['prerequisites'],
                difficulty=parsed['difficulty'],
                learned_from='gpt4o_research',
                confidence=0.85
            )
            
            # Store code snippets
            for i, example in enumerate(parsed['examples']):
                if example.strip():
                    self.code_kb.store_snippet(
                        concept_id=concept_id,
                        language=language or 'python',  # Default to Python
                        code=example,
                        description=f"Example {i+1} for {concept_name}",
                        tags=[concept_name, 'example']
                    )
            
            # Log learning event
            duration_ms = int((time.time() - start_time) * 1000)
            self.code_kb.log_learning(
                query=concept_name,
                concept_id=concept_id,
                learned_facts=1 + len(parsed['examples']),
                depth=depth,
                success=True,
                duration_ms=duration_ms
            )
            
            # Recursive learning of prerequisites (if not at max depth)
            prerequisite_results = []
            if depth < max_depth and parsed['prerequisites']:
                for prereq in parsed['prerequisites'][:2]:  # Limit to 2 prerequisites
                    prereq_result = self.learn_concept(prereq, language, depth=depth+1, max_depth=max_depth)
                    prerequisite_results.append(prereq_result)
                    
                    # Link concepts
                    if prereq_result.get('concept_id'):
                        self.code_kb.link_concepts(
                            from_concept=concept_id,
                            to_concept=prereq_result['concept_id'],
                            relationship='prerequisite',
                            strength=0.9
                        )
            
            # Link related concepts (just store names for now, link later if learned)
            for related in parsed['related_concepts']:
                # Check if related concept exists
                existing_related = self.code_kb.search_concepts(query=related, language=language, limit=1)
                if existing_related:
                    self.code_kb.link_concepts(
                        from_concept=concept_id,
                        to_concept=existing_related[0]['id'],
                        relationship='related_to',
                        strength=0.6
                    )
            
            return {
                'concept_id': concept_id,
                'concept_name': concept_name,
                'learned_facts': 1 + len(parsed['examples']),
                'difficulty': parsed['difficulty'],
                'prerequisites': parsed['prerequisites'],
                'related_concepts': parsed['related_concepts'],
                'prerequisite_results': prerequisite_results,
                'success': True,
                'duration_ms': duration_ms
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.code_kb.log_learning(
                query=concept_name,
                learned_facts=0,
                depth=depth,
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )
            return {
                'success': False,
                'error': str(e),
                'learned_facts': 0
            }
    
    def _parse_concept_response(self, content: str, concept_name: str) -> Dict[str, Any]:
        """Parse GPT-4o structured response."""
        
        # Extract core definition
        desc_match = re.search(r'\*\*Core Definition\*\*(.+?)(?=\*\*|$)', content, re.DOTALL | re.I)
        description = desc_match.group(1).strip() if desc_match else content[:300]
        
        # Extract code examples
        examples = re.findall(r'```[\w]*\n(.+?)```', content, re.DOTALL)
        if not examples:
            # Try without language specifier
            examples = re.findall(r'```(.+?)```', content, re.DOTALL)
        
        # Extract prerequisites
        prereq_match = re.search(r'\*\*Prerequisites\*\*(.+?)(?=\*\*|$)', content, re.DOTALL | re.I)
        prerequisites = []
        if prereq_match:
            prereq_text = prereq_match.group(1)
            prerequisites = [
                p.strip().strip('*-•').strip() 
                for p in re.findall(r'[-•*]\s*(.+?)(?:\n|$)', prereq_text)
                if p.strip()
            ][:4]
        
        # Extract related concepts
        related_match = re.search(r'\*\*Related Concepts\*\*(.+?)(?=\*\*|$)', content, re.DOTALL | re.I)
        related_concepts = []
        if related_match:
            related_text = related_match.group(1)
            related_concepts = [
                r.strip().strip('*-•').strip() 
                for r in re.findall(r'[-•*]\s*(.+?)(?:\n|$)', related_text)
                if r.strip()
            ][:5]
        
        # Extract difficulty
        diff_match = re.search(r'\*\*Difficulty Level\*\*[:\s]*(\d+|Beginner|Intermediate|Advanced|Expert)', content, re.I)
        difficulty = 1
        if diff_match:
            diff_str = diff_match.group(1).lower()
            if diff_str in ['1', 'beginner']:
                difficulty = 1
            elif diff_str in ['2', 'intermediate']:
                difficulty = 2
            elif diff_str in ['3', 'advanced']:
                difficulty = 3
            elif diff_str in ['4', 'expert']:
                difficulty = 4
        
        # Determine category
        category = self._categorize_concept(concept_name, content)
        
        return {
            'description': description[:500],
            'examples': examples[:3],
            'prerequisites': prerequisites,
            'related_concepts': related_concepts,
            'difficulty': difficulty,
            'category': category
        }
    
    def _categorize_concept(self, name: str, content: str) -> str:
        """Categorize the concept based on name and content."""
        name_lower = name.lower()
        content_lower = content.lower()
        
        if any(k in name_lower for k in ['class', 'object', 'inheritance', 'polymorphism']):
            return 'paradigm'
        if any(k in name_lower for k in ['function', 'method', 'lambda', 'closure']):
            return 'syntax'
        if any(k in name_lower for k in ['pattern', 'singleton', 'factory', 'observer']):
            return 'pattern'
        if any(k in name_lower for k in ['python', 'javascript', 'go', 'rust', 'java']):
            return 'language'
        if any(k in name_lower for k in ['library', 'framework', 'api', 'module']):
            return 'library'
        if any(k in name_lower for k in ['async', 'thread', 'concurrent', 'parallel']):
            return 'paradigm'
        
        return 'concept'
    
    def expand_knowledge(self, concept_id: str, max_related: int = 3) -> Dict[str, Any]:
        """
        Expand knowledge by learning related concepts.
        
        Args:
            concept_id: The concept to expand from
            max_related: Maximum number of related concepts to learn
        
        Returns:
            Dict with expansion results
        """
        concept = self.code_kb.get_concept(concept_id)
        if not concept:
            return {'success': False, 'error': 'Concept not found'}
        
        # Get related concepts
        related = self.code_kb.get_related_concepts(concept_id)
        
        # Learn unlearned related concepts
        learned = []
        for rel in related[:max_related]:
            result = self.learn_concept(rel['name'], concept['language'], depth=1, max_depth=2)
            if result.get('success'):
                learned.append(result)
        
        return {
            'success': True,
            'concept_name': concept['name'],
            'related_learned': len(learned),
            'results': learned
        }
