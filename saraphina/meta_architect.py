#!/usr/bin/env python3
"""
MetaArchitect - Propose architectural refactors using GPT-4o analysis.

Analyzes module structure, dependencies, complexity and proposes:
- Module splits / micro-services
- New abstraction layers
- Design pattern applications
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
import ast
import json


class MetaArchitect:
    """Generate architectural redesign proposals using GPT-4o."""

    def __init__(self, codebase_root: Path):
        self.codebase_root = codebase_root
        self.gpt4_available = self._check_gpt4()

    def _check_gpt4(self) -> bool:
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                return True
        except Exception:
            pass
        return False

    def analyze_module(self, module_name: str) -> Dict[str, Any]:
        """
        Analyze a module's structure, complexity, and dependencies.
        
        Returns metrics: lines_of_code, function_count, class_count, 
        imports, complexity_score (McCabe), coupling_score
        """
        module_path = self.codebase_root / f"{module_name}.py"
        if not module_path.exists():
            return {'error': f'Module not found: {module_path}'}

        try:
            source = module_path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=str(module_path))
        except Exception as e:
            return {'error': f'Parse error: {e}'}

        metrics = {
            'module': module_name,
            'path': str(module_path),
            'lines_of_code': len(source.splitlines()),
            'function_count': 0,
            'class_count': 0,
            'method_count': 0,
            'imports': [],
            'functions': [],
            'classes': [],
            'complexity_score': 0.0,
        }

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    metrics['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    metrics['imports'].append(node.module)

        # Extract top-level functions and classes
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                metrics['function_count'] += 1
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                metrics['functions'].append({
                    'name': node.name,
                    'lines': func_lines,
                    'args': len(node.args.args)
                })
            elif isinstance(node, ast.ClassDef):
                metrics['class_count'] += 1
                class_methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                metrics['method_count'] += len(class_methods)
                metrics['classes'].append({
                    'name': node.name,
                    'methods': len(class_methods),
                    'lines': node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                })

        # Rough complexity score (McCabe-like): count decision points
        decision_nodes = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                decision_nodes += 1
            elif isinstance(node, ast.BoolOp):
                decision_nodes += len(node.values) - 1

        metrics['complexity_score'] = decision_nodes / max(1, metrics['lines_of_code']) * 100

        # Coupling score: number of unique imports
        metrics['coupling_score'] = len(set(metrics['imports']))

        return metrics

    def propose_refactor(
        self,
        target_module: str,
        refactor_type: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Propose an architectural refactor for a module.
        
        refactor_type: 'auto', 'microservice', 'abstraction', 'pattern'
        """
        if not self.gpt4_available:
            return {
                'success': False,
                'error': 'GPT-4o not available'
            }

        # Analyze target module
        metrics = self.analyze_module(target_module)
        if 'error' in metrics:
            return {'success': False, 'error': metrics['error']}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            # Build analysis prompt
            prompt = self._build_refactor_prompt(target_module, metrics, refactor_type)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert software architect specializing in Python system design.

Your task is to analyze code metrics and propose architectural improvements that:
- Reduce complexity and improve maintainability
- Follow SOLID principles and design patterns
- Consider scalability and testability
- Provide concrete, actionable refactoring plans

Format your response as JSON with keys:
{
  "type": "microservice|abstraction|pattern|refactor",
  "title": "Brief title",
  "rationale": "Why this refactor improves the system",
  "proposed_design": {
    "approach": "High-level strategy",
    "components": ["list", "of", "new", "modules"],
    "benefits": ["list", "of", "benefits"],
    "risks": ["list", "of", "risks"]
  },
  "risk_score": 0.0-1.0,
  "complexity_score": 0.0-1.0,
  "estimated_effort_hours": number
}"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2000
            )

            content = response.choices[0].message.content or ""
            
            # Parse JSON response
            proposal = self._parse_proposal_response(content)
            proposal['success'] = True
            proposal['scope'] = target_module
            proposal['analysis'] = metrics

            return proposal

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _build_refactor_prompt(
        self,
        module_name: str,
        metrics: Dict[str, Any],
        refactor_type: str
    ) -> str:
        """Build GPT-4o prompt for refactoring proposal."""
        
        prompt = f"""Analyze this Python module and propose an architectural refactor.

**Module:** {module_name}
**Lines of Code:** {metrics['lines_of_code']}
**Functions:** {metrics['function_count']}
**Classes:** {metrics['class_count']} ({metrics['method_count']} methods)
**Imports/Dependencies:** {metrics['coupling_score']}
**Complexity Score:** {metrics['complexity_score']:.1f}

**Current Structure:**
"""
        
        if metrics.get('classes'):
            prompt += "\nClasses:\n"
            for cls in metrics['classes'][:5]:
                prompt += f"  - {cls['name']}: {cls['methods']} methods, {cls['lines']} lines\n"
        
        if metrics.get('functions'):
            prompt += "\nTop-level Functions:\n"
            for func in metrics['functions'][:5]:
                prompt += f"  - {func['name']}: {func['lines']} lines, {func['args']} params\n"

        if refactor_type == 'microservice':
            prompt += "\n**Goal:** Propose splitting this module into micro-services or smaller, decoupled modules."
        elif refactor_type == 'abstraction':
            prompt += "\n**Goal:** Propose adding abstraction layers (interfaces, facades, adapters)."
        elif refactor_type == 'pattern':
            prompt += "\n**Goal:** Propose applying design patterns (Strategy, Factory, Observer, etc.)."
        else:
            prompt += "\n**Goal:** Propose the most impactful architectural improvement."

        prompt += "\n\nProvide a detailed refactoring proposal in JSON format."

        return prompt

    def _parse_proposal_response(self, content: str) -> Dict[str, Any]:
        """Parse GPT-4o response into structured proposal."""
        import re
        
        # Try to extract JSON from code blocks
        json_match = re.search(r'```(?:json)?\n(.+?)\n```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try raw JSON
            json_str = content

        try:
            proposal = json.loads(json_str)
            return proposal
        except json.JSONDecodeError:
            # Fallback: extract key information via regex
            return {
                'type': 'refactor',
                'title': 'Architectural Refactor',
                'rationale': content[:500],
                'proposed_design': {'raw': content},
                'risk_score': 0.5,
                'complexity_score': 0.5,
                'estimated_effort_hours': 0.0
            }

    def list_analyzable_modules(self) -> List[str]:
        """List Python modules in codebase that can be analyzed."""
        modules: List[str] = []
        
        if not self.codebase_root.exists():
            return modules

        for py_file in self.codebase_root.glob("*.py"):
            if py_file.stem.startswith('_'):
                continue
            modules.append(py_file.stem)

        return sorted(modules)
