#!/usr/bin/env python3
"""
TestHarness - Safe sandboxed execution of generated code with testing.

Runs code in isolated environment, executes pytest, measures coverage,
and performs static analysis.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json


class TestHarness:
    """Execute and test generated code in sandbox environment."""
    
    def __init__(self, sandbox_root: Optional[str] = None):
        """
        Initialize test harness.
        
        Args:
            sandbox_root: Root directory for sandbox (temp dir if None)
        """
        self.sandbox_root = Path(sandbox_root) if sandbox_root else Path(tempfile.gettempdir()) / "saraphina_sandbox"
        self.sandbox_root.mkdir(exist_ok=True, parents=True)
    
    def execute_sandbox(
        self,
        proposal_id: str,
        code: str,
        tests: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Execute code in sandbox with full test suite.
        
        Args:
            proposal_id: Unique identifier for the proposal
            code: Main code to test
            tests: Test code
            language: Programming language
        
        Returns:
            Dict with test results, coverage, static analysis
        """
        if language != "python":
            return {
                'success': False,
                'error': f'Language {language} not yet supported',
                'proposal_id': proposal_id
            }
        
        # Create isolated sandbox directory
        sandbox_dir = self.sandbox_root / proposal_id
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir)
        sandbox_dir.mkdir(parents=True)
        
        try:
            # Write code and tests to files
            code_file = sandbox_dir / "code.py"
            test_file = sandbox_dir / "test_code.py"
            
            code_file.write_text(code, encoding='utf-8')
            test_file.write_text(tests, encoding='utf-8')
            
            results = {
                'success': True,
                'proposal_id': proposal_id,
                'sandbox_dir': str(sandbox_dir),
                'executed_at': datetime.now().isoformat()
            }
            
            # Run static analysis
            results['static_analysis'] = self._run_static_analysis(code_file)
            
            # Run tests with pytest
            results['test_results'] = self._run_pytest(sandbox_dir, test_file)
            
            # Run coverage analysis
            results['coverage'] = self._run_coverage(sandbox_dir, code_file, test_file)
            
            # Overall assessment
            results['passed'] = (
                results['test_results'].get('passed', False) and
                not results['static_analysis'].get('critical_issues', False)
            )
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'proposal_id': proposal_id,
                'sandbox_dir': str(sandbox_dir)
            }
    
    def _run_static_analysis(self, code_file: Path) -> Dict[str, Any]:
        """Run pylint or flake8 on code."""
        results = {
            'tool': None,
            'score': None,
            'issues': [],
            'critical_issues': False
        }
        
        # Try pylint first
        try:
            cmd = [sys.executable, '-m', 'pylint', str(code_file), '--output-format=json']
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=code_file.parent
            )
            
            results['tool'] = 'pylint'
            
            if proc.stdout:
                try:
                    issues = json.loads(proc.stdout)
                    results['issues'] = [
                        {
                            'type': issue.get('type'),
                            'message': issue.get('message'),
                            'line': issue.get('line'),
                            'symbol': issue.get('symbol')
                        }
                        for issue in issues[:10]  # Limit to 10
                    ]
                    # Check for critical issues (errors)
                    results['critical_issues'] = any(
                        issue.get('type') == 'error' for issue in issues
                    )
                except json.JSONDecodeError:
                    pass
            
            # Extract score from stderr (pylint outputs to stderr)
            if proc.stderr:
                import re
                score_match = re.search(r'Your code has been rated at ([\d.]+)/10', proc.stderr)
                if score_match:
                    results['score'] = float(score_match.group(1))
            
            return results
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to flake8
        try:
            cmd = [sys.executable, '-m', 'flake8', str(code_file), '--format=json']
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=code_file.parent
            )
            
            results['tool'] = 'flake8'
            
            if proc.stdout:
                # Flake8 output: filename:line:col: code message
                lines = proc.stdout.strip().split('\n')
                issues = []
                for line in lines[:10]:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        issues.append({
                            'line': parts[1],
                            'col': parts[2],
                            'message': parts[3].strip()
                        })
                results['issues'] = issues
                results['critical_issues'] = any('E' in str(i.get('message', '')) for i in issues)
            
            return results
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results['tool'] = 'none'
            results['error'] = 'No static analysis tools available (install pylint or flake8)'
            return results
    
    def _run_pytest(self, sandbox_dir: Path, test_file: Path) -> Dict[str, Any]:
        """Run pytest on test file."""
        results = {
            'passed': False,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'duration': 0.0,
            'output': '',
            'errors': []
        }
        
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_file),
                '-v',
                '--tb=short',
                '--json-report',
                '--json-report-file=report.json'
            ]
            
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=sandbox_dir
            )
            
            results['output'] = proc.stdout
            
            # Try to read JSON report
            report_file = sandbox_dir / 'report.json'
            if report_file.exists():
                try:
                    report = json.loads(report_file.read_text())
                    summary = report.get('summary', {})
                    results['tests_run'] = summary.get('total', 0)
                    results['tests_passed'] = summary.get('passed', 0)
                    results['tests_failed'] = summary.get('failed', 0)
                    results['duration'] = report.get('duration', 0.0)
                    
                    # Extract test details
                    tests = report.get('tests', [])
                    for test in tests:
                        if test.get('outcome') == 'failed':
                            results['errors'].append({
                                'test': test.get('nodeid'),
                                'message': test.get('call', {}).get('longrepr', 'Unknown error')
                            })
                    
                except json.JSONDecodeError:
                    pass
            
            # Parse stdout if no JSON
            if results['tests_run'] == 0:
                import re
                match = re.search(r'(\d+) passed', proc.stdout)
                if match:
                    results['tests_passed'] = int(match.group(1))
                    results['tests_run'] = results['tests_passed']
                
                match = re.search(r'(\d+) failed', proc.stdout)
                if match:
                    results['tests_failed'] = int(match.group(1))
                    results['tests_run'] += results['tests_failed']
            
            results['passed'] = proc.returncode == 0 and results['tests_failed'] == 0
            
            return results
            
        except subprocess.TimeoutExpired:
            results['error'] = 'Tests timed out (60s limit)'
            return results
        except FileNotFoundError:
            results['error'] = 'pytest not available (install pytest)'
            return results
        except Exception as e:
            results['error'] = str(e)
            return results
    
    def _run_coverage(
        self,
        sandbox_dir: Path,
        code_file: Path,
        test_file: Path
    ) -> Dict[str, Any]:
        """Measure code coverage."""
        results = {
            'available': False,
            'coverage_percent': 0.0,
            'lines_covered': 0,
            'lines_total': 0,
            'missing_lines': []
        }
        
        try:
            # Run coverage
            cmd = [
                sys.executable, '-m', 'coverage', 'run',
                '--source', str(code_file.stem),
                '-m', 'pytest',
                str(test_file),
                '-q'
            ]
            
            subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
                cwd=sandbox_dir
            )
            
            # Get coverage report
            cmd = [sys.executable, '-m', 'coverage', 'json', '-o', 'coverage.json']
            subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                cwd=sandbox_dir
            )
            
            # Read coverage data
            cov_file = sandbox_dir / 'coverage.json'
            if cov_file.exists():
                cov_data = json.loads(cov_file.read_text())
                totals = cov_data.get('totals', {})
                
                results['available'] = True
                results['coverage_percent'] = totals.get('percent_covered', 0.0)
                results['lines_covered'] = totals.get('covered_lines', 0)
                results['lines_total'] = totals.get('num_statements', 0)
                
                # Get missing lines
                files = cov_data.get('files', {})
                for file_data in files.values():
                    missing = file_data.get('missing_lines', [])
                    if missing:
                        results['missing_lines'] = missing[:20]  # Limit
            
            return results
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results['error'] = 'coverage not available (install coverage)'
            return results
        except Exception as e:
            results['error'] = str(e)
            return results
    
    def generate_report(self, execution_results: Dict[str, Any]) -> str:
        """Generate human-readable test report."""
        if not execution_results.get('success'):
            return f"❌ Execution failed: {execution_results.get('error', 'Unknown error')}"
        
        report = []
        report.append(f"📊 **Test Report for {execution_results['proposal_id']}**\n")
        
        # Overall status
        if execution_results.get('passed'):
            report.append("✅ **Status:** PASSED")
        else:
            report.append("❌ **Status:** FAILED")
        
        report.append("")
        
        # Test results
        test_res = execution_results.get('test_results', {})
        if test_res:
            report.append("**Test Execution:**")
            report.append(f"  - Tests run: {test_res.get('tests_run', 0)}")
            report.append(f"  - Passed: {test_res.get('tests_passed', 0)}")
            report.append(f"  - Failed: {test_res.get('tests_failed', 0)}")
            report.append(f"  - Duration: {test_res.get('duration', 0):.2f}s")
            
            if test_res.get('errors'):
                report.append("\n**Failed Tests:**")
                for err in test_res['errors'][:3]:
                    report.append(f"  - {err.get('test', 'unknown')}")
                    msg = err.get('message', '')[:200]
                    report.append(f"    {msg}")
            report.append("")
        
        # Coverage
        cov = execution_results.get('coverage', {})
        if cov.get('available'):
            report.append("**Code Coverage:**")
            report.append(f"  - Coverage: {cov.get('coverage_percent', 0):.1f}%")
            report.append(f"  - Lines covered: {cov.get('lines_covered', 0)}/{cov.get('lines_total', 0)}")
            
            if cov.get('missing_lines'):
                missing = cov['missing_lines'][:10]
                report.append(f"  - Missing lines: {', '.join(map(str, missing))}")
            report.append("")
        
        # Static analysis
        static = execution_results.get('static_analysis', {})
        if static.get('tool'):
            report.append("**Static Analysis:**")
            report.append(f"  - Tool: {static['tool']}")
            
            if static.get('score') is not None:
                report.append(f"  - Score: {static['score']:.1f}/10")
            
            if static.get('critical_issues'):
                report.append("  - ⚠️ Critical issues found")
            
            if static.get('issues'):
                report.append(f"  - Issues: {len(static['issues'])}")
                for issue in static['issues'][:3]:
                    msg = issue.get('message', 'unknown')[:100]
                    line = issue.get('line', '?')
                    report.append(f"    Line {line}: {msg}")
            report.append("")
        
        return "\n".join(report)
    
    def cleanup_sandbox(self, proposal_id: str) -> bool:
        """Remove sandbox directory."""
        sandbox_dir = self.sandbox_root / proposal_id
        if sandbox_dir.exists():
            try:
                shutil.rmtree(sandbox_dir)
                return True
            except Exception:
                return False
        return False
