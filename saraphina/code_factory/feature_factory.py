"""
FeatureFactory: AI-powered code generation with testing and static analysis.
Generates code proposals from feature specifications.
"""
import ast
import subprocess
import tempfile
import secrets
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import json

from .code_artifacts import (
    CodeArtifact, CodeArtifactDB, ArtifactType, ArtifactStatus, compute_signature
)


class CodeTemplate:
    """Template-based code generation"""
    
    @staticmethod
    def generate_function(func_name: str, params: List[str], docstring: str, 
                         return_type: str = "Any") -> str:
        """Generate function template"""
        params_str = ", ".join(params)
        
        return f'''def {func_name}({params_str}) -> {return_type}:
    """
    {docstring}
    """
    # TODO: Implement function logic
    pass
'''
    
    @staticmethod
    def generate_class(class_name: str, methods: List[Dict], docstring: str) -> str:
        """Generate class template"""
        methods_code = []
        
        for method in methods:
            method_name = method.get("name", "method")
            params = method.get("params", ["self"])
            method_doc = method.get("docstring", "Method description")
            
            params_str = ", ".join(params)
            methods_code.append(f'''
    def {method_name}({params_str}):
        """
        {method_doc}
        """
        pass
''')
        
        return f'''class {class_name}:
    """
    {docstring}
    """
    
    def __init__(self):
        """Initialize {class_name}"""
        pass
{''.join(methods_code)}
'''
    
    @staticmethod
    def generate_helper_function(purpose: str) -> str:
        """Generate simple helper function based on purpose"""
        if "calculate" in purpose.lower():
            return '''def calculate_result(value_a: float, value_b: float) -> float:
    """Calculate result from two values"""
    return value_a + value_b
'''
        elif "validate" in purpose.lower():
            return '''def validate_input(data: str) -> bool:
    """Validate input data"""
    return len(data) > 0 and data.isalnum()
'''
        elif "format" in purpose.lower():
            return '''def format_output(data: dict) -> str:
    """Format data as string"""
    return json.dumps(data, indent=2)
'''
        else:
            return '''def process_data(input_data):
    """Process input data and return result"""
    # TODO: Implement processing logic
    return input_data
'''


class TestGenerator:
    """Automatic test generation"""
    
    @staticmethod
    def generate_tests(code: str, artifact_type: ArtifactType) -> str:
        """Generate pytest tests for code"""
        # Parse code to extract functions/classes
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "# Could not parse code for test generation\n"
        
        tests = ["import pytest\n\n"]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                test_code = TestGenerator._generate_function_test(node)
                tests.append(test_code)
            elif isinstance(node, ast.ClassDef):
                test_code = TestGenerator._generate_class_test(node)
                tests.append(test_code)
        
        return "".join(tests)
    
    @staticmethod
    def _generate_function_test(func_node: ast.FunctionDef) -> str:
        """Generate test for function"""
        func_name = func_node.name
        test_name = f"test_{func_name}"
        
        return f'''
def {test_name}():
    """Test {func_name} function"""
    # Test basic functionality
    result = {func_name}()
    assert result is not None
    
    # Test with sample inputs
    # TODO: Add specific test cases
    pass

def {test_name}_edge_cases():
    """Test {func_name} edge cases"""
    # Test None input
    # Test empty input
    # Test boundary conditions
    pass

'''
    
    @staticmethod
    def _generate_class_test(class_node: ast.ClassDef) -> str:
        """Generate test for class"""
        class_name = class_node.name
        test_name = f"test_{class_name.lower()}"
        
        return f'''
class Test{class_name}:
    """Tests for {class_name} class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.instance = {class_name}()
    
    def {test_name}_initialization(self):
        """Test {class_name} initialization"""
        assert self.instance is not None
    
    def {test_name}_methods(self):
        """Test {class_name} methods"""
        # TODO: Add method tests
        pass

'''


class StaticAnalyzer:
    """Static code analysis"""
    
    @staticmethod
    def analyze(code: str, tests: str) -> Dict:
        """Run static analysis tools"""
        results = {
            "syntax_valid": False,
            "flake8": {},
            "bandit": {},
            "mypy": {},
            "complexity": {},
            "overall_score": 0.0
        }
        
        # Check syntax
        try:
            ast.parse(code)
            results["syntax_valid"] = True
        except SyntaxError as e:
            results["syntax_valid"] = False
            results["syntax_error"] = str(e)
            return results
        
        # Write code to temp file for analysis
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Flake8 - style and quality
            results["flake8"] = StaticAnalyzer._run_flake8(temp_file)
            
            # Bandit - security
            results["bandit"] = StaticAnalyzer._run_bandit(temp_file)
            
            # Complexity analysis
            results["complexity"] = StaticAnalyzer._analyze_complexity(code)
            
            # Calculate overall score
            results["overall_score"] = StaticAnalyzer._calculate_score(results)
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
        
        return results
    
    @staticmethod
    def _run_flake8(filepath: str) -> Dict:
        """Run flake8 style checker"""
        try:
            result = subprocess.run(
                ['flake8', '--max-line-length=120', filepath],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "passed": result.returncode == 0,
                "issues": result.stdout.strip().split('\n') if result.stdout else [],
                "count": len(result.stdout.strip().split('\n')) if result.stdout else 0
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"passed": None, "error": "flake8 not available"}
    
    @staticmethod
    def _run_bandit(filepath: str) -> Dict:
        """Run bandit security scanner"""
        try:
            result = subprocess.run(
                ['bandit', '-f', 'json', filepath],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    "passed": len(data.get("results", [])) == 0,
                    "issues": data.get("results", []),
                    "severity_high": sum(1 for r in data.get("results", []) if r.get("issue_severity") == "HIGH")
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return {"passed": None, "error": "bandit not available"}
        
        return {"passed": True, "issues": []}
    
    @staticmethod
    def _analyze_complexity(code: str) -> Dict:
        """Analyze cyclomatic complexity"""
        try:
            tree = ast.parse(code)
            complexity_scores = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = StaticAnalyzer._calculate_complexity(node)
                    complexity_scores.append({
                        "function": node.name,
                        "complexity": complexity
                    })
            
            max_complexity = max([c["complexity"] for c in complexity_scores], default=0)
            avg_complexity = sum([c["complexity"] for c in complexity_scores]) / len(complexity_scores) if complexity_scores else 0
            
            return {
                "functions": complexity_scores,
                "max_complexity": max_complexity,
                "avg_complexity": avg_complexity,
                "acceptable": max_complexity <= 10  # McCabe threshold
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def _calculate_complexity(node) -> int:
        """Calculate McCabe cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    @staticmethod
    def _calculate_score(results: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0
        
        # Syntax errors = 0
        if not results["syntax_valid"]:
            return 0.0
        
        # Deduct for flake8 issues
        flake8 = results.get("flake8", {})
        if flake8.get("passed") == False:
            score -= min(flake8.get("count", 0) * 2, 30)
        
        # Deduct for security issues
        bandit = results.get("bandit", {})
        if bandit.get("passed") == False:
            score -= bandit.get("severity_high", 0) * 15
        
        # Deduct for high complexity
        complexity = results.get("complexity", {})
        if not complexity.get("acceptable", True):
            score -= 20
        
        return max(score, 0.0)


class FeatureFactory:
    """Main code generation factory"""
    
    def __init__(self, artifact_db: CodeArtifactDB):
        self.artifact_db = artifact_db
        self.templates = CodeTemplate()
        self.test_gen = TestGenerator()
        self.analyzer = StaticAnalyzer()
    
    def propose_code(self, feature_spec: str, artifact_type: ArtifactType = ArtifactType.FUNCTION) -> Tuple[str, Dict]:
        """
        Generate code proposal from feature specification.
        
        Returns:
            (artifact_id, report) where report contains code, tests, and analysis
        """
        # Generate code based on feature spec
        code = self._generate_code_from_spec(feature_spec, artifact_type)
        
        # Generate tests
        tests = self.test_gen.generate_tests(code, artifact_type)
        
        # Run static analysis
        static_analysis = self.analyzer.analyze(code, tests)
        
        # Compute signature
        signature = compute_signature(code, tests)
        
        # Create artifact
        artifact_id = f"artifact-{secrets.token_hex(8)}"
        
        artifact = CodeArtifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            code=code,
            tests=tests,
            feature_spec=feature_spec,
            author="saraphina-ai",
            provenance={
                "method": "template_generation",
                "version": "1.0",
                "timestamp": time.time()
            },
            signature=signature,
            status=ArtifactStatus.PROPOSED,
            static_analysis=static_analysis
        )
        
        # Store in database
        self.artifact_db.create_artifact(artifact)
        
        # Generate report
        report = {
            "artifact_id": artifact_id,
            "code": code,
            "tests": tests,
            "static_analysis": static_analysis,
            "signature": signature,
            "quality_score": static_analysis.get("overall_score", 0),
            "recommendation": self._get_recommendation(static_analysis)
        }
        
        return artifact_id, report
    
    def _generate_code_from_spec(self, spec: str, artifact_type: ArtifactType) -> str:
        """Generate code from natural language specification"""
        spec_lower = spec.lower()
        
        # Simple keyword-based generation
        if artifact_type == ArtifactType.FUNCTION:
            if "calculate" in spec_lower or "compute" in spec_lower:
                return self.templates.generate_function(
                    "calculate_value",
                    ["input_value: float"],
                    spec,
                    "float"
                )
            elif "validate" in spec_lower or "check" in spec_lower:
                return self.templates.generate_function(
                    "validate_data",
                    ["data: str"],
                    spec,
                    "bool"
                )
            else:
                return self.templates.generate_helper_function(spec)
        
        elif artifact_type == ArtifactType.CLASS:
            class_name = "CustomClass"
            # Extract class name from spec if possible
            if "class" in spec_lower:
                words = spec.split()
                for i, word in enumerate(words):
                    if word.lower() == "class" and i + 1 < len(words):
                        class_name = words[i + 1].strip(',:.')
                        break
            
            return self.templates.generate_class(
                class_name,
                [{"name": "process", "params": ["self", "data"], "docstring": "Process data"}],
                spec
            )
        
        else:
            return self.templates.generate_helper_function(spec)
    
    def _get_recommendation(self, static_analysis: Dict) -> str:
        """Get human-readable recommendation"""
        score = static_analysis.get("overall_score", 0)
        
        if score >= 90:
            return "✅ Excellent quality - ready for sandbox testing"
        elif score >= 75:
            return "✓ Good quality - minor issues, safe to test"
        elif score >= 50:
            return "⚠️  Acceptable - has issues, review before testing"
        else:
            return "❌ Poor quality - needs significant improvements"


import time
