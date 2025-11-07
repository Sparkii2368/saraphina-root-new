#!/usr/bin/env python3
"""
RefinementEngine - Automatic code improvement through iterative testing.

Analyzes test failures, generates targeted fixes, and retests until success
or max iterations reached.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import json


class RefinementEngine:
    """Automatically refine code based on test failures."""
    
    def __init__(self, code_factory, test_harness, proposal_db):
        """
        Initialize refinement engine.
        
        Args:
            code_factory: CodeFactory instance for code generation
            test_harness: TestHarness instance for testing
            proposal_db: CodeProposalDB instance for storage
        """
        self.code_factory = code_factory
        self.test_harness = test_harness
        self.proposal_db = proposal_db
        self.max_iterations = 3
    
    def auto_refine(
        self,
        proposal_id: str,
        max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Automatically refine code until tests pass or max iterations reached.
        
        Args:
            proposal_id: ID of proposal to refine
            max_iterations: Override default max iterations (3)
        
        Returns:
            Dict with success status, iteration count, final results
        """
        max_iter = max_iterations or self.max_iterations
        
        # Get original proposal
        proposal = self.proposal_db.get_proposal(proposal_id)
        if not proposal:
            return {
                'success': False,
                'error': 'Proposal not found',
                'proposal_id': proposal_id
            }
        
        iterations = []
        current_code = proposal['code']
        current_tests = proposal['tests']
        
        for iteration in range(1, max_iter + 1):
            print(f"\n🔄 Refinement Iteration {iteration}/{max_iter}")
            
            # Run tests
            results = self.test_harness.execute_sandbox(
                proposal_id=f"{proposal_id}_iter{iteration}",
                code=current_code,
                tests=current_tests,
                language=proposal['language']
            )
            
            # Store iteration results
            iteration_data = {
                'iteration': iteration,
                'timestamp': datetime.now().isoformat(),
                'passed': results.get('passed', False),
                'tests_run': results.get('test_results', {}).get('tests_run', 0),
                'tests_passed': results.get('test_results', {}).get('tests_passed', 0),
                'tests_failed': results.get('test_results', {}).get('tests_failed', 0),
                'coverage': results.get('coverage', {}).get('coverage_percent', 0),
                'static_score': results.get('static_analysis', {}).get('score')
            }
            iterations.append(iteration_data)
            
            # Check if tests passed
            if results.get('passed'):
                # Success! Store final version
                self.proposal_db.store_refinement(
                    proposal_id=proposal_id,
                    original_code=proposal['code'],
                    refined_code=current_code,
                    feedback=f"Auto-refined in {iteration} iteration(s)",
                    explanation="Automatic refinement via test-driven improvement"
                )
                
                return {
                    'success': True,
                    'proposal_id': proposal_id,
                    'iterations': iterations,
                    'iteration_count': iteration,
                    'final_code': current_code,
                    'final_results': results,
                    'improvement': 'Tests passed after refinement'
                }
            
            # Analyze failures
            analysis = self._analyze_failures(results, proposal['feature_spec'])
            
            # Generate fix
            print(f"   📋 Analyzing {analysis['failure_count']} failure(s)...")
            fix_result = self.code_factory.refine_code(
                original_code=current_code,
                feedback=analysis['feedback'],
                language=proposal['language']
            )
            
            if not fix_result.get('success'):
                return {
                    'success': False,
                    'error': f"Refinement generation failed: {fix_result.get('error')}",
                    'proposal_id': proposal_id,
                    'iterations': iterations
                }
            
            # Update code for next iteration
            current_code = fix_result['refined_code']
            print(f"   ✏️  Generated fix ({len(current_code)} chars)")
        
        # Max iterations reached without success
        return {
            'success': False,
            'error': f'Max iterations ({max_iter}) reached without passing tests',
            'proposal_id': proposal_id,
            'iterations': iterations,
            'iteration_count': max_iter,
            'final_code': current_code,
            'improvement': 'Partial - tests still failing'
        }
    
    def _analyze_failures(
        self,
        execution_results: Dict[str, Any],
        feature_spec: str
    ) -> Dict[str, Any]:
        """
        Analyze test failures and generate targeted feedback.
        
        Args:
            execution_results: Results from test_harness.execute_sandbox
            feature_spec: Original feature specification
        
        Returns:
            Dict with failure_count, feedback, patterns
        """
        test_res = execution_results.get('test_results', {})
        static = execution_results.get('static_analysis', {})
        
        failures = []
        patterns = []
        
        # Parse test errors
        test_errors = test_res.get('errors', [])
        for error in test_errors:
            test_name = error.get('test', 'unknown')
            message = error.get('message', '')
            
            # Extract key failure info
            failures.append({
                'test': test_name,
                'message': message[:200],
                'type': self._classify_error(message)
            })
        
        # Identify patterns
        error_types = [f['type'] for f in failures]
        if error_types.count('assertion') > 1:
            patterns.append('multiple_assertion_failures')
        if error_types.count('exception') > 0:
            patterns.append('unhandled_exceptions')
        if error_types.count('import') > 0:
            patterns.append('missing_imports')
        
        # Check static analysis issues
        if static.get('critical_issues'):
            patterns.append('critical_static_issues')
        
        # Build feedback message
        feedback = self._build_feedback(failures, patterns, feature_spec, static)
        
        return {
            'failure_count': len(failures),
            'failures': failures,
            'patterns': patterns,
            'feedback': feedback
        }
    
    def _classify_error(self, message: str) -> str:
        """Classify error type from message."""
        msg_lower = message.lower()
        
        if 'assertionerror' in msg_lower or 'assert' in msg_lower:
            return 'assertion'
        if 'importerror' in msg_lower or 'modulenotfounderror' in msg_lower:
            return 'import'
        if 'typeerror' in msg_lower:
            return 'type'
        if 'attributeerror' in msg_lower:
            return 'attribute'
        if 'keyerror' in msg_lower or 'indexerror' in msg_lower:
            return 'access'
        if 'valueerror' in msg_lower:
            return 'value'
        if 'zerodivisionerror' in msg_lower:
            return 'zero_division'
        
        return 'exception'
    
    def _build_feedback(
        self,
        failures: List[Dict[str, Any]],
        patterns: List[str],
        feature_spec: str,
        static: Dict[str, Any]
    ) -> str:
        """Build comprehensive feedback message for refinement."""
        feedback = [f"Fix the following issues to meet spec: {feature_spec}"]
        feedback.append("")
        
        # Test failures
        if failures:
            feedback.append("**Test Failures:**")
            for i, fail in enumerate(failures[:5], 1):
                feedback.append(f"{i}. {fail['test']}")
                feedback.append(f"   Error type: {fail['type']}")
                feedback.append(f"   Message: {fail['message'][:150]}")
            
            if len(failures) > 5:
                feedback.append(f"   ... and {len(failures) - 5} more failures")
            feedback.append("")
        
        # Patterns
        if 'multiple_assertion_failures' in patterns:
            feedback.append("- Multiple assertion failures detected. Review logic carefully.")
        if 'unhandled_exceptions' in patterns:
            feedback.append("- Add proper error handling for exceptions.")
        if 'missing_imports' in patterns:
            feedback.append("- Add missing import statements.")
        if 'critical_static_issues' in patterns:
            feedback.append("- Fix critical static analysis issues.")
        
        # Static analysis details
        if static.get('issues'):
            feedback.append("")
            feedback.append("**Static Analysis Issues:**")
            for issue in static['issues'][:3]:
                msg = issue.get('message', 'Unknown issue')
                line = issue.get('line', '?')
                feedback.append(f"- Line {line}: {msg[:100]}")
        
        feedback.append("")
        feedback.append("Generate corrected code that passes all tests.")
        
        return "\n".join(feedback)
    
    def get_refinement_history(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get refinement history for a proposal."""
        # Query from database
        cursor = self.proposal_db.conn.cursor()
        cursor.execute("""
            SELECT refined_at, feedback, explanation
            FROM code_refinements
            WHERE proposal_id = ?
            ORDER BY refined_at DESC
        """, (proposal_id,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'refined_at': row[0],
                'feedback': row[1],
                'explanation': row[2]
            })
        
        return history
    
    def suggest_improvements(
        self,
        proposal_id: str
    ) -> Dict[str, Any]:
        """
        Suggest improvements even if tests pass.
        
        Analyzes coverage gaps, code complexity, style issues.
        """
        proposal = self.proposal_db.get_proposal(proposal_id)
        if not proposal:
            return {'success': False, 'error': 'Proposal not found'}
        
        execution = self.proposal_db.get_latest_execution(proposal_id)
        if not execution:
            return {'success': False, 'error': 'No test results found'}
        
        suggestions = []
        
        # Coverage analysis
        coverage = execution.get('coverage_percent', 0)
        if coverage < 90:
            suggestions.append({
                'type': 'coverage',
                'priority': 'medium',
                'message': f"Coverage is {coverage:.1f}%. Consider adding tests for edge cases."
            })
        
        # Static analysis
        static_score = execution.get('static_analysis_score')
        if static_score and static_score < 9.0:
            suggestions.append({
                'type': 'code_quality',
                'priority': 'low',
                'message': f"Static analysis score is {static_score:.1f}/10. Consider refactoring."
            })
        
        # Parse execution data for missing lines
        try:
            exec_data = json.loads(execution['execution_data'])
            missing_lines = exec_data.get('coverage_missing', [])
            if missing_lines:
                suggestions.append({
                    'type': 'coverage_gaps',
                    'priority': 'medium',
                    'message': f"Lines not covered: {', '.join(map(str, missing_lines[:10]))}"
                })
        except Exception:
            pass
        
        return {
            'success': True,
            'proposal_id': proposal_id,
            'suggestion_count': len(suggestions),
            'suggestions': suggestions
        }
