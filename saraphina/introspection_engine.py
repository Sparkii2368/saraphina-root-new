#!/usr/bin/env python3
"""
Introspection Engine - Deep code analysis using AST parsing

Extracts detailed information from Python source:
- Classes with methods, properties, inheritance
- Functions with parameters, return types, decorators
- Docstrings and documentation coverage
- TODOs, FIXMEs, and code comments
- Type hints and annotations
- Complexity metrics

Works with CodebaseScanner to provide complete self-awareness.
"""
import ast
import re
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("IntrospectionEngine")


@dataclass
class FunctionInfo:
    """Detailed function/method information"""
    name: str
    line_number: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_annotation: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    complexity: int = 1  # Cyclomatic complexity estimate


@dataclass
class ClassInfo:
    """Detailed class information"""
    name: str
    line_number: int
    docstring: Optional[str] = None
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class CodeIssue:
    """Code quality issue or TODO"""
    type: str  # 'TODO', 'FIXME', 'HACK', 'WARNING'
    line_number: int
    message: str
    severity: str = 'low'  # low, medium, high


class IntrospectionEngine:
    """Deep code introspection using AST analysis"""
    
    def __init__(self, db_path: str = "D:\\Saraphina Root\\data\\modules.db"):
        self.db_path = Path(db_path)
        self._extend_database()
        
        logger.info("Introspection Engine initialized")
    
    def _extend_database(self):
        """Extend modules.db with introspection tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Detailed class info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                name TEXT,
                line_number INTEGER,
                docstring TEXT,
                bases TEXT,
                decorators TEXT,
                FOREIGN KEY(module_id) REFERENCES modules(id)
            )
        """)
        
        # Detailed function info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS function_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                class_id INTEGER,
                name TEXT,
                line_number INTEGER,
                docstring TEXT,
                parameters TEXT,
                return_annotation TEXT,
                decorators TEXT,
                is_async BOOLEAN,
                is_method BOOLEAN,
                complexity INTEGER,
                FOREIGN KEY(module_id) REFERENCES modules(id),
                FOREIGN KEY(class_id) REFERENCES class_details(id)
            )
        """)
        
        # Code issues (TODOs, FIXMEs, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                type TEXT,
                line_number INTEGER,
                message TEXT,
                severity TEXT,
                FOREIGN KEY(module_id) REFERENCES modules(id)
            )
        """)
        
        # Documentation coverage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentation_coverage (
                module_id INTEGER PRIMARY KEY,
                total_functions INTEGER,
                documented_functions INTEGER,
                total_classes INTEGER,
                documented_classes INTEGER,
                coverage_percent REAL,
                FOREIGN KEY(module_id) REFERENCES modules(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def analyze_file(self, file_path: Path, module_id: int) -> Dict[str, Any]:
        """
        Perform deep analysis of a single file
        
        Args:
            file_path: Path to Python file
            module_id: Module ID from modules table
        
        Returns:
            Analysis summary
        """
        logger.info(f"Analyzing {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return {'error': str(e)}
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return {'error': f'Syntax error: {e}'}
        
        # Extract information
        classes = self._extract_classes(tree)
        functions = self._extract_functions(tree)
        issues = self._extract_issues(content)
        
        # Calculate documentation coverage
        doc_coverage = self._calculate_doc_coverage(classes, functions)
        
        # Store in database
        self._store_analysis(module_id, classes, functions, issues, doc_coverage)
        
        return {
            'classes': len(classes),
            'functions': len(functions),
            'issues': len(issues),
            'doc_coverage': doc_coverage
        }
    
    def _extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """Extract detailed class information"""
        classes = []
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = ClassInfo(
                    name=node.name,
                    line_number=node.lineno,
                    docstring=ast.get_docstring(node),
                    bases=[self._get_name(base) for base in node.bases],
                    decorators=[self._get_name(dec) for dec in node.decorator_list]
                )
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = self._extract_function_info(item, is_method=True)
                        class_info.methods.append(method_info)
                    elif isinstance(item, ast.FunctionDef) and any(
                        isinstance(dec, ast.Name) and dec.id == 'property' 
                        for dec in item.decorator_list
                    ):
                        class_info.properties.append(item.name)
                
                classes.append(class_info)
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """Extract top-level functions"""
        functions = []
        
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._extract_function_info(node, is_method=False)
                functions.append(func_info)
        
        return functions
    
    def _extract_function_info(self, node, is_method: bool = False) -> FunctionInfo:
        """Extract detailed function information"""
        # Parameters
        params = []
        if node.args.args:
            params = [arg.arg for arg in node.args.args]
        
        # Return annotation
        return_ann = None
        if node.returns:
            return_ann = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        # Decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]
        
        # Estimate complexity (count branches)
        complexity = self._estimate_complexity(node)
        
        return FunctionInfo(
            name=node.name,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            parameters=params,
            return_annotation=return_ann,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            complexity=complexity
        )
    
    def _estimate_complexity(self, node: ast.AST) -> int:
        """Estimate cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return str(node)
    
    def _extract_issues(self, content: str) -> List[CodeIssue]:
        """Extract TODOs, FIXMEs, and other code issues"""
        issues = []
        
        patterns = {
            'TODO': r'#\s*TODO[:\s]*(.*)',
            'FIXME': r'#\s*FIXME[:\s]*(.*)',
            'HACK': r'#\s*HACK[:\s]*(.*)',
            'WARNING': r'#\s*WARNING[:\s]*(.*)',
            'BUG': r'#\s*BUG[:\s]*(.*)'
        }
        
        severities = {
            'TODO': 'low',
            'FIXME': 'medium',
            'HACK': 'medium',
            'WARNING': 'high',
            'BUG': 'high'
        }
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for issue_type, pattern in patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    message = match.group(1).strip() if match.groups() else ""
                    issues.append(CodeIssue(
                        type=issue_type,
                        line_number=line_num,
                        message=message,
                        severity=severities[issue_type]
                    ))
        
        return issues
    
    def _calculate_doc_coverage(self, classes: List[ClassInfo], 
                                functions: List[FunctionInfo]) -> float:
        """Calculate documentation coverage percentage"""
        total = len(classes) + len(functions)
        if total == 0:
            return 100.0
        
        documented = sum(1 for c in classes if c.docstring)
        documented += sum(1 for f in functions if f.docstring)
        
        for cls in classes:
            for method in cls.methods:
                total += 1
                if method.docstring:
                    documented += 1
        
        return (documented / total) * 100 if total > 0 else 100.0
    
    def _store_analysis(self, module_id: int, classes: List[ClassInfo], 
                       functions: List[FunctionInfo], issues: List[CodeIssue],
                       doc_coverage: float):
        """Store analysis results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear old data
        cursor.execute("DELETE FROM class_details WHERE module_id = ?", (module_id,))
        cursor.execute("DELETE FROM function_details WHERE module_id = ?", (module_id,))
        cursor.execute("DELETE FROM code_issues WHERE module_id = ?", (module_id,))
        
        # Store classes
        for cls in classes:
            cursor.execute("""
                INSERT INTO class_details 
                (module_id, name, line_number, docstring, bases, decorators)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                module_id, cls.name, cls.line_number, cls.docstring,
                ','.join(cls.bases), ','.join(cls.decorators)
            ))
            
            class_id = cursor.lastrowid
            
            # Store methods
            for method in cls.methods:
                cursor.execute("""
                    INSERT INTO function_details
                    (module_id, class_id, name, line_number, docstring, parameters,
                     return_annotation, decorators, is_async, is_method, complexity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    module_id, class_id, method.name, method.line_number,
                    method.docstring, ','.join(method.parameters),
                    method.return_annotation, ','.join(method.decorators),
                    method.is_async, method.is_method, method.complexity
                ))
        
        # Store top-level functions
        for func in functions:
            cursor.execute("""
                INSERT INTO function_details
                (module_id, class_id, name, line_number, docstring, parameters,
                 return_annotation, decorators, is_async, is_method, complexity)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                module_id, func.name, func.line_number, func.docstring,
                ','.join(func.parameters), func.return_annotation,
                ','.join(func.decorators), func.is_async, func.is_method,
                func.complexity
            ))
        
        # Store issues
        for issue in issues:
            cursor.execute("""
                INSERT INTO code_issues
                (module_id, type, line_number, message, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (module_id, issue.type, issue.line_number, 
                  issue.message, issue.severity))
        
        # Store documentation coverage
        total_funcs = len(functions)
        doc_funcs = sum(1 for f in functions if f.docstring)
        total_classes = len(classes)
        doc_classes = sum(1 for c in classes if c.docstring)
        
        cursor.execute("""
            INSERT OR REPLACE INTO documentation_coverage
            (module_id, total_functions, documented_functions, 
             total_classes, documented_classes, coverage_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (module_id, total_funcs, doc_funcs, total_classes, 
              doc_classes, doc_coverage))
        
        conn.commit()
        conn.close()
    
    def get_module_details(self, module_name: str) -> Dict[str, Any]:
        """Get detailed analysis for a module"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get module ID
        cursor.execute("SELECT id FROM modules WHERE name = ?", (module_name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        module_id = row[0]
        
        # Get classes
        cursor.execute("""
            SELECT name, line_number, docstring, bases
            FROM class_details
            WHERE module_id = ?
        """, (module_id,))
        
        classes = [{'name': r[0], 'line': r[1], 'docstring': r[2], 
                   'bases': r[3].split(',') if r[3] else []} 
                  for r in cursor.fetchall()]
        
        # Get functions
        cursor.execute("""
            SELECT name, line_number, docstring, parameters, complexity
            FROM function_details
            WHERE module_id = ? AND class_id IS NULL
        """, (module_id,))
        
        functions = [{'name': r[0], 'line': r[1], 'docstring': r[2],
                     'params': r[3].split(',') if r[3] else [], 
                     'complexity': r[4]}
                    for r in cursor.fetchall()]
        
        # Get issues
        cursor.execute("""
            SELECT type, line_number, message, severity
            FROM code_issues
            WHERE module_id = ?
        """, (module_id,))
        
        issues = [{'type': r[0], 'line': r[1], 'message': r[2], 
                  'severity': r[3]} 
                 for r in cursor.fetchall()]
        
        # Get doc coverage
        cursor.execute("""
            SELECT coverage_percent FROM documentation_coverage
            WHERE module_id = ?
        """, (module_id,))
        
        doc_row = cursor.fetchone()
        doc_coverage = doc_row[0] if doc_row else 0.0
        
        conn.close()
        
        return {
            'classes': classes,
            'functions': functions,
            'issues': issues,
            'doc_coverage': doc_coverage
        }
    
    def get_all_issues(self, severity: str = None) -> List[Dict[str, Any]]:
        """Get all code issues across codebase"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if severity:
            cursor.execute("""
                SELECT m.name, i.type, i.line_number, i.message, i.severity
                FROM code_issues i
                JOIN modules m ON i.module_id = m.id
                WHERE i.severity = ?
                ORDER BY i.severity DESC, m.name
            """, (severity,))
        else:
            cursor.execute("""
                SELECT m.name, i.type, i.line_number, i.message, i.severity
                FROM code_issues i
                JOIN modules m ON i.module_id = m.id
                ORDER BY i.severity DESC, m.name
            """)
        
        issues = []
        for row in cursor.fetchall():
            issues.append({
                'module': row[0],
                'type': row[1],
                'line': row[2],
                'message': row[3],
                'severity': row[4]
            })
        
        conn.close()
        return issues


# CLI
if __name__ == "__main__":
    import sys
    from saraphina.codebase_scanner import CodebaseScanner
    
    engine = IntrospectionEngine()
    scanner = CodebaseScanner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "analyze":
            # Analyze all modules
            modules = scanner.get_all_modules()
            print(f"Analyzing {len(modules)} modules...")
            
            root = Path("D:\\Saraphina Root")
            for module in modules:
                file_path = root / module['path']
                # Need module_id - skip for now
                print(f"  {module['name']}")
        
        elif command == "issues":
            issues = engine.get_all_issues()
            print(f"\nFound {len(issues)} code issues:\n")
            for issue in issues[:20]:
                print(f"[{issue['severity'].upper()}] {issue['module']}:{issue['line']}")
                print(f"  {issue['type']}: {issue['message']}\n")
    else:
        print("Usage: python introspection_engine.py [analyze|issues]")
