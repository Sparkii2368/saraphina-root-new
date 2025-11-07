"""
Autonomous System Components
Multi-agent review, self-healing, production feedback loop, advanced fuzzing
"""
import time
import json
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import ast
import traceback


# ============ Multi-Agent Code Review ============

class ReviewVerdict(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    NEEDS_REVISION = "needs_revision"


@dataclass
class ReviewResult:
    """Result from code review agent"""
    agent_name: str
    verdict: ReviewVerdict
    confidence: float
    issues: List[str]
    suggestions: List[str]
    severity_scores: Dict[str, float]  # issue_type -> severity (0-1)


class SecurityReviewer:
    """Security-focused code review agent"""
    
    def review(self, code: str) -> ReviewResult:
        """Review code for security issues"""
        issues = []
        suggestions = []
        severity_scores = {}
        
        # Check for common security issues
        if "eval(" in code or "exec(" in code:
            issues.append("Dangerous use of eval/exec")
            severity_scores["code_injection"] = 1.0
        
        if "pickle.loads" in code:
            issues.append("Unsafe deserialization with pickle")
            severity_scores["deserialization"] = 0.8
        
        if "input(" in code and "int(" not in code:
            issues.append("Unvalidated user input")
            severity_scores["input_validation"] = 0.6
        
        if "subprocess" in code and "shell=True" in code:
            issues.append("Shell injection risk in subprocess")
            severity_scores["shell_injection"] = 0.9
        
        if "password" in code.lower() and "=" in code:
            issues.append("Potential hardcoded credential")
            severity_scores["hardcoded_secret"] = 0.7
        
        # Suggestions
        if "try:" in code and "except:" in code and "pass" in code:
            suggestions.append("Avoid bare except with pass - log errors")
        
        # Verdict
        critical_issues = [s for s in severity_scores.values() if s >= 0.8]
        if critical_issues:
            verdict = ReviewVerdict.REJECT
            confidence = 0.9
        elif issues:
            verdict = ReviewVerdict.NEEDS_REVISION
            confidence = 0.7
        else:
            verdict = ReviewVerdict.APPROVE
            confidence = 0.8
        
        return ReviewResult(
            agent_name="SecurityReviewer",
            verdict=verdict,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            severity_scores=severity_scores
        )


class PerformanceReviewer:
    """Performance-focused code review agent"""
    
    def review(self, code: str) -> ReviewResult:
        """Review code for performance issues"""
        issues = []
        suggestions = []
        severity_scores = {}
        
        # Check for performance anti-patterns
        if "for" in code and "append(" in code and "[]" in code:
            # List comprehension opportunity
            suggestions.append("Consider list comprehension for better performance")
        
        if code.count("for") > 2:
            # Nested loops
            issues.append("Multiple nested loops detected - O(n²) or worse complexity")
            severity_scores["complexity"] = 0.6
        
        if ".split()" in code and code.count(".split()") > 1:
            suggestions.append("Cache .split() result if used multiple times")
        
        # Check for inefficient patterns
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if '+=' in line and 'str' in line.lower():
                issues.append(f"String concatenation in loop (line {i}) - use join()")
                severity_scores["string_concat"] = 0.4
        
        # Analyze complexity
        try:
            tree = ast.parse(code)
            complexity = self._calculate_complexity(tree)
            if complexity > 10:
                issues.append(f"High cyclomatic complexity: {complexity}")
                severity_scores["complexity"] = min(complexity / 20.0, 1.0)
        except:
            pass
        
        # Verdict
        if any(s > 0.7 for s in severity_scores.values()):
            verdict = ReviewVerdict.NEEDS_REVISION
            confidence = 0.8
        elif issues:
            verdict = ReviewVerdict.NEEDS_REVISION
            confidence = 0.6
        else:
            verdict = ReviewVerdict.APPROVE
            confidence = 0.75
        
        return ReviewResult(
            agent_name="PerformanceReviewer",
            verdict=verdict,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            severity_scores=severity_scores
        )
    
    def _calculate_complexity(self, tree) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity


class ArchitectureReviewer:
    """Architecture and design review agent"""
    
    def review(self, code: str) -> ReviewResult:
        """Review code for architecture issues"""
        issues = []
        suggestions = []
        severity_scores = {}
        
        # Check for design issues
        if "class" in code:
            if "__init__" not in code:
                suggestions.append("Class missing __init__ constructor")
            
            if code.count("def ") > 10:
                issues.append("Large class (>10 methods) - consider splitting")
                severity_scores["god_class"] = 0.5
        
        # Check for function size
        functions = code.split("def ")
        for func in functions[1:]:
            lines = func.split('\n')
            if len(lines) > 50:
                issues.append("Function >50 lines - consider refactoring")
                severity_scores["long_function"] = 0.4
        
        # Check for SRP violations
        if "and" in code.lower() or "or" in code.lower():
            # Function does multiple things
            pass  # Would need deeper analysis
        
        # Check for proper abstraction
        if code.count("if") > 5:
            suggestions.append("Multiple conditionals - consider strategy pattern")
        
        # Verdict
        if any(s > 0.6 for s in severity_scores.values()):
            verdict = ReviewVerdict.NEEDS_REVISION
            confidence = 0.7
        elif suggestions:
            verdict = ReviewVerdict.APPROVE
            confidence = 0.65
        else:
            verdict = ReviewVerdict.APPROVE
            confidence = 0.8
        
        return ReviewResult(
            agent_name="ArchitectureReviewer",
            verdict=verdict,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            severity_scores=severity_scores
        )


class MultiAgentReviewSystem:
    """Coordinates multiple review agents"""
    
    def __init__(self):
        self.agents = [
            SecurityReviewer(),
            PerformanceReviewer(),
            ArchitectureReviewer()
        ]
    
    def review_code(self, code: str) -> Tuple[bool, List[ReviewResult]]:
        """
        Multi-agent code review with consensus voting
        
        Returns:
            (approved, reviews)
        """
        reviews = []
        
        for agent in self.agents:
            review = agent.review(code)
            reviews.append(review)
        
        # Consensus voting
        approvals = sum(1 for r in reviews if r.verdict == ReviewVerdict.APPROVE)
        rejections = sum(1 for r in reviews if r.verdict == ReviewVerdict.REJECT)
        
        # Require majority approval and no rejections
        approved = approvals >= 2 and rejections == 0
        
        return approved, reviews


# ============ Production Feedback Loop ============

@dataclass
class DeploymentOutcome:
    """Track outcomes of deployed code"""
    artifact_id: str
    deployed_at: float
    error_count: int = 0
    execution_count: int = 0
    avg_latency_ms: float = 0.0
    errors: List[Dict] = field(default_factory=list)


class ProductionFeedbackLoop:
    """Learn from production deployments"""
    
    def __init__(self):
        self.outcomes: Dict[str, DeploymentOutcome] = {}
        self.error_patterns: Dict[str, int] = defaultdict(int)
        self.improvement_suggestions: List[Dict] = []
    
    def track_deployment(self, artifact_id: str):
        """Start tracking deployment"""
        self.outcomes[artifact_id] = DeploymentOutcome(
            artifact_id=artifact_id,
            deployed_at=time.time()
        )
    
    def log_execution(self, artifact_id: str, success: bool, latency_ms: float, 
                     error: Optional[Dict] = None):
        """Log execution result"""
        if artifact_id not in self.outcomes:
            return
        
        outcome = self.outcomes[artifact_id]
        outcome.execution_count += 1
        
        if not success and error:
            outcome.error_count += 1
            outcome.errors.append(error)
            
            # Track error pattern
            error_type = error.get("type", "unknown")
            self.error_patterns[error_type] += 1
        
        # Update latency (running average)
        outcome.avg_latency_ms = (
            (outcome.avg_latency_ms * (outcome.execution_count - 1) + latency_ms) 
            / outcome.execution_count
        )
    
    def analyze_failures(self, artifact_id: str) -> Optional[Dict]:
        """Analyze failure patterns and suggest fixes"""
        if artifact_id not in self.outcomes:
            return None
        
        outcome = self.outcomes[artifact_id]
        if outcome.error_count == 0:
            return None
        
        # Analyze error patterns
        error_types = defaultdict(int)
        error_messages = []
        
        for error in outcome.errors:
            error_types[error.get("type", "unknown")] += 1
            error_messages.append(error.get("message", ""))
        
        # Find most common error
        most_common = max(error_types.items(), key=lambda x: x[1])
        
        # Generate suggestion
        suggestion = {
            "artifact_id": artifact_id,
            "error_rate": outcome.error_count / outcome.execution_count,
            "most_common_error": most_common[0],
            "occurrences": most_common[1],
            "suggested_fix": self._suggest_fix(most_common[0], error_messages),
            "priority": "high" if outcome.error_count / outcome.execution_count > 0.1 else "medium"
        }
        
        self.improvement_suggestions.append(suggestion)
        return suggestion
    
    def _suggest_fix(self, error_type: str, messages: List[str]) -> str:
        """Suggest fix based on error pattern"""
        if "KeyError" in error_type:
            return "Add .get() with default value or validate keys exist"
        elif "TypeError" in error_type:
            return "Add type validation and coercion"
        elif "ValueError" in error_type:
            return "Add input validation and range checking"
        elif "AttributeError" in error_type:
            return "Check object type before accessing attributes"
        elif "IndexError" in error_type:
            return "Add bounds checking for list/array access"
        else:
            return "Add comprehensive error handling and logging"
    
    def get_metrics_summary(self) -> Dict:
        """Get aggregate metrics"""
        if not self.outcomes:
            return {}
        
        total_executions = sum(o.execution_count for o in self.outcomes.values())
        total_errors = sum(o.error_count for o in self.outcomes.values())
        avg_latency = sum(o.avg_latency_ms for o in self.outcomes.values()) / len(self.outcomes)
        
        return {
            "total_artifacts": len(self.outcomes),
            "total_executions": total_executions,
            "total_errors": total_errors,
            "overall_error_rate": total_errors / total_executions if total_executions > 0 else 0,
            "avg_latency_ms": avg_latency,
            "top_error_patterns": sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:5],
            "pending_improvements": len(self.improvement_suggestions)
        }


# ============ Self-Healing System ============

class SelfHealingSystem:
    """Automatically detect and fix production issues"""
    
    def __init__(self, feedback_loop: ProductionFeedbackLoop, code_generator):
        self.feedback_loop = feedback_loop
        self.code_generator = code_generator
        self.healing_attempts: List[Dict] = []
    
    def detect_and_heal(self, artifact_id: str) -> Optional[str]:
        """Detect issues and generate fix"""
        # Analyze failures
        analysis = self.feedback_loop.analyze_failures(artifact_id)
        if not analysis:
            return None
        
        # Only auto-heal if error rate is concerning
        if analysis["error_rate"] < 0.05:  # <5% error rate
            return None
        
        print(f"🔧 Self-healing triggered for {artifact_id}")
        print(f"   Error rate: {analysis['error_rate']:.1%}")
        print(f"   Most common: {analysis['most_common_error']}")
        
        # Generate fix (would use neural codegen in production)
        fix_spec = f"""Fix this error: {analysis['most_common_error']}
        
Suggested approach: {analysis['suggested_fix']}

Generate improved version with proper error handling."""
        
        # Log healing attempt
        self.healing_attempts.append({
            "artifact_id": artifact_id,
            "timestamp": time.time(),
            "error_type": analysis["most_common_error"],
            "fix_spec": fix_spec
        })
        
        return fix_spec
    
    def canary_deploy(self, artifact_id: str, percentage: float = 10.0) -> Dict:
        """Deploy to small percentage of traffic"""
        return {
            "artifact_id": artifact_id,
            "canary_percentage": percentage,
            "status": "monitoring",
            "started_at": time.time()
        }


# ============ Advanced Fuzzing ============

class PropertyBasedFuzzer:
    """Property-based testing and fuzzing"""
    
    def __init__(self):
        self.test_cases_generated = 0
        self.crashes_found = []
    
    def fuzz_function(self, func, iterations: int = 1000) -> Dict:
        """Fuzz test a function"""
        results = {
            "iterations": iterations,
            "passed": 0,
            "failed": 0,
            "crashes": [],
            "edge_cases_found": []
        }
        
        for i in range(iterations):
            # Generate random input
            test_input = self._generate_random_input()
            
            try:
                result = func(test_input)
                results["passed"] += 1
                
                # Check properties
                if not self._check_properties(test_input, result):
                    results["edge_cases_found"].append({
                        "input": test_input,
                        "output": result
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["crashes"].append({
                    "input": test_input,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        self.test_cases_generated += iterations
        self.crashes_found.extend(results["crashes"])
        
        return results
    
    def _generate_random_input(self):
        """Generate random test input"""
        input_types = [
            None,
            "",
            " ",
            "test",
            "a" * 10000,  # Large string
            0,
            -1,
            999999999,
            [],
            [1, 2, 3],
            {},
            {"key": "value"}
        ]
        return random.choice(input_types)
    
    def _check_properties(self, input_val, output_val) -> bool:
        """Check invariant properties"""
        # Example properties
        if output_val is None and input_val is not None:
            return False  # Should not return None for non-None input
        
        return True


# Global instances
_multi_agent_review = None
_feedback_loop = None
_self_healing = None

def get_multi_agent_review() -> MultiAgentReviewSystem:
    global _multi_agent_review
    if _multi_agent_review is None:
        _multi_agent_review = MultiAgentReviewSystem()
    return _multi_agent_review

def get_feedback_loop() -> ProductionFeedbackLoop:
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = ProductionFeedbackLoop()
    return _feedback_loop

def get_self_healing(code_generator) -> SelfHealingSystem:
    global _self_healing
    if _self_healing is None:
        _self_healing = SelfHealingSystem(get_feedback_loop(), code_generator)
    return _self_healing
