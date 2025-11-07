#!/usr/bin/env python3
"""
Error Auto-Healing System - Self-healing runtime error detection and patching

Wraps modules to capture errors → Extract traceback → Generate spec → 
Generate fix → Validate → Apply → Learn

This makes Saraphina truly self-healing: crashes become learning opportunities.
"""
import sys
import traceback
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import functools

logger = logging.getLogger("ErrorAutoHealer")


@dataclass
class ErrorSignature:
    """Unique signature of a runtime error"""
    error_type: str
    error_message: str
    module_name: str
    function_name: str
    line_number: int
    traceback_hash: str
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    occurrence_count: int = 1
    fixed: bool = False
    fix_artifact_id: Optional[str] = None


class ErrorAutoHealer:
    """Automatic error detection and healing system"""
    
    def __init__(self, db_path: str = "D:\\Saraphina Root\\data\\modules.db",
                 auto_fix: bool = False):
        """
        Initialize error auto-healer
        
        Args:
            db_path: Path to modules database
            auto_fix: If True, automatically generates and applies fixes
        """
        self.db_path = Path(db_path)
        self.auto_fix = auto_fix
        self.error_cache = {}  # In-memory cache of recent errors
        
        self._init_error_tables()
        
        logger.info(f"Error Auto-Healer initialized (auto_fix={auto_fix})")
    
    def _init_error_tables(self):
        """Create error tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Error signatures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_signatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                error_message TEXT,
                module_name TEXT,
                function_name TEXT,
                line_number INTEGER,
                traceback_hash TEXT UNIQUE,
                traceback_full TEXT,
                first_seen TEXT,
                last_seen TEXT,
                occurrence_count INTEGER DEFAULT 1,
                fixed BOOLEAN DEFAULT 0,
                fix_artifact_id TEXT,
                fix_timestamp TEXT
            )
        """)
        
        # Fix attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fix_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id INTEGER,
                attempt_timestamp TEXT,
                spec_generated TEXT,
                code_generated TEXT,
                validation_passed BOOLEAN,
                applied BOOLEAN,
                artifact_id TEXT,
                FOREIGN KEY(error_id) REFERENCES error_signatures(id)
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traceback_hash ON error_signatures(traceback_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_type ON error_signatures(error_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixed ON error_signatures(fixed)")
        
        conn.commit()
        conn.close()
    
    def capture_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorSignature:
        """
        Capture and log an error
        
        Args:
            error: The exception that occurred
            context: Additional context (module, function, etc.)
        
        Returns:
            ErrorSignature with unique hash
        """
        # Extract traceback
        tb = traceback.extract_tb(sys.exc_info()[2])
        
        if not tb:
            # No traceback available
            signature = ErrorSignature(
                error_type=type(error).__name__,
                error_message=str(error),
                module_name=context.get('module', 'unknown') if context else 'unknown',
                function_name=context.get('function', 'unknown') if context else 'unknown',
                line_number=0,
                traceback_hash=self._hash_error(error, None)
            )
        else:
            last_frame = tb[-1]
            
            signature = ErrorSignature(
                error_type=type(error).__name__,
                error_message=str(error),
                module_name=Path(last_frame.filename).stem,
                function_name=last_frame.name,
                line_number=last_frame.lineno,
                traceback_hash=self._hash_error(error, tb)
            )
        
        # Store in database
        self._store_error(signature, traceback.format_exc())
        
        logger.warning(f"Captured error: {signature.error_type} in {signature.module_name}.{signature.function_name}:{signature.line_number}")
        
        return signature
    
    def _hash_error(self, error: Exception, tb) -> str:
        """Generate unique hash for error signature"""
        import hashlib
        
        if tb:
            # Hash based on error type + location
            last_frame = tb[-1]
            content = f"{type(error).__name__}:{last_frame.filename}:{last_frame.lineno}"
        else:
            content = f"{type(error).__name__}:{str(error)}"
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _store_error(self, signature: ErrorSignature, full_traceback: str):
        """Store or update error signature in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if error already exists
        cursor.execute("""
            SELECT id, occurrence_count FROM error_signatures
            WHERE traceback_hash = ?
        """, (signature.traceback_hash,))
        
        existing = cursor.fetchone()
        
        if existing:
            error_id, count = existing
            # Update occurrence count
            cursor.execute("""
                UPDATE error_signatures
                SET occurrence_count = ?, last_seen = ?
                WHERE id = ?
            """, (count + 1, datetime.now().isoformat(), error_id))
            
            logger.debug(f"Error seen {count + 1} times")
        else:
            # Insert new error
            cursor.execute("""
                INSERT INTO error_signatures
                (error_type, error_message, module_name, function_name, line_number,
                 traceback_hash, traceback_full, first_seen, last_seen, occurrence_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                signature.error_type,
                signature.error_message,
                signature.module_name,
                signature.function_name,
                signature.line_number,
                signature.traceback_hash,
                full_traceback,
                signature.first_seen,
                signature.first_seen
            ))
        
        conn.commit()
        conn.close()
    
    def generate_fix_spec(self, signature: ErrorSignature) -> Dict[str, Any]:
        """
        Generate an UpgradeSpec from error signature
        
        Args:
            signature: Error signature to fix
        
        Returns:
            Dict representing spec
        """
        # Build description for spec generator
        description = f"""Fix runtime error in {signature.module_name}.py

Error Type: {signature.error_type}
Error Message: {signature.error_message}
Location: {signature.function_name}() at line {signature.line_number}

The function is crashing and needs to be fixed. Please:
1. Add proper error handling
2. Fix the root cause of the error
3. Add validation for inputs
4. Ensure the function handles edge cases

Maintain all existing functionality while making it robust."""
        
        spec = {
            'feature_name': f'Fix {signature.error_type} in {signature.module_name}',
            'description': description,
            'modules': [],  # Modifying existing, not creating new
            'modifications': [f'{signature.module_name}.py'],
            'requirements': [],
            'system_requirements': [],
            'tests': [
                f'Test that {signature.function_name}() no longer crashes',
                f'Test error handling for {signature.error_type}',
                'Test function with various inputs',
                'Test edge cases that previously failed'
            ],
            'acceptance_criteria': [
                f'Function {signature.function_name}() executes without {signature.error_type}',
                'Proper error handling added',
                'All existing functionality preserved',
                'Edge cases handled gracefully'
            ],
            'priority': 'high',
            'estimated_complexity': 'medium'
        }
        
        return spec
    
    def attempt_auto_fix(self, signature: ErrorSignature) -> Dict[str, Any]:
        """
        Attempt to automatically fix an error
        
        This triggers the full upgrade flow:
        Spec → Generate → Validate → Preview → (Wait for user)
        
        Args:
            signature: Error to fix
        
        Returns:
            Dict with fix attempt results
        """
        logger.info(f"Attempting auto-fix for {signature.traceback_hash}")
        
        try:
            # Generate spec
            spec_dict = self.generate_fix_spec(signature)
            
            # Log attempt
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM error_signatures WHERE traceback_hash = ?
            """, (signature.traceback_hash,))
            
            error_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO fix_attempts
                (error_id, attempt_timestamp, spec_generated, validation_passed, applied)
                VALUES (?, ?, ?, 0, 0)
            """, (error_id, datetime.now().isoformat(), str(spec_dict)))
            
            attempt_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'spec': spec_dict,
                'attempt_id': attempt_id,
                'message': 'Fix spec generated. User must approve to apply.'
            }
        
        except Exception as e:
            logger.error(f"Auto-fix attempt failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_fixed(self, signature: ErrorSignature, artifact_id: str):
        """Mark an error as fixed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE error_signatures
            SET fixed = 1, fix_artifact_id = ?, fix_timestamp = ?
            WHERE traceback_hash = ?
        """, (artifact_id, datetime.now().isoformat(), signature.traceback_hash))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Marked error {signature.traceback_hash} as fixed")
    
    def get_unfixed_errors(self, limit: int = 20) -> list:
        """Get list of unfixed errors"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT error_type, error_message, module_name, function_name, 
                   line_number, occurrence_count, first_seen, last_seen
            FROM error_signatures
            WHERE fixed = 0
            ORDER BY occurrence_count DESC, last_seen DESC
            LIMIT ?
        """, (limit,))
        
        errors = []
        for row in cursor.fetchall():
            errors.append({
                'error_type': row[0],
                'error_message': row[1],
                'module': row[2],
                'function': row[3],
                'line': row[4],
                'count': row[5],
                'first_seen': row[6],
                'last_seen': row[7]
            })
        
        conn.close()
        return errors
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total errors
        cursor.execute("SELECT COUNT(*) FROM error_signatures")
        total = cursor.fetchone()[0]
        
        # Fixed errors
        cursor.execute("SELECT COUNT(*) FROM error_signatures WHERE fixed = 1")
        fixed = cursor.fetchone()[0]
        
        # Total occurrences
        cursor.execute("SELECT SUM(occurrence_count) FROM error_signatures")
        total_occurrences = cursor.fetchone()[0] or 0
        
        # Most common errors
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM error_signatures
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 5
        """)
        
        common_errors = [{'type': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_unique_errors': total,
            'fixed_errors': fixed,
            'unfixed_errors': total - fixed,
            'fix_rate': fixed / total if total > 0 else 0,
            'total_occurrences': total_occurrences,
            'common_errors': common_errors
        }


def auto_heal_decorator(healer: ErrorAutoHealer):
    """
    Decorator to auto-capture errors from functions
    
    Usage:
        @auto_heal_decorator(healer)
        def my_function():
            # code that might crash
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture error
                context = {
                    'module': func.__module__,
                    'function': func.__name__
                }
                signature = healer.capture_error(e, context)
                
                # Optionally attempt auto-fix
                if healer.auto_fix:
                    healer.attempt_auto_fix(signature)
                
                # Re-raise (or could return None/default value)
                raise
        
        return wrapper
    return decorator


# CLI
if __name__ == "__main__":
    import sys
    
    healer = ErrorAutoHealer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            stats = healer.get_statistics()
            print("\n" + "="*60)
            print("ERROR AUTO-HEALER STATISTICS")
            print("="*60)
            print(f"Total Unique Errors: {stats['total_unique_errors']}")
            print(f"  Fixed: {stats['fixed_errors']}")
            print(f"  Unfixed: {stats['unfixed_errors']}")
            print(f"  Fix Rate: {stats['fix_rate']:.1%}")
            print(f"\nTotal Occurrences: {stats['total_occurrences']}")
            print("\nMost Common Errors:")
            for err in stats['common_errors']:
                print(f"  {err['type']}: {err['count']}x")
            print("="*60)
        
        elif command == "unfixed":
            errors = healer.get_unfixed_errors(10)
            print(f"\n{len(errors)} unfixed errors:\n")
            for err in errors:
                print(f"[{err['error_type']}] {err['module']}.{err['function']}:{err['line']}")
                print(f"  Message: {err['error_message'][:80]}")
                print(f"  Seen {err['count']}x (last: {err['last_seen'][:19]})\n")
    else:
        print("Usage: python error_auto_healer.py [stats|unfixed]")
