"""
Neural Code Generation
LLM-powered code synthesis using GPT-4, Codex, or local models.
"""
import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import secrets
import time

# Multi-provider support
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class CodeGenerationRequest:
    """Request for code generation"""
    specification: str
    code_type: str  # function, class, module
    language: str = "python"
    style_guide: str = "pep8"
    include_tests: bool = True
    include_docs: bool = True
    include_type_hints: bool = True
    max_complexity: int = 10
    context: Optional[str] = None  # Existing codebase context


@dataclass
class GeneratedCode:
    """Generated code artifact"""
    code: str
    tests: str
    documentation: str
    metadata: Dict
    confidence: float


class PromptEngineer:
    """Crafts optimized prompts for code generation"""
    
    @staticmethod
    def build_system_prompt() -> str:
        """System prompt for code generation"""
        return """You are an expert software engineer specializing in Python development.

You write:
- Clean, idiomatic Python code following PEP 8
- Comprehensive docstrings with examples
- Type hints for all functions and methods
- Proper error handling
- Efficient algorithms with O(n) complexity analysis
- Security-conscious code (input validation, no SQL injection, etc.)

You avoid:
- Magic numbers (use named constants)
- Deep nesting (max 3 levels)
- Functions longer than 50 lines
- Unclear variable names
- Missing edge case handling"""
    
    @staticmethod
    def build_code_prompt(request: CodeGenerationRequest) -> str:
        """Build prompt for code generation"""
        prompt_parts = [
            f"Generate a Python {request.code_type} for the following specification:",
            f"\n{request.specification}\n",
            "\nRequirements:"
        ]
        
        if request.include_type_hints:
            prompt_parts.append("- Include type hints for all parameters and return values")
        
        if request.include_docs:
            prompt_parts.append("- Include comprehensive docstrings with usage examples")
        
        prompt_parts.append(f"- Follow {request.style_guide} style guide")
        prompt_parts.append(f"- Maximum cyclomatic complexity: {request.max_complexity}")
        prompt_parts.append("- Include input validation and error handling")
        
        if request.context:
            prompt_parts.append(f"\nExisting codebase context:\n{request.context}")
        
        prompt_parts.append("\nProvide ONLY the code, no explanations.")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def build_test_prompt(code: str, spec: str) -> str:
        """Build prompt for test generation"""
        return f"""Generate comprehensive pytest tests for the following code:

```python
{code}
```

Original specification: {spec}

Requirements:
- Use pytest framework
- Test happy path
- Test edge cases (empty input, None, boundary values)
- Test error conditions
- Aim for >90% code coverage
- Include parametrized tests where applicable
- Add descriptive test names

Provide ONLY the test code, no explanations."""


class NeuralCodeGenerator:
    """Main neural code generator using LLMs"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4"):
        """
        Initialize generator
        
        Args:
            provider: "openai", "anthropic", or "local"
            model: Model name (e.g., "gpt-4", "claude-3-opus")
        """
        self.provider = provider
        self.model = model
        self.prompt_engineer = PromptEngineer()
        
        # Configure API
        if provider == "openai" and OPENAI_AVAILABLE:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                print("Warning: OPENAI_API_KEY not set")
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
    
    def generate_code(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Generate code from specification"""
        
        # Generate main code
        code = self._generate_implementation(request)
        
        # Generate tests
        tests = ""
        if request.include_tests:
            tests = self._generate_tests(code, request.specification)
        
        # Generate documentation
        docs = self._extract_documentation(code)
        
        # Calculate confidence
        confidence = self._estimate_confidence(code, request)
        
        return GeneratedCode(
            code=code,
            tests=tests,
            documentation=docs,
            metadata={
                "provider": self.provider,
                "model": self.model,
                "specification": request.specification,
                "generated_at": time.time()
            },
            confidence=confidence
        )
    
    def _generate_implementation(self, request: CodeGenerationRequest) -> str:
        """Generate code implementation"""
        
        system_prompt = self.prompt_engineer.build_system_prompt()
        user_prompt = self.prompt_engineer.build_code_prompt(request)
        
        if self.provider == "openai" and OPENAI_AVAILABLE:
            return self._generate_openai(system_prompt, user_prompt)
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            # Fallback to template-based generation
            return self._generate_template_fallback(request)
    
    def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using OpenAI API"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower temperature for more deterministic code
                max_tokens=2000
            )
            
            code = response.choices[0].message.content
            return self._extract_code_block(code)
            
        except Exception as e:
            print(f"OpenAI generation error: {e}")
            return "# Error generating code"
    
    def _generate_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Anthropic Claude"""
        try:
            message = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            code = message.content[0].text
            return self._extract_code_block(code)
            
        except Exception as e:
            print(f"Anthropic generation error: {e}")
            return "# Error generating code"
    
    def _generate_template_fallback(self, request: CodeGenerationRequest) -> str:
        """Fallback to template-based generation"""
        spec_lower = request.specification.lower()
        
        if "calculate" in spec_lower or "compute" in spec_lower:
            return '''def calculate_value(input_value: float) -> float:
    """
    Calculate result from input value.
    
    Args:
        input_value: Input value to process
        
    Returns:
        Calculated result
        
    Raises:
        ValueError: If input is invalid
    """
    if input_value < 0:
        raise ValueError("Input must be non-negative")
    
    return input_value * 2.0
'''
        elif "validate" in spec_lower:
            return '''def validate_input(data: str) -> bool:
    """
    Validate input data.
    
    Args:
        data: Data to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not data:
        return False
    
    return len(data) > 0 and data.isalnum()
'''
        else:
            return f'''def process_data(input_data):
    """
    {request.specification}
    
    Args:
        input_data: Input data to process
        
    Returns:
        Processed result
    """
    # TODO: Implement functionality
    return input_data
'''
    
    def _generate_tests(self, code: str, spec: str) -> str:
        """Generate tests for code"""
        test_prompt = self.prompt_engineer.build_test_prompt(code, spec)
        
        if self.provider == "openai" and OPENAI_AVAILABLE:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at writing pytest tests."},
                        {"role": "user", "content": test_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                tests = response.choices[0].message.content
                return self._extract_code_block(tests)
                
            except Exception as e:
                print(f"Test generation error: {e}")
        
        # Fallback: basic test template
        return f'''import pytest

def test_basic_functionality():
    """Test basic functionality"""
    # TODO: Add specific tests
    pass

def test_edge_cases():
    """Test edge cases"""
    # TODO: Test None, empty, boundary values
    pass

def test_error_handling():
    """Test error conditions"""
    # TODO: Test invalid inputs
    pass
'''
    
    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code blocks"""
        lines = text.split('\n')
        in_code_block = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    break
                in_code_block = True
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
        
        # No code block found, return as-is
        return text
    
    def _extract_documentation(self, code: str) -> str:
        """Extract documentation from code"""
        # Extract module docstring and function docstrings
        docs = []
        in_docstring = False
        current_doc = []
        
        for line in code.split('\n'):
            stripped = line.strip()
            
            if '"""' in stripped or "'''" in stripped:
                if in_docstring:
                    docs.append(' '.join(current_doc))
                    current_doc = []
                    in_docstring = False
                else:
                    in_docstring = True
                continue
            
            if in_docstring:
                current_doc.append(stripped)
        
        return '\n\n'.join(docs)
    
    def _estimate_confidence(self, code: str, request: CodeGenerationRequest) -> float:
        """Estimate confidence in generated code"""
        confidence = 1.0
        
        # Deduct for missing elements
        if request.include_type_hints and ':' not in code:
            confidence -= 0.2
        
        if request.include_docs and '"""' not in code:
            confidence -= 0.2
        
        # Deduct for very short code (likely incomplete)
        if len(code.split('\n')) < 5:
            confidence -= 0.3
        
        # Deduct for TODOs
        if 'TODO' in code or 'pass' in code:
            confidence -= 0.1
        
        return max(confidence, 0.0)
    
    def improve_code(self, code: str, feedback: str) -> str:
        """Improve code based on feedback"""
        
        prompt = f"""Improve the following code based on this feedback:

Feedback: {feedback}

Original code:
```python
{code}
```

Provide the improved version addressing the feedback. Maintain all existing functionality."""

        if self.provider == "openai" and OPENAI_AVAILABLE:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt_engineer.build_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                
                return self._extract_code_block(response.choices[0].message.content)
            except Exception as e:
                print(f"Code improvement error: {e}")
        
        return code  # Return original if improvement fails
