#!/usr/bin/env python3
"""
SandboxValidator - Tests generated code before applying it

Prevents broken code from being deployed by:
1. Syntax checking
2. Import testing
3. Static analysis
4. Running unit tests
"""
import os
import sys
import ast
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("SandboxValidator")


@dataclass
class ValidationResult:
    """Results from validation"""
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'errors': self.errors,
            'warnings': self.warnings,
            'tests_run': self.tests_run,
            'tests_passed': self.tests_passed,
            'tests_failed': self.tests_failed
        }


class SandboxValidator:
    """Validates generated code in a safe sandbox environment"""
    
    def __init__(self, saraphina_root: str = "D:\\Saraphina Root\\saraphina",
                 auto_install: bool = True):
        self.saraphina_root = Path(saraphina_root)
        self.temp_dir = None
        self.auto_install = auto_install
    
    def test(self, artifact, spec=None) -> ValidationResult:
        """
        Test an artifact before applying
        
        Args:
            artifact: CodeArtifact from CodeForge
            spec: Optional UpgradeSpec for additional context
        
        Returns:
            ValidationResult with pass/fail and details
        """
        logger.info(f"Validating artifact: {artifact.artifact_id}")
        
        result = ValidationResult(passed=True)
        
        # Create temp sandbox
        self.temp_dir = Path(tempfile.mkdtemp(prefix="saraphina_sandbox_"))
        logger.info(f"Created sandbox: {self.temp_dir}")
        
        try:
            # Step 1: Syntax Check
            syntax_ok = self._check_syntax(artifact, result)
            if not syntax_ok:
                result.passed = False
                return result
            
            # Step 2: Import Test
            import_ok = self._test_imports(artifact, result)
            if not import_ok:
                result.passed = False
                # Don't return yet - collect all errors
            
            # Step 3: Static Analysis
            self._static_analysis(artifact, result)
            
            # Step 4: Run Tests (if provided)
            if hasattr(artifact, 'tests') and artifact.tests:
                self._run_tests(artifact, result)
            
            # Final decision
            if result.errors:
                result.passed = False
            
            logger.info(f"Validation result: {'PASS' if result.passed else 'FAIL'}")
            return result
            
        finally:
            # Cleanup
            self._cleanup_sandbox()
    
    def _check_syntax(self, artifact, result: ValidationResult) -> bool:
        """Check Python syntax of all generated code"""
        logger.info("Checking syntax...")
        
        all_code = {}
        
        # Collect all code
        if hasattr(artifact, 'new_files'):
            all_code.update(artifact.new_files)
        
        if hasattr(artifact, 'code_diffs'):
            all_code.update(artifact.code_diffs)
        
        syntax_ok = True
        
        for filename, code in all_code.items():
            if not filename.endswith('.py'):
                continue
            
            try:
                ast.parse(code)
                logger.debug(f"  ✓ {filename}: Valid syntax")
            except SyntaxError as e:
                error_msg = f"Syntax error in {filename} line {e.lineno}: {e.msg}"
                result.errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
                syntax_ok = False
        
        return syntax_ok
    
    def _test_imports(self, artifact, result: ValidationResult) -> bool:
        """Test that code can be imported without errors"""
        logger.info("Testing imports...")
        
        # Write files to sandbox
        files_written = self._write_to_sandbox(artifact)
        
        import_ok = True
        
        for filename in files_written:
            if not filename.endswith('.py'):
                continue
            
            module_name = filename[:-3]  # Remove .py
            
            # Try to import
            try:
                # Add sandbox to path temporarily
                sys.path.insert(0, str(self.temp_dir))
                
                # Attempt import
                __import__(module_name)
                
                logger.debug(f"  ✓ {filename}: Imports successfully")
                
            except ImportError as e:
                error_msg = f"Import error in {filename}: {e}"
                
                # Try auto-install if enabled
                if self.auto_install:
                    package_name = self._extract_package_name(str(e))
                    if package_name:
                        logger.info(f"  📦 Attempting auto-install: {package_name}")
                        if self._auto_install_package(package_name):
                            logger.info(f"  ✓ Installed {package_name}, retrying import...")
                            try:
                                # Retry import
                                __import__(module_name)
                                logger.debug(f"  ✓ {filename}: Imports successfully after install")
                                continue  # Success!
                            except Exception:
                                pass  # Fall through to error
                
                result.errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
                import_ok = False
                
            except Exception as e:
                # Runtime errors during import
                error_msg = f"Runtime error importing {filename}: {type(e).__name__}: {e}"
                result.errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
                import_ok = False
                
            finally:
                # Remove sandbox from path
                if str(self.temp_dir) in sys.path:
                    sys.path.remove(str(self.temp_dir))
                
                # Unload module to prevent conflicts
                if module_name in sys.modules:
                    del sys.modules[module_name]
        
        return import_ok
    
    def _static_analysis(self, artifact, result: ValidationResult):
        """Run static analysis checks"""
        logger.info("Running static analysis...")
        
        # Check for common issues
        all_code = {}
        if hasattr(artifact, 'new_files'):
            all_code.update(artifact.new_files)
        if hasattr(artifact, 'code_diffs'):
            all_code.update(artifact.code_diffs)
        
        for filename, code in all_code.items():
            if not filename.endswith('.py'):
                continue
            
            # Check for circular imports
            if self._check_circular_import(filename, code):
                warning = f"Possible circular import in {filename}"
                result.warnings.append(warning)
                logger.warning(f"  ⚠ {warning}")
            
            # Check for missing dependencies
            missing_deps = self._check_dependencies(code)
            if missing_deps:
                warning = f"{filename} may need packages: {', '.join(missing_deps)}"
                result.warnings.append(warning)
                logger.warning(f"  ⚠ {warning}")
    
    def _check_circular_import(self, filename: str, code: str) -> bool:
        """Check if code imports itself"""
        module_name = filename[:-3]  # Remove .py
        
        # Look for imports of itself
        lines = code.split('\n')
        for line in lines:
            if 'import' in line and module_name in line:
                return True
        
        return False
    
    def _check_dependencies(self, code: str) -> List[str]:
        """Check for potentially missing dependencies"""
        common_packages = {
            'speech_recognition': 'speech_recognition',
            'pyaudio': 'pyaudio',
            'requests': 'requests',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'tkinter': 'tkinter'
        }
        
        missing = []
        
        for package, import_name in common_packages.items():
            if import_name in code:
                # Check if installed
                try:
                    __import__(package)
                except ImportError:
                    missing.append(package)
        
        return missing
    
    def _run_tests(self, artifact, result: ValidationResult):
        """Run unit tests if provided"""
        logger.info("Running tests...")
        
        if not hasattr(artifact, 'tests') or not artifact.tests:
            return
        
        # Write test files to sandbox
        for test_filename, test_code in artifact.tests.items():
            test_path = self.temp_dir / test_filename
            test_path.write_text(test_code, encoding='utf-8')
        
        # Run pytest
        try:
            proc = subprocess.run(
                [sys.executable, '-m', 'pytest', str(self.temp_dir), '-v'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output
            output = proc.stdout + proc.stderr
            
            # Count tests
            if 'passed' in output:
                import re
                match = re.search(r'(\d+) passed', output)
                if match:
                    result.tests_passed = int(match.group(1))
            
            if 'failed' in output:
                import re
                match = re.search(r'(\d+) failed', output)
                if match:
                    result.tests_failed = int(match.group(1))
            
            result.tests_run = result.tests_passed + result.tests_failed
            
            if result.tests_failed > 0:
                result.errors.append(f"{result.tests_failed} tests failed")
                logger.error(f"  ✗ {result.tests_failed} tests failed")
            else:
                logger.info(f"  ✓ All {result.tests_passed} tests passed")
                
        except subprocess.TimeoutExpired:
            result.errors.append("Tests timed out after 30 seconds")
            logger.error("  ✗ Tests timed out")
        except Exception as e:
            result.warnings.append(f"Could not run tests: {e}")
            logger.warning(f"  ⚠ Could not run tests: {e}")
    
    def _write_to_sandbox(self, artifact) -> List[str]:
        """Write artifact files to sandbox directory"""
        written = []
        
        if hasattr(artifact, 'new_files'):
            for filename, content in artifact.new_files.items():
                file_path = self.temp_dir / filename
                file_path.write_text(content, encoding='utf-8')
                written.append(filename)
        
        if hasattr(artifact, 'code_diffs'):
            for filename, content in artifact.code_diffs.items():
                file_path = self.temp_dir / filename
                file_path.write_text(content, encoding='utf-8')
                written.append(filename)
        
        return written
    
    def _extract_package_name(self, error_msg: str) -> str:
        """Extract package name from ImportError message"""
        import re
        
        # "No module named 'package'"
        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_msg)
        if match:
            package = match.group(1)
            # Get root package (e.g. 'package.submodule' -> 'package')
            return package.split('.')[0]
        
        return None
    
    def _auto_install_package(self, package_name: str) -> bool:
        """Attempt to install package using pip"""
        try:
            import subprocess
            import sys
            
            # Run pip install
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name}")
                return True
            else:
                logger.warning(f"Failed to install {package_name}: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Install timeout for {package_name}")
            return False
        except Exception as e:
            logger.warning(f"Install error for {package_name}: {e}")
            return False
    
    def _cleanup_sandbox(self):
        """Clean up temporary sandbox directory"""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up sandbox: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup sandbox: {e}")


# Example usage
if __name__ == "__main__":
    # Test with dummy artifact
    from dataclasses import dataclass
    
    @dataclass
    class DummyArtifact:
        artifact_id: str = "TEST-001"
        new_files: Dict[str, str] = None
        code_diffs: Dict[str, str] = None
        tests: Dict[str, str] = None
        
        def __post_init__(self):
            if self.new_files is None:
                self.new_files = {
                    'test_module.py': '''#!/usr/bin/env python3
def hello():
    return "world"

if __name__ == "__main__":
    print(hello())
'''
                }
    
    validator = SandboxValidator()
    artifact = DummyArtifact()
    
    result = validator.test(artifact)
    
    print("\n" + "="*60)
    print("VALIDATION RESULT")
    print("="*60)
    print(f"Passed: {result.passed}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print("="*60)
