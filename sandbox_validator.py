import ast
import traceback
import tempfile
import os
import subprocess
from typing import Dict, List, Optional

class ValidationResult:
    def __init__(self, passed: bool, errors: List[str]):
        self.passed = passed
        self.errors = errors

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "errors": self.errors
        }

class SandboxValidator:
    def __init__(self):
        pass

    def test(self, artifact_code: str, spec: dict) -> ValidationResult:
        errors = []

        # Step 1: Syntax check using AST
        try:
            ast.parse(artifact_code)
        except SyntaxError as e:
            errors.append(f"SyntaxError: {e}")
        except Exception as e:
            errors.append(f"Unknown parse error: {e}")

        # Step 2: Import check via py_compile
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
                tf.write(artifact_code)
                temp_path = tf.name

            result = subprocess.run(
                ["python", "-m", "py_compile", temp_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                errors.append(f"Import/Syntax check failed: {result.stderr.strip()}")
        except Exception as e:
            errors.append(f"Import validation error: {e}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        # Step 3: Run any test snippets from the spec
        test_cmds = spec.get("tests", [])
        for test in test_cmds:
            try:
                test_code = test.get("code")
                if not test_code:
                    continue
                exec(test_code, {})
            except Exception as e:
                errors.append(f"Test '{test.get('name', 'unknown')}' failed: {e}")

        return ValidationResult(passed=(len(errors) == 0), errors=errors)
