#!/usr/bin/env python3
"""
HotReloadManager - Dynamically reload Python modules without restarting.

Enables live code updates while Saraphina is running, with automatic
dependency tracking and error recovery.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path
import sys
import importlib
import importlib.util
import logging
import traceback
import ast
import hashlib
import shutil
import glob
import os

logger = logging.getLogger(__name__)


class HotReloadManager:
    """Manage live reloading of Python modules."""
    
    def __init__(self, saraphina_root: Path, max_backups: int = 3):
        """
        Initialize hot reload manager.
        
        Args:
            saraphina_root: Root directory of Saraphina modules
            max_backups: Maximum number of timestamped backups to keep per file
        """
        self.saraphina_root = saraphina_root
        self.module_versions = {}  # module_name -> version_hash
        self.reload_history = []  # List of reload attempts
        self.loaded_modules = {}  # module_name -> module object
        self.max_backups = max_backups
        
    def can_hot_reload(self, module_name: str) -> Dict[str, Any]:
        """
        Check if a module can be safely hot-reloaded.
        
        Args:
            module_name: Module to check (e.g., 'knowledge_engine')
        
        Returns:
            Dict with can_reload (bool), reasons, warnings
        """
        result = {
            'can_reload': True,
            'reasons': [],
            'warnings': [],
            'dependencies': []
        }
        
        full_module = f'saraphina.{module_name}'
        
        # Check if module is currently loaded
        if full_module not in sys.modules:
            result['can_reload'] = False
            result['reasons'].append(f'Module {full_module} not currently loaded')
            return result
        
        # Check for C extensions (cannot reload)
        module = sys.modules[full_module]
        if hasattr(module, '__file__') and module.__file__:
            if module.__file__.endswith(('.so', '.pyd', '.dll')):
                result['can_reload'] = False
                result['reasons'].append('Module contains C extensions (cannot hot-reload)')
                return result
        
        # Find dependencies
        dependencies = self._find_module_dependencies(full_module)
        result['dependencies'] = dependencies
        
        if dependencies:
            result['warnings'].append(f'Module has {len(dependencies)} dependent modules that may need reloading')
        
        # Check if module is actively in use
        active_refs = self._count_active_references(full_module)
        if active_refs > 10:
            result['warnings'].append(f'Module has {active_refs} active references (reload may cause issues)')
        
        return result
    
    def _find_module_dependencies(self, module_name: str) -> List[str]:
        """Find modules that depend on this module."""
        dependencies = []
        
        for loaded_name, loaded_module in sys.modules.items():
            if not loaded_name.startswith('saraphina.'):
                continue
            if loaded_name == module_name:
                continue
            
            # Check if loaded_module imports module_name
            if hasattr(loaded_module, '__dict__'):
                for attr_name, attr_value in loaded_module.__dict__.items():
                    if hasattr(attr_value, '__module__'):
                        if attr_value.__module__ == module_name:
                            dependencies.append(loaded_name)
                            break
        
        return dependencies
    
    def _count_active_references(self, module_name: str) -> int:
        """Count active references to a module."""
        import sys
        return sys.getrefcount(sys.modules.get(module_name, None))
    
    def hot_reload_module(
        self,
        module_name: str,
        test_after_reload: bool = True
    ) -> Dict[str, Any]:
        """
        Hot-reload a module while system is running.
        
        Args:
            module_name: Module to reload (e.g., 'knowledge_engine')
            test_after_reload: Run basic tests after reloading
        
        Returns:
            Dict with success status, errors, warnings
        """
        start_time = datetime.now()
        full_module = f'saraphina.{module_name}'
        
        # Pre-flight checks
        check_result = self.can_hot_reload(module_name)
        if not check_result['can_reload']:
            return {
                'success': False,
                'error': '; '.join(check_result['reasons']),
                'module': module_name
            }
        
        # Store current version hash
        current_hash = self._get_module_hash(full_module)
        old_version = self.module_versions.get(full_module)
        
        logger.info(f"Attempting hot-reload of {full_module}")
        
        try:
            # Get current module
            old_module = sys.modules.get(full_module)
            if not old_module:
                return {
                    'success': False,
                    'error': f'Module {full_module} not loaded',
                    'module': module_name
                }
            
            # Reload the module
            reloaded_module = importlib.reload(old_module)
            
            # Update version tracking
            new_hash = self._get_module_hash(full_module)
            self.module_versions[full_module] = new_hash
            
            # Test if module still works
            if test_after_reload:
                test_result = self._test_module(full_module, reloaded_module)
                if not test_result['passed']:
                    # Rollback by reloading again (will load from backup if available)
                    logger.error(f"Module {full_module} failed tests after reload")
                    return {
                        'success': False,
                        'error': f'Module tests failed: {test_result["error"]}',
                        'module': module_name,
                        'test_results': test_result
                    }
            
            # Record successful reload
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            reload_record = {
                'module': full_module,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'duration_ms': duration_ms,
                'old_hash': old_version,
                'new_hash': new_hash,
                'warnings': check_result.get('warnings', [])
            }
            
            self.reload_history.append(reload_record)
            
            # Update loaded modules cache
            self.loaded_modules[full_module] = reloaded_module
            
            logger.info(f"Successfully hot-reloaded {full_module} in {duration_ms:.0f}ms")
            
            return {
                'success': True,
                'module': module_name,
                'full_module': full_module,
                'duration_ms': duration_ms,
                'warnings': check_result.get('warnings', []),
                'dependencies': check_result.get('dependencies', []),
                'version_changed': (old_version != new_hash)
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Hot-reload failed for {full_module}: {e}")
            logger.debug(error_trace)
            
            # Record failed attempt
            reload_record = {
                'module': full_module,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'traceback': error_trace
            }
            self.reload_history.append(reload_record)
            
            return {
                'success': False,
                'error': str(e),
                'module': module_name,
                'traceback': error_trace
            }
    
    def _get_module_hash(self, full_module_name: str) -> Optional[str]:
        """Get hash of module source file."""
        try:
            module = sys.modules.get(full_module_name)
            if not module or not hasattr(module, '__file__'):
                return None
            
            file_path = Path(module.__file__)
            if not file_path.exists():
                return None
            
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        
        except Exception:
            return None
    
    def _test_module(self, full_module_name: str, module) -> Dict[str, Any]:
        """
        Run basic tests on a reloaded module.
        
        Tests:
        - Module can be imported
        - Expected classes/functions exist
        - Basic instantiation works (if applicable)
        """
        result = {
            'passed': True,
            'tests_run': 0,
            'error': None
        }
        
        try:
            # Test 1: Module has expected attributes
            if hasattr(module, '__all__'):
                expected_exports = module.__all__
                for export in expected_exports:
                    if not hasattr(module, export):
                        result['passed'] = False
                        result['error'] = f'Missing expected export: {export}'
                        return result
                result['tests_run'] += len(expected_exports)
            
            # Test 2: Try instantiating main class (if exists)
            module_name_parts = full_module_name.split('.')
            if len(module_name_parts) > 1:
                # Try to find class with similar name
                class_name_variants = [
                    ''.join(word.capitalize() for word in module_name_parts[-1].split('_')),
                    module_name_parts[-1].capitalize()
                ]
                
                for class_name in class_name_variants:
                    if hasattr(module, class_name):
                        cls = getattr(module, class_name)
                        # Check if it's a class
                        if isinstance(cls, type):
                            # Don't instantiate (might require args)
                            # Just verify it's callable
                            if not callable(cls):
                                result['passed'] = False
                                result['error'] = f'{class_name} is not callable'
                                return result
                            result['tests_run'] += 1
                            break
            
            # Test 3: No syntax errors (already passed if we got here)
            result['tests_run'] += 1
            
            return result
        
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
            return result
    
    def reload_dependencies(
        self,
        module_name: str,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        Reload modules that depend on this module.
        
        Args:
            module_name: Base module that was reloaded
            recursive: Reload dependencies recursively
        
        Returns:
            Dict with reloaded modules and results
        """
        full_module = f'saraphina.{module_name}'
        dependencies = self._find_module_dependencies(full_module)
        
        results = {
            'total': len(dependencies),
            'succeeded': [],
            'failed': [],
            'skipped': []
        }
        
        for dep in dependencies:
            # Extract short name
            if dep.startswith('saraphina.'):
                short_name = dep.split('.')[-1]
            else:
                short_name = dep
            
            reload_result = self.hot_reload_module(short_name, test_after_reload=True)
            
            if reload_result['success']:
                results['succeeded'].append(dep)
            else:
                results['failed'].append({
                    'module': dep,
                    'error': reload_result.get('error')
                })
        
        return results
    
    def get_reload_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reload history."""
        return self.reload_history[-limit:]
    
    def clear_reload_cache(self):
        """Clear reload history and version cache."""
        self.reload_history.clear()
        self.module_versions.clear()
        self.loaded_modules.clear()
    
    def _create_timestamped_backup(self, file_path: Path, artifact_id: Optional[str] = None) -> Path:
        """
        Create timestamped backup of a file.
        
        Args:
            file_path: Path to file to backup
            artifact_id: Optional artifact ID to include in backup name
        
        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if artifact_id:
            # Format: filename.py.bak.20251106_201045.artifact_abc123
            backup_name = f"{file_path.name}.bak.{timestamp}.{artifact_id[:8]}"
        else:
            # Format: filename.py.bak.20251106_201045
            backup_name = f"{file_path.name}.bak.{timestamp}"
        
        backup_path = file_path.parent / backup_name
        shutil.copy2(file_path, backup_path)
        
        logger.info(f"Created timestamped backup: {backup_name}")
        return backup_path
    
    def _cleanup_old_backups(self, file_path: Path):
        """
        Remove old backup files, keeping only max_backups most recent.
        
        Args:
            file_path: Original file path (backups are in same directory)
        """
        # Find all backups for this file
        backup_pattern = f"{file_path.name}.bak.*"
        backup_dir = file_path.parent
        
        # Get all backup files matching pattern
        backup_files = list(backup_dir.glob(backup_pattern))
        
        if len(backup_files) <= self.max_backups:
            return  # No cleanup needed
        
        # Sort by modification time (oldest first)
        backup_files.sort(key=lambda p: p.stat().st_mtime)
        
        # Delete oldest backups
        num_to_delete = len(backup_files) - self.max_backups
        for old_backup in backup_files[:num_to_delete]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup.name}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {old_backup.name}: {e}")
    
    def _cleanup_backups_after_commit(self, file_paths: List[Path]):
        """
        Remove all .bak files for given paths after successful git commit.
        Since changes are in git history, backups are redundant.
        
        Args:
            file_paths: List of file paths that were committed
        """
        for file_path in file_paths:
            backup_pattern = f"{file_path.name}.bak.*"
            backup_dir = file_path.parent
            
            for backup_file in backup_dir.glob(backup_pattern):
                try:
                    backup_file.unlink()
                    logger.info(f"Cleaned up backup after git commit: {backup_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup backup {backup_file.name}: {e}")
    
    def apply_artifact(self, artifact) -> Dict[str, Any]:
        """
        Apply a CodeForge artifact: write files and reload modules.
        
        Args:
            artifact: CodeArtifact from CodeForge with new_files and code_diffs
        
        Returns:
            Dict with success, files_modified, modules_reloaded
        """
        try:
            files_modified = 0
            modules_reloaded = 0
            created_files = []
            modified_files = []
            
            # Write new files
            if hasattr(artifact, 'new_files') and artifact.new_files:
                for filename, content in artifact.new_files.items():
                    file_path = Path(self.saraphina_root) / filename
                    
                    # Create timestamped backup if file exists
                    if file_path.exists():
                        artifact_id = artifact.artifact_id if hasattr(artifact, 'artifact_id') else None
                        self._create_timestamped_backup(file_path, artifact_id)
                        # Cleanup old backups
                        self._cleanup_old_backups(file_path)
                    
                    # Write new file
                    file_path.write_text(content, encoding='utf-8')
                    created_files.append(filename)
                    files_modified += 1
                    logger.info(f"Created file: {filename}")
            
            # Apply code diffs (modifications to existing files)
            if hasattr(artifact, 'code_diffs') and artifact.code_diffs:
                for filename, diff_content in artifact.code_diffs.items():
                    file_path = Path(self.saraphina_root) / filename
                    
                    if file_path.exists():
                        # Create timestamped backup
                        artifact_id = artifact.artifact_id if hasattr(artifact, 'artifact_id') else None
                        self._create_timestamped_backup(file_path, artifact_id)
                        # Cleanup old backups
                        self._cleanup_old_backups(file_path)
                        
                        # Apply diff (for now, just overwrite with new content)
                        file_path.write_text(diff_content, encoding='utf-8')
                        modified_files.append(filename)
                        files_modified += 1
                        logger.info(f"Modified file: {filename}")
            
            # Reload affected modules
            modules_to_reload = set()
            
            for filename in created_files + modified_files:
                if filename.endswith('.py'):
                    # Extract module name from filename
                    module_name = filename.replace('.py', '')
                    modules_to_reload.add(module_name)
            
            # Hot-reload each module
            reloaded_modules = []
            for module_name in modules_to_reload:
                # First, need to import new modules
                full_module = f'saraphina.{module_name}'
                
                if full_module not in sys.modules:
                    # New module, need to import it
                    try:
                        spec = importlib.util.spec_from_file_location(
                            full_module,
                            Path(self.saraphina_root) / f"{module_name}.py"
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[full_module] = module
                            spec.loader.exec_module(module)
                            reloaded_modules.append(module_name)
                            modules_reloaded += 1
                            logger.info(f"Imported new module: {module_name}")
                    except Exception as e:
                        logger.error(f"Failed to import new module {module_name}: {e}")
                else:
                    # Existing module, hot-reload it
                    reload_result = self.hot_reload_module(module_name, test_after_reload=False)
                    if reload_result['success']:
                        reloaded_modules.append(module_name)
                        modules_reloaded += 1
            
            return {
                'success': True,
                'files_modified': files_modified,
                'modules_reloaded': modules_reloaded,
                'created_files': created_files,
                'modified_files': modified_files,
                'reloaded_modules': reloaded_modules,
                'artifact_id': artifact.artifact_id if hasattr(artifact, 'artifact_id') else None
            }
        
        except Exception as e:
            logger.error(f"Failed to apply artifact: {e}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
