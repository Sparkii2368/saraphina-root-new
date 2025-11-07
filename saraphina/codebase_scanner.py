#!/usr/bin/env python3
"""
Codebase Scanner - Saraphina's self-awareness module

Walks her own directory tree and builds a live registry of:
- All Python modules
- File metadata (size, modified date)
- Basic structure (imports, top-level definitions)
- Dependencies between modules

Stores everything in modules.db for fast introspection.
"""
import os
import ast
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("CodebaseScanner")


@dataclass
class ModuleInfo:
    """Information about a single Python module"""
    path: str
    name: str
    size_bytes: int
    last_modified: str
    lines_of_code: int
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    has_main: bool = False
    scan_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CodebaseScanner:
    """Scans Saraphina's codebase and builds module registry"""
    
    def __init__(self, root_path: str = "D:\\Saraphina Root", 
                 db_path: str = "D:\\Saraphina Root\\data\\modules.db"):
        self.root_path = Path(root_path)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        logger.info(f"Codebase Scanner initialized: {self.root_path}")
    
    def _init_database(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Modules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                size_bytes INTEGER,
                last_modified TEXT,
                lines_of_code INTEGER,
                has_main BOOLEAN,
                scan_timestamp TEXT
            )
        """)
        
        # Imports table (module dependencies)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                import_name TEXT,
                import_type TEXT,
                FOREIGN KEY(module_id) REFERENCES modules(id)
            )
        """)
        
        # Classes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                name TEXT,
                line_number INTEGER,
                docstring TEXT,
                FOREIGN KEY(module_id) REFERENCES modules(id)
            )
        """)
        
        # Functions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                name TEXT,
                line_number INTEGER,
                docstring TEXT,
                is_async BOOLEAN,
                FOREIGN KEY(module_id) REFERENCES modules(id)
            )
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_module_name ON modules(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_module_path ON modules(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_imports ON imports(module_id)")
        
        conn.commit()
        conn.close()
    
    def scan_codebase(self, exclude_dirs: List[str] = None) -> Dict[str, Any]:
        """
        Full scan of codebase
        
        Returns:
            Summary dict with counts and statistics
        """
        logger.info(f"Starting full codebase scan: {self.root_path}")
        
        if exclude_dirs is None:
            exclude_dirs = ['__pycache__', '.git', 'venv', 'node_modules', '.venv']
        
        modules_found = []
        errors = []
        
        # Walk directory tree
        for root, dirs, files in os.walk(self.root_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        module_info = self._scan_module(file_path)
                        modules_found.append(module_info)
                        self._store_module(module_info)
                    except Exception as e:
                        error_msg = f"Error scanning {file_path}: {e}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
        
        # Calculate statistics
        total_loc = sum(m.lines_of_code for m in modules_found)
        total_size = sum(m.size_bytes for m in modules_found)
        
        summary = {
            'modules_scanned': len(modules_found),
            'total_lines': total_loc,
            'total_size_kb': total_size / 1024,
            'errors': len(errors),
            'scan_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Scan complete: {summary['modules_scanned']} modules, {summary['total_lines']} LOC")
        
        return summary
    
    def _scan_module(self, file_path: Path) -> ModuleInfo:
        """Scan a single Python module"""
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic file info
        stats = file_path.stat()
        module_name = file_path.stem
        
        # Count lines
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            tree = None
        
        module_info = ModuleInfo(
            path=str(file_path.relative_to(self.root_path)),
            name=module_name,
            size_bytes=stats.st_size,
            last_modified=datetime.fromtimestamp(stats.st_mtime).isoformat(),
            lines_of_code=loc
        )
        
        if tree:
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_info.imports.append(node.module)
            
            # Extract top-level classes and functions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    module_info.classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    module_info.functions.append(node.name)
            
            # Check for __main__ block
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    if isinstance(node.test, ast.Compare):
                        if hasattr(node.test.left, 'id') and node.test.left.id == '__name__':
                            module_info.has_main = True
        
        return module_info
    
    def _store_module(self, module_info: ModuleInfo):
        """Store module info in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or replace module
        cursor.execute("""
            INSERT OR REPLACE INTO modules 
            (path, name, size_bytes, last_modified, lines_of_code, has_main, scan_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            module_info.path,
            module_info.name,
            module_info.size_bytes,
            module_info.last_modified,
            module_info.lines_of_code,
            module_info.has_main,
            module_info.scan_timestamp
        ))
        
        module_id = cursor.lastrowid
        
        # Store imports
        cursor.execute("DELETE FROM imports WHERE module_id = ?", (module_id,))
        for import_name in module_info.imports:
            cursor.execute("""
                INSERT INTO imports (module_id, import_name, import_type)
                VALUES (?, ?, ?)
            """, (module_id, import_name, 'import'))
        
        conn.commit()
        conn.close()
    
    def get_module_info(self, module_name: str) -> Dict[str, Any]:
        """Get info about a specific module"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT path, name, size_bytes, last_modified, lines_of_code, has_main
            FROM modules
            WHERE name = ?
        """, (module_name,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        module_id = cursor.lastrowid
        
        # Get imports
        cursor.execute("""
            SELECT import_name FROM imports WHERE module_id = ?
        """, (module_id,))
        
        imports = [r[0] for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            'path': row[0],
            'name': row[1],
            'size_bytes': row[2],
            'last_modified': row[3],
            'lines_of_code': row[4],
            'has_main': row[5],
            'imports': imports
        }
    
    def get_all_modules(self) -> List[Dict[str, Any]]:
        """Get list of all scanned modules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, path, lines_of_code, size_bytes, last_modified
            FROM modules
            ORDER BY name
        """)
        
        modules = []
        for row in cursor.fetchall():
            modules.append({
                'name': row[0],
                'path': row[1],
                'lines_of_code': row[2],
                'size_bytes': row[3],
                'last_modified': row[4]
            })
        
        conn.close()
        return modules
    
    def get_dependencies(self, module_name: str) -> List[str]:
        """Get modules that this module depends on"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.import_name
            FROM imports i
            JOIN modules m ON i.module_id = m.id
            WHERE m.name = ?
        """, (module_name,))
        
        deps = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return deps
    
    def get_dependents(self, module_name: str) -> List[str]:
        """Get modules that depend on this module"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT m.name
            FROM modules m
            JOIN imports i ON i.module_id = m.id
            WHERE i.import_name LIKE ?
        """, (f"%{module_name}%",))
        
        dependents = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return dependents
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get codebase statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total modules
        cursor.execute("SELECT COUNT(*) FROM modules")
        total_modules = cursor.fetchone()[0]
        
        # Total LOC
        cursor.execute("SELECT SUM(lines_of_code) FROM modules")
        total_loc = cursor.fetchone()[0] or 0
        
        # Total size
        cursor.execute("SELECT SUM(size_bytes) FROM modules")
        total_size = cursor.fetchone()[0] or 0
        
        # Modules with main
        cursor.execute("SELECT COUNT(*) FROM modules WHERE has_main = 1")
        with_main = cursor.fetchone()[0]
        
        # Most imported modules
        cursor.execute("""
            SELECT import_name, COUNT(*) as count
            FROM imports
            GROUP BY import_name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_imports = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_modules': total_modules,
            'total_lines_of_code': total_loc,
            'total_size_kb': total_size / 1024,
            'modules_with_main': with_main,
            'top_imports': top_imports
        }


# CLI for scanning
if __name__ == "__main__":
    import sys
    
    scanner = CodebaseScanner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "scan":
            print("Scanning codebase...")
            summary = scanner.scan_codebase()
            print("\n" + "="*60)
            print("SCAN COMPLETE")
            print("="*60)
            print(f"Modules: {summary['modules_scanned']}")
            print(f"Total LOC: {summary['total_lines']}")
            print(f"Total Size: {summary['total_size_kb']:.1f} KB")
            print(f"Errors: {summary['errors']}")
            print("="*60)
        
        elif command == "stats":
            stats = scanner.get_statistics()
            print("\n" + "="*60)
            print("CODEBASE STATISTICS")
            print("="*60)
            print(f"Total Modules: {stats['total_modules']}")
            print(f"Total LOC: {stats['total_lines_of_code']}")
            print(f"Total Size: {stats['total_size_kb']:.1f} KB")
            print(f"Modules with __main__: {stats['modules_with_main']}")
            print("\nTop Imports:")
            for imp in stats['top_imports'][:5]:
                print(f"  {imp['name']}: {imp['count']} times")
            print("="*60)
        
        elif command == "list":
            modules = scanner.get_all_modules()
            print(f"\nFound {len(modules)} modules:")
            for m in modules[:20]:
                print(f"  {m['name']}: {m['lines_of_code']} LOC")
    else:
        print("Usage: python codebase_scanner.py [scan|stats|list]")
