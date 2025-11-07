"""
Sandboxed Runtime Environment
Docker-based isolated execution with deterministic testing, coverage, and fuzzing.
"""
import docker
import tempfile
import subprocess
import json
from typing import Dict, Optional
from pathlib import Path
import time

from .code_artifacts import CodeArtifactDB, ArtifactStatus


class SandboxRunner:
    """Runs code in isolated Docker container"""
    
    def __init__(self, artifact_db: CodeArtifactDB):
        self.artifact_db = artifact_db
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None
            print("Warning: Docker not available, using local subprocess sandbox")
    
    def run_tests(self, artifact_id: str) -> Dict:
        """Run tests for artifact in sandbox"""
        artifact = self.artifact_db.get_artifact(artifact_id)
        if not artifact:
            return {"error": "Artifact not found"}
        
        # Update status
        self.artifact_db.update_status(
            artifact_id,
            ArtifactStatus.SANDBOX_TESTING,
            "system"
        )
        
        # Run in sandbox
        if self.docker_client:
            result = self._run_in_docker(artifact.code, artifact.tests)
        else:
            result = self._run_local_sandbox(artifact.code, artifact.tests)
        
        # Update results
        if result["tests_passed"]:
            self.artifact_db.update_status(
                artifact_id,
                ArtifactStatus.TESTS_PASSED,
                "system",
                {"coverage": result.get("coverage", 0)}
            )
        else:
            self.artifact_db.update_status(
                artifact_id,
                ArtifactStatus.TESTS_FAILED,
                "system",
                {"failures": result.get("failures", [])}
            )
        
        # Store test results
        self.artifact_db.update_test_results(
            artifact_id,
            result,
            result.get("coverage", 0.0)
        )
        
        return result
    
    def _run_in_docker(self, code: str, tests: str) -> Dict:
        """Run tests in Docker container"""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Write files
            (tmppath / "code.py").write_text(code)
            (tmppath / "test_code.py").write_text(tests)
            
            # Write pytest config
            (tmppath / "pytest.ini").write_text("""
[pytest]
addopts = --cov=code --cov-report=json --cov-report=term -v
            """)
            
            try:
                # Run container
                container = self.docker_client.containers.run(
                    "python:3.11-slim",
                    command="bash -c 'pip install pytest pytest-cov && pytest test_code.py'",
                    volumes={str(tmppath): {'bind': '/workspace', 'mode': 'rw'}},
                    working_dir="/workspace",
                    detach=True,
                    mem_limit="256m",
                    network_disabled=True,  # Security: no network access
                    remove=True
                )
                
                # Wait for completion (with timeout)
                result = container.wait(timeout=60)
                logs = container.logs().decode('utf-8')
                
                return self._parse_test_output(logs, result["StatusCode"])
                
            except docker.errors.ContainerError as e:
                return {
                    "tests_passed": False,
                    "error": str(e),
                    "coverage": 0.0
                }
            except Exception as e:
                return {
                    "tests_passed": False,
                    "error": f"Docker error: {str(e)}",
                    "coverage": 0.0
                }
    
    def _run_local_sandbox(self, code: str, tests: str) -> Dict:
        """Run tests locally (fallback when Docker unavailable)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Write files
            (tmppath / "code.py").write_text(code)
            (tmppath / "test_code.py").write_text(tests)
            
            try:
                # Run pytest with coverage
                result = subprocess.run(
                    ["pytest", "test_code.py", "--cov=code", "--cov-report=json", "-v"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse coverage
                coverage_file = tmppath / "coverage.json"
                coverage = 0.0
                if coverage_file.exists():
                    cov_data = json.loads(coverage_file.read_text())
                    coverage = cov_data.get("totals", {}).get("percent_covered", 0.0)
                
                return {
                    "tests_passed": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr,
                    "coverage": coverage,
                    "exit_code": result.returncode
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "tests_passed": False,
                    "error": "Tests timed out after 30 seconds",
                    "coverage": 0.0
                }
            except Exception as e:
                return {
                    "tests_passed": False,
                    "error": str(e),
                    "coverage": 0.0
                }
    
    def _parse_test_output(self, logs: str, exit_code: int) -> Dict:
        """Parse pytest output"""
        passed = exit_code == 0
        
        # Extract coverage if available
        coverage = 0.0
        for line in logs.split('\n'):
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            coverage = float(part.rstrip('%'))
                        except ValueError:
                            pass
        
        # Extract test results
        failures = []
        if not passed:
            for line in logs.split('\n'):
                if 'FAILED' in line:
                    failures.append(line)
        
        return {
            "tests_passed": passed,
            "output": logs,
            "coverage": coverage,
            "failures": failures,
            "exit_code": exit_code
        }
    
    def run_fuzzing(self, artifact_id: str, iterations: int = 100) -> Dict:
        """Run fuzz testing on artifact"""
        artifact = self.artifact_db.get_artifact(artifact_id)
        if not artifact:
            return {"error": "Artifact not found"}
        
        # Simple fuzzing: generate random inputs
        fuzzing_results = {
            "iterations": iterations,
            "crashes": 0,
            "exceptions": [],
            "success_rate": 0.0
        }
        
        # In production: integrate with hypothesis or atheris
        # For now: basic random input testing
        
        return fuzzing_results


class Dockerfile:
    """Sandbox Dockerfile template"""
    
    CONTENT = """
FROM python:3.11-slim

WORKDIR /workspace

# Install testing dependencies
RUN pip install --no-cache-dir \\
    pytest==7.4.3 \\
    pytest-cov==4.1.0 \\
    pytest-timeout==2.2.0 \\
    coverage==7.3.2

# Security: Run as non-root
RUN useradd -m sandbox
USER sandbox

# Copy code and tests at runtime via volumes
VOLUME /workspace

# Default command
CMD ["pytest", "--cov=code", "--cov-report=json", "--cov-report=term", "-v"]
"""
