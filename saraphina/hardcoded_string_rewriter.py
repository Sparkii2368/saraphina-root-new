#!/usr/bin/env python3
"""
HardcodedStringRewriter - Detect and replace hardcoded strings in code

Safely identifies string literals, numbers, and constants in Python code
and generates patches to replace them with configurable values.

Features:
- AST-based detection of hardcoded values
- Context-aware replacement (avoids imports, function names, etc.)
- Generates config files for extracted constants
- Integration with CodeForge for safe patching
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import ast
import re
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class HardcodedValue:
    """Represents a hardcoded value found in code"""
    value: Any
    value_type: str  # 'string', 'number', 'boolean'
    file_path: str
    line_number: int
    column: int
    context: str  # Surrounding code context
    category: str  # 'ui_text', 'config', 'path', 'url', 'api_key', 'other'
    suggested_name: Optional[str] = None
    replacement_strategy: str = "config"  # 'config', 'constant', 'parameter'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'type': self.value_type,
            'file': self.file_path,
            'line': self.line_number,
            'column': self.column,
            'context': self.context,
            'category': self.category,
            'suggested_name': self.suggested_name,
            'replacement_strategy': self.replacement_strategy
        }


@dataclass
class RewriteSpec:
    """Specification for rewriting hardcoded values"""
    file_path: str
    hardcoded_values: List[HardcodedValue]
    config_file: Optional[str] = None
    constants_module: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'hardcoded_values': [hv.to_dict() for hv in self.hardcoded_values],
            'config_file': self.config_file,
            'constants_module': self.constants_module
        }


class HardcodedStringRewriter:
    """Detect and replace hardcoded strings in Python code"""
    
    # Strings to ignore (framework/library specific)
    IGNORE_PATTERNS = {
        '__init__', '__main__', '__name__', '__file__',
        'utf-8', 'ascii', 'latin-1',  # Encodings
        'r', 'w', 'a', 'rb', 'wb',  # File modes
        'GET', 'POST', 'PUT', 'DELETE',  # HTTP methods
        'json', 'xml', 'html', 'csv',  # Formats
    }
    
    # Categories based on patterns
    CATEGORY_PATTERNS = {
        'ui_text': [
            r'^[A-Z][a-z].*',  # Title case
            r'.*\s.*',  # Contains spaces (likely display text)
            r'.*[.!?]$',  # Ends with punctuation
        ],
        'path': [
            r'[/\\]',  # Contains path separators
            r'^[A-Z]:\\.*',  # Windows path
            r'^/.*',  # Unix path
        ],
        'url': [
            r'^https?://',
            r'^ftp://',
            r'^ws://',
        ],
        'config': [
            r'^[a-z_]+$',  # snake_case (likely config key)
        ],
    }
    
    def __init__(self, saraphina_root: str = "D:\\Saraphina Root\\saraphina"):
        self.saraphina_root = Path(saraphina_root)
        self.scanned_values: Dict[str, List[HardcodedValue]] = {}
    
    def scan_file(self, file_path: Path) -> List[HardcodedValue]:
        """
        Scan a Python file for hardcoded values.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            List of HardcodedValue objects
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
            
            values = []
            visitor = HardcodedValueVisitor(str(file_path), content)
            visitor.visit(tree)
            
            for value in visitor.hardcoded_values:
                # Categorize and suggest name
                value.category = self._categorize_value(value)
                value.suggested_name = self._suggest_name(value)
                values.append(value)
            
            self.scanned_values[str(file_path)] = values
            return values
        
        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")
            return []
    
    def scan_directory(self, directory: Optional[Path] = None) -> Dict[str, List[HardcodedValue]]:
        """
        Scan all Python files in a directory.
        
        Args:
            directory: Directory to scan (default: saraphina_root)
        
        Returns:
            Dict mapping file paths to lists of hardcoded values
        """
        if directory is None:
            directory = self.saraphina_root
        
        results = {}
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith('test_'):
                continue  # Skip test files
            
            values = self.scan_file(py_file)
            if values:
                results[str(py_file)] = values
                logger.info(f"Found {len(values)} hardcoded values in {py_file.name}")
        
        return results
    
    def _categorize_value(self, value: HardcodedValue) -> str:
        """Categorize a hardcoded value based on patterns"""
        if value.value_type != 'string':
            return 'config'
        
        str_value = str(value.value)
        
        # Check against category patterns
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, str_value):
                    return category
        
        return 'other'
    
    def _suggest_name(self, value: HardcodedValue) -> str:
        """Suggest a variable name for a hardcoded value"""
        if value.value_type == 'string':
            str_value = str(value.value)
            
            # Convert to snake_case
            name = re.sub(r'[^a-zA-Z0-9]+', '_', str_value)
            name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
            name = name.lower().strip('_')
            
            # Add prefix based on category
            prefixes = {
                'ui_text': 'TEXT_',
                'path': 'PATH_',
                'url': 'URL_',
                'config': 'CONFIG_',
            }
            prefix = prefixes.get(value.category, '')
            
            # Truncate if too long
            if len(name) > 30:
                name = name[:30]
            
            return f"{prefix}{name}".upper()
        
        elif value.value_type == 'number':
            # Use context to suggest name
            context_lower = value.context.lower()
            if 'timeout' in context_lower:
                return 'TIMEOUT_SECONDS'
            elif 'port' in context_lower:
                return 'PORT'
            elif 'max' in context_lower or 'limit' in context_lower:
                return 'MAX_VALUE'
            else:
                return 'NUMERIC_CONSTANT'
        
        else:
            return 'CONSTANT_VALUE'
    
    def generate_rewrite_spec(
        self,
        file_path: str,
        values_to_replace: Optional[List[HardcodedValue]] = None,
        strategy: str = "config"
    ) -> RewriteSpec:
        """
        Generate a specification for rewriting hardcoded values.
        
        Args:
            file_path: File to rewrite
            values_to_replace: Specific values to replace (None = all)
            strategy: 'config' (config.json), 'constant' (constants.py), or 'parameter'
        
        Returns:
            RewriteSpec object
        """
        all_values = self.scanned_values.get(file_path, [])
        
        if values_to_replace is None:
            values_to_replace = all_values
        
        # Set replacement strategy
        for value in values_to_replace:
            value.replacement_strategy = strategy
        
        spec = RewriteSpec(
            file_path=file_path,
            hardcoded_values=values_to_replace
        )
        
        if strategy == 'config':
            spec.config_file = str(self.saraphina_root.parent / "config" / "constants.json")
        elif strategy == 'constant':
            spec.constants_module = "saraphina.constants"
        
        return spec
    
    def generate_config_file(self, spec: RewriteSpec) -> Dict[str, Any]:
        """
        Generate a config file for extracted constants.
        
        Args:
            spec: RewriteSpec with values to extract
        
        Returns:
            Dict representing config JSON
        """
        config = {}
        
        for value in spec.hardcoded_values:
            if value.suggested_name:
                config[value.suggested_name] = value.value
        
        return config
    
    def generate_constants_module(self, spec: RewriteSpec) -> str:
        """
        Generate a Python constants module.
        
        Args:
            spec: RewriteSpec with values to extract
        
        Returns:
            Python code as string
        """
        lines = [
            '"""',
            'Constants module - Auto-generated by HardcodedStringRewriter',
            '"""',
            ''
        ]
        
        # Group by category
        by_category: Dict[str, List[HardcodedValue]] = {}
        for value in spec.hardcoded_values:
            category = value.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(value)
        
        # Generate constants by category
        for category, values in sorted(by_category.items()):
            lines.append(f"# {category.upper()}")
            for value in values:
                if value.suggested_name:
                    if value.value_type == 'string':
                        lines.append(f'{value.suggested_name} = "{value.value}"')
                    else:
                        lines.append(f'{value.suggested_name} = {value.value}')
            lines.append('')
        
        return '\n'.join(lines)
    
    def generate_patch(self, spec: RewriteSpec) -> str:
        """
        Generate a unified diff patch for replacing hardcoded values.
        
        Args:
            spec: RewriteSpec with replacement details
        
        Returns:
            Unified diff as string
        """
        file_path = Path(spec.file_path)
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines(keepends=True)
        
        # Sort by line number (descending) to avoid offset issues
        sorted_values = sorted(
            spec.hardcoded_values,
            key=lambda v: (v.line_number, v.column),
            reverse=True
        )
        
        # Apply replacements
        modified_lines = lines.copy()
        for value in sorted_values:
            if not value.suggested_name:
                continue
            
            line_idx = value.line_number - 1
            if 0 <= line_idx < len(modified_lines):
                line = modified_lines[line_idx]
                
                # Replace the value
                if value.value_type == 'string':
                    # Replace string literal
                    old_pattern = f'"{value.value}"'
                    if old_pattern not in line:
                        old_pattern = f"'{value.value}'"
                else:
                    old_pattern = str(value.value)
                
                # Generate replacement based on strategy
                if spec.config_file:
                    replacement = f'config["{value.suggested_name}"]'
                elif spec.constants_module:
                    replacement = f'constants.{value.suggested_name}'
                else:
                    replacement = value.suggested_name
                
                modified_lines[line_idx] = line.replace(old_pattern, replacement, 1)
        
        # Generate diff
        import difflib
        diff = difflib.unified_diff(
            lines,
            modified_lines,
            fromfile=f"a/{file_path.name}",
            tofile=f"b/{file_path.name}",
            lineterm=''
        )
        
        return '\n'.join(diff)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about scanned hardcoded values"""
        total_values = sum(len(values) for values in self.scanned_values.values())
        
        by_type = {}
        by_category = {}
        
        for values in self.scanned_values.values():
            for value in values:
                by_type[value.value_type] = by_type.get(value.value_type, 0) + 1
                by_category[value.category] = by_category.get(value.category, 0) + 1
        
        return {
            'total_files': len(self.scanned_values),
            'total_values': total_values,
            'by_type': by_type,
            'by_category': by_category,
            'files': {
                path: len(values)
                for path, values in self.scanned_values.items()
            }
        }


class HardcodedValueVisitor(ast.NodeVisitor):
    """AST visitor to find hardcoded values"""
    
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.hardcoded_values: List[HardcodedValue] = []
    
    def visit_Constant(self, node: ast.Constant):
        """Visit constant nodes (Python 3.8+)"""
        value = node.value
        
        # Skip None, True, False
        if value is None or isinstance(value, bool):
            self.generic_visit(node)
            return
        
        # Skip very short strings (likely keywords)
        if isinstance(value, str):
            if len(value) < 3 or value in HardcodedStringRewriter.IGNORE_PATTERNS:
                self.generic_visit(node)
                return
        
        # Determine type
        if isinstance(value, str):
            value_type = 'string'
        elif isinstance(value, (int, float)):
            value_type = 'number'
        else:
            value_type = 'other'
        
        # Get context (surrounding line)
        line_idx = node.lineno - 1
        context = self.source_lines[line_idx] if 0 <= line_idx < len(self.source_lines) else ""
        
        hv = HardcodedValue(
            value=value,
            value_type=value_type,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            context=context.strip(),
            category='other'
        )
        
        self.hardcoded_values.append(hv)
        self.generic_visit(node)
    
    def visit_Str(self, node: ast.Str):
        """Visit string nodes (Python 3.7 and below)"""
        # Create a Constant node for compatibility
        const_node = ast.Constant(value=node.s)
        const_node.lineno = node.lineno
        const_node.col_offset = node.col_offset
        self.visit_Constant(const_node)
    
    def visit_Num(self, node: ast.Num):
        """Visit number nodes (Python 3.7 and below)"""
        const_node = ast.Constant(value=node.n)
        const_node.lineno = node.lineno
        const_node.col_offset = node.col_offset
        self.visit_Constant(const_node)


# CLI interface
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    rewriter = HardcodedStringRewriter()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "scan":
            # Scan all files
            results = rewriter.scan_directory()
            print(f"\n📊 Scan Results:")
            print(f"Files scanned: {len(results)}")
            
            for file_path, values in results.items():
                print(f"\n{Path(file_path).name}: {len(values)} hardcoded values")
                for value in values[:5]:  # Show first 5
                    print(f"  Line {value.line_number}: {value.value_type} = {value.value}")
                if len(values) > 5:
                    print(f"  ... and {len(values) - 5} more")
        
        elif command == "stats":
            # Show statistics
            rewriter.scan_directory()
            stats = rewriter.get_statistics()
            
            print("\n📊 Statistics:")
            print(f"Total files: {stats['total_files']}")
            print(f"Total hardcoded values: {stats['total_values']}")
            
            print("\nBy type:")
            for type_name, count in stats['by_type'].items():
                print(f"  {type_name}: {count}")
            
            print("\nBy category:")
            for category, count in stats['by_category'].items():
                print(f"  {category}: {count}")
        
        else:
            print("Usage: python hardcoded_string_rewriter.py [scan|stats]")
    
    else:
        print("Usage: python hardcoded_string_rewriter.py [scan|stats]")
