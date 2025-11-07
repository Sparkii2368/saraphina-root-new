#!/usr/bin/env python3
"""
CodeRiskModel - Classify code patches by risk level for safe self-editing.

Risk Levels:
- SAFE: Minor changes (docstrings, comments, formatting)
- CAUTION: Logic changes that preserve functionality
- SENSITIVE: Security, encryption, authentication, data deletion
- CRITICAL: Core architecture changes
"""
from __future__ import annotations
from typing import Dict, Any, List, Set
import ast
import re


class CodeRiskModel:
    """Classify code modifications by risk level."""

    # Sensitive patterns that require owner approval
    SENSITIVE_PATTERNS = {
        'security': [
            r'encrypt', r'decrypt', r'password', r'secret', r'token', r'auth',
            r'credential', r'private.*key', r'api.*key', r'hash.*password'
        ],
        'data_loss': [
            r'\.delete\(', r'\.drop\(', r'\.unlink\(', r'\.rmtree\(',
            r'DELETE\s+FROM', r'DROP\s+TABLE', r'TRUNCATE', r'rm\s+-rf'
        ],
        'permissions': [
            r'chmod', r'chown', r'sudo', r'admin', r'privilege', r'root',
            r'os\.system', r'subprocess\.call', r'eval\(', r'exec\('
        ],
        'network': [
            r'socket\(', r'listen\(', r'bind\(', r'connect\(',
            r'requests\.', r'urllib', r'http\.'
        ],
        'database': [
            r'DROP\s+', r'ALTER\s+', r'GRANT\s+', r'REVOKE\s+',
            r'migrate', r'rollback'
        ]
    }

    # Critical modules that are core to Saraphina
    CRITICAL_MODULES = {
        'knowledge_engine', 'db', 'security', 'safety_gate', 'trust_firewall',
        'self_modification_engine', 'code_risk_model'
    }

    def __init__(self):
        self.compiled_patterns = {}
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            self.compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify_patch(
        self,
        original_code: str,
        modified_code: str,
        file_name: str
    ) -> Dict[str, Any]:
        """
        Classify a code patch by risk level.
        
        Returns:
            Dict with risk_level, risk_score (0-1), flags, rationale
        """
        result = {
            'risk_level': 'SAFE',
            'risk_score': 0.0,
            'flags': [],
            'sensitive_categories': [],
            'rationale': []
        }

        # Check if critical module
        module_name = file_name.replace('.py', '').replace('/', '.').replace('\\', '.')
        # Check basename and full path
        base_name = module_name.split('.')[-1]
        if module_name in self.CRITICAL_MODULES or base_name in self.CRITICAL_MODULES:
            result['flags'].append('critical_module')
            result['risk_score'] += 0.3
            result['rationale'].append(f'{module_name} is a critical system module')

        # Check for sensitive patterns in modified code
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(modified_code)
                if matches:
                    result['sensitive_categories'].append(category)
                    result['flags'].append(f'sensitive_{category}')
                    result['risk_score'] += 0.2
                    result['rationale'].append(f'Contains {category} operations: {matches[:2]}')

        # Check what's being added/removed
        additions = self._get_additions(original_code, modified_code)
        deletions = self._get_deletions(original_code, modified_code)

        # Deletions are risky
        if deletions:
            deleted_functions = self._extract_function_names(deletions)
            if deleted_functions:
                result['flags'].append('function_deletion')
                result['risk_score'] += 0.4
                result['rationale'].append(f'Deletes functions: {deleted_functions[:3]}')

        # Large changes are risky
        change_ratio = len(additions) / max(len(original_code), 1)
        if change_ratio > 0.5:
            result['flags'].append('large_change')
            result['risk_score'] += 0.3
            result['rationale'].append(f'{change_ratio:.1%} of code changed')

        # AST analysis for structural changes
        try:
            old_tree = ast.parse(original_code)
            new_tree = ast.parse(modified_code)
            
            old_imports = self._get_imports(old_tree)
            new_imports = self._get_imports(new_tree)
            
            added_imports = new_imports - old_imports
            removed_imports = old_imports - new_imports
            
            if removed_imports:
                result['flags'].append('import_removal')
                result['risk_score'] += 0.2
                result['rationale'].append(f'Removes imports: {list(removed_imports)[:3]}')
            
            # Check for dangerous imports
            dangerous_imports = {'os', 'subprocess', 'shutil', 'sys'}
            if added_imports & dangerous_imports:
                result['flags'].append('dangerous_import')
                result['risk_score'] += 0.3
                result['rationale'].append(f'Adds dangerous imports: {added_imports & dangerous_imports}')
        
        except SyntaxError:
            result['flags'].append('syntax_error')
            result['risk_score'] = 1.0
            result['rationale'].append('Code has syntax errors')

        # Determine risk level based on score
        if result['risk_score'] >= 0.7:
            result['risk_level'] = 'CRITICAL'
        elif result['risk_score'] >= 0.4:
            result['risk_level'] = 'SENSITIVE'
        elif result['risk_score'] >= 0.2:
            result['risk_level'] = 'CAUTION'
        else:
            result['risk_level'] = 'SAFE'

        return result

    def _get_additions(self, original: str, modified: str) -> str:
        """Extract lines that were added."""
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(),
            modified.splitlines(),
            lineterm=''
        )
        additions = []
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:])
        return '\n'.join(additions)

    def _get_deletions(self, original: str, modified: str) -> str:
        """Extract lines that were deleted."""
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(),
            modified.splitlines(),
            lineterm=''
        )
        deletions = []
        for line in diff:
            if line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:])
        return '\n'.join(deletions)

    def _extract_function_names(self, code: str) -> List[str]:
        """Extract function names from code snippet."""
        try:
            tree = ast.parse(code)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except:
            # Fallback to regex
            matches = re.findall(r'def\s+(\w+)\s*\(', code)
            return matches

    def _get_imports(self, tree: ast.AST) -> Set[str]:
        """Extract imported module names from AST."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports

    def requires_owner_approval(self, classification: Dict[str, Any]) -> bool:
        """Check if patch requires explicit owner approval."""
        risk_level = classification['risk_level']
        return risk_level in ['SENSITIVE', 'CRITICAL']

    def format_risk_report(self, classification: Dict[str, Any]) -> str:
        """Format risk classification as readable report."""
        risk_level = classification['risk_level']
        risk_score = classification['risk_score']
        
        icons = {
            'SAFE': '✅',
            'CAUTION': '⚠️',
            'SENSITIVE': '🔒',
            'CRITICAL': '🚨'
        }
        
        report = f"{icons.get(risk_level, '❓')} Risk Level: {risk_level} ({risk_score:.2f})\n\n"
        
        if classification['rationale']:
            report += "Reasons:\n"
            for reason in classification['rationale']:
                report += f"  • {reason}\n"
        
        if classification['sensitive_categories']:
            report += f"\nSensitive Categories: {', '.join(classification['sensitive_categories'])}\n"
        
        if classification['flags']:
            report += f"\nFlags: {', '.join(classification['flags'])}\n"
        
        if self.requires_owner_approval(classification):
            report += "\n⚠️  OWNER APPROVAL REQUIRED\n"
        
        return report
