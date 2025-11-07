#!/usr/bin/env python3
"""
CodeFactory - GPT-4o powered code generation with knowledge context.

Proposes code patches based on feature specifications, leveraging
the CodeKnowledgeDB for relevant context and examples.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json
import uuid

from .code_knowledge_db import CodeKnowledgeDB


class CodeFactory:
    """Generate code using GPT-4o with learned programming knowledge."""
    
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
    
    def propose_code(
        self,
        feature_spec: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code proposal from feature specification.
        
        Args:
            feature_spec: Natural language description of desired feature
            language: Target programming language
            context: Additional context (existing code, constraints, etc.)
        
        Returns:
            Dict with proposal_id, code, tests, analysis, and metadata
        """
        if not self.gpt4_available:
            return {
                'success': False,
                'error': 'GPT-4o not available',
                'proposal_id': None
            }
        
        proposal_id = f"proposal_{uuid.uuid4().hex[:12]}"
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Search for relevant concepts in knowledge base
            related_concepts = self._find_related_concepts(feature_spec, language)
            
            # Build context-aware prompt
            prompt = self._build_code_prompt(feature_spec, language, related_concepts, context)
            
            # Generate code with GPT-4o
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert programmer generating production-quality code.
                        
Your code must:
- Be clean, readable, and well-documented
- Follow best practices and idioms for the target language
- Include comprehensive docstrings/comments
- Handle errors appropriately
- Be testable and maintainable

Format your response as:
```python
# Your code here
```

Then provide test cases:
```python
# Test code here
```"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content or ""
            
            # Parse code and tests from response
            parsed = self._parse_code_response(content)
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'feature_spec': feature_spec,
                'language': language,
                'code': parsed['code'],
                'tests': parsed['tests'],
                'explanation': parsed['explanation'],
                'related_concepts': [c['name'] for c in related_concepts],
                'raw_response': content,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'proposal_id': proposal_id,
                'feature_spec': feature_spec
            }
    
    def _find_related_concepts(
        self,
        feature_spec: str,
        language: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant concepts from knowledge base."""
        # Extract key terms from spec
        import re
        words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', feature_spec) if len(w) >= 4]
        
        concepts = []
        for word in words[:3]:  # Top 3 keywords
            results = self.code_kb.search_concepts(
                query=word,
                language=language,
                limit=2
            )
            concepts.extend(results)
        
        # Deduplicate by ID
        seen = set()
        unique_concepts = []
        for c in concepts:
            if c['id'] not in seen:
                seen.add(c['id'])
                unique_concepts.append(c)
        
        return unique_concepts[:limit]
    
    def _build_code_prompt(
        self,
        feature_spec: str,
        language: str,
        related_concepts: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build context-rich prompt for code generation."""
        prompt = f"""Generate {language} code for the following feature:

**Feature Specification:**
{feature_spec}

"""
        
        # Add knowledge context
        if related_concepts:
            prompt += "**Relevant Concepts You Know:**\n"
            for concept in related_concepts:
                prompt += f"- {concept['name']} ({concept['category']}, difficulty: {concept['difficulty']}/4)\n"
                if concept.get('description'):
                    prompt += f"  {concept['description'][:150]}...\n"
            prompt += "\n"
        
        # Add additional context
        if context:
            if context.get('existing_code'):
                prompt += f"**Existing Code Context:**\n```{language}\n{context['existing_code']}\n```\n\n"
            if context.get('constraints'):
                prompt += f"**Constraints:**\n{context['constraints']}\n\n"
            if context.get('requirements'):
                prompt += f"**Requirements:**\n{context['requirements']}\n\n"
        
        prompt += """**Deliverables:**

1. Complete, working code
2. Comprehensive test cases (using pytest for Python)
3. Brief explanation of approach

Generate production-ready code with proper error handling, documentation, and tests."""
        
        return prompt
    
    def _parse_code_response(self, content: str) -> Dict[str, Any]:
        """Parse code and tests from GPT-4o response."""
        import re
        
        # Extract all code blocks
        code_blocks = re.findall(r'```(?:python|py)?\n(.+?)```', content, re.DOTALL)
        
        # First block is main code, second is tests
        code = code_blocks[0].strip() if len(code_blocks) > 0 else ""
        tests = code_blocks[1].strip() if len(code_blocks) > 1 else ""
        
        # Extract explanation (text before first code block)
        explanation_match = re.search(r'^(.+?)```', content, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        
        # If no explanation before code, try after
        if not explanation:
            explanation_parts = re.split(r'```[^\n]*\n.+?```', content, flags=re.DOTALL)
            explanation = " ".join(p.strip() for p in explanation_parts if p.strip())[:500]
        
        return {
            'code': code,
            'tests': tests,
            'explanation': explanation[:500] if explanation else "Code generated successfully"
        }
    
    def refine_code(
        self,
        original_code: str,
        feedback: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Refine existing code based on feedback.
        
        Args:
            original_code: The code to improve
            feedback: What to change/fix
            language: Programming language
        
        Returns:
            Dict with refined code and explanation
        """
        if not self.gpt4_available:
            return {'success': False, 'error': 'GPT-4o not available'}
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Improve the following {language} code based on this feedback:

**Feedback:**
{feedback}

**Original Code:**
```{language}
{original_code}
```

Provide the improved code with explanations of changes."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer improving code quality."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content or ""
            parsed = self._parse_code_response(content)
            
            return {
                'success': True,
                'refined_code': parsed['code'],
                'explanation': parsed['explanation'],
                'original_code': original_code
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
