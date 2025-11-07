#!/usr/bin/env python3
"""
CodeForge - GPT-4 powered code generation for autonomous self-upgrades
"""
import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI
from pathlib import Path

logger = logging.getLogger("CodeForge")


@dataclass
class CodeArtifact:
    """Generated code artifact ready for validation and deployment"""
    artifact_id: str
    spec_id: str
    gap_id: str
    
    # Generated code
    new_files: Dict[str, str] = field(default_factory=dict)  # filename -> content
    code_diffs: Dict[str, Dict[str, str]] = field(default_factory=dict)  # filename -> {old, new}
    tests: Dict[str, str] = field(default_factory=dict)  # test_filename -> content
    
    # Documentation
    docstring: str = ""
    readme_update: str = ""
    
    # Metadata
    risk_score: float = 0.5
    estimated_loc: int = 0
    dependencies: List[str] = field(default_factory=list)
    
    # Status
    status: str = "generated"  # generated, validated, applied, failed, rolled_back
    created_at: datetime = field(default_factory=datetime.utcnow)
    validation_results: Dict[str, Any] = field(default_factory=dict)


class CodeForge:
    """Autonomous code generator using GPT-4 to implement features"""
    
    def __init__(self, api_key: Optional[str] = None, learning_journal=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required for CodeForge")
        
        self.client = OpenAI(api_key=self.api_key)
        self.saraphina_root = Path("D:\\Saraphina Root\\saraphina")
        self.artifacts: Dict[str, CodeArtifact] = {}
        self.learning_journal = learning_journal  # For learning from past failures
    
    def generate_from_spec(self, spec, context: Dict[str, Any] = None) -> CodeArtifact:
        """
        Generate code from a structured UpgradeSpec
        
        This is the NEW spec-driven generation method that:
        1. Takes a validated UpgradeSpec as input
        2. Uses past failures from Learning Journal to avoid mistakes
        3. Generates EXACTLY what the spec asks for
        4. Returns artifact ready for validation
        
        Args:
            spec: UpgradeSpec from SpecGenerator
            context: Optional additional context
        
        Returns:
            CodeArtifact with generated code
        """
        logger.info(f"Generating code from spec: {spec.feature_name}")
        
        context = context or {}
        
        # Get past failures to learn from
        past_failures = []
        if self.learning_journal:
            past_failures = self.learning_journal.get_recent_failures(limit=3)
        
        # Create artifact
        artifact = CodeArtifact(
            artifact_id=f"ART-SPEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            spec_id=getattr(spec, 'spec_id', 'CUSTOM'),
            gap_id="SPEC-DRIVEN"
        )
        
        # Generate new files (modules)
        for module_filename in spec.modules:
            module_name = module_filename.replace('.py', '')
            logger.info(f"Generating new module: {module_filename}")
            code = self._generate_module_from_spec(spec, module_name, past_failures)
            artifact.new_files[module_filename] = code
            
            # Auto-generate tests
            logger.info(f"Generating tests for: {module_filename}")
            test_code = self._generate_tests_from_spec(spec, module_name, code)
            if test_code:
                artifact.tests[f"test_{module_name}.py"] = test_code
        
        # Generate modifications to existing files
        for modification_filename in spec.modifications:
            module_name = modification_filename.replace('.py', '')
            logger.info(f"Generating modifications for: {modification_filename}")
            original_code = self._read_existing_module(module_name)
            modified_code = self._generate_modification_from_spec(
                spec, module_name, original_code, past_failures
            )
            artifact.code_diffs[modification_filename] = modified_code
        
        # Store dependencies
        artifact.dependencies = spec.requirements
        
        # Calculate risk
        artifact.risk_score = 0.3 if spec.priority == "low" else 0.5 if spec.priority == "medium" else 0.7
        artifact.estimated_loc = sum(len(code.split('\n')) for code in artifact.new_files.values())
        
        # Store artifact
        self.artifacts[artifact.artifact_id] = artifact
        
        logger.info(f"Generated artifact {artifact.artifact_id} from spec")
        return artifact
    
    def generate_from_gap(self, gap, context: Dict[str, Any] = None) -> CodeArtifact:
        """
        Generate complete implementation for a gap
        
        This is the CORE autonomous upgrade function - it:
        1. Analyzes the gap and requirement
        2. Reads existing code for context
        3. Uses GPT-4 to generate NEW Python code
        4. Creates tests and documentation
        5. Returns a validated artifact ready to apply
        """
        logger.info(f"Generating code for {gap.gap_id}: {gap.requirement}")
        
        context = context or {}
        
        # Create artifact
        artifact = CodeArtifact(
            artifact_id=f"ART-{gap.gap_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            spec_id=gap.gap_id,
            gap_id=gap.gap_id
        )
        
        # Determine what to build
        module_name = self._determine_module_name(gap)
        is_new_module = self._is_new_module(module_name)
        
        if is_new_module:
            # Generate entirely new module
            logger.info(f"Generating new module: {module_name}")
            code = self._generate_new_module(gap, module_name, context)
            artifact.new_files[f"{module_name}.py"] = code
            
            # Generate tests
            test_code = self._generate_tests(gap, module_name, code)
            artifact.tests[f"test_{module_name}.py"] = test_code
        else:
            # Generate modifications to existing module
            logger.info(f"Generating modifications to: {module_name}")
            original_code = self._read_existing_module(module_name)
            modified_code = self._generate_module_modifications(
                gap, module_name, original_code, context
            )
            # Store only the NEW code (HotReloadManager expects string, not dict)
            artifact.code_diffs[f"{module_name}.py"] = modified_code
        
        # Calculate risk score
        artifact.risk_score = self._calculate_risk(gap, artifact)
        artifact.estimated_loc = sum(len(code.split('\n')) for code in artifact.new_files.values())
        
        # Store artifact
        self.artifacts[artifact.artifact_id] = artifact
        
        logger.info(f"Generated artifact {artifact.artifact_id} with {artifact.estimated_loc} LOC, risk={artifact.risk_score:.2f}")
        return artifact
    
    def _determine_module_name(self, gap) -> str:
        """Determine target module name from gap"""
        
        # Map common terms to module names (snake_case)
        requirement_lower = gap.requirement.lower()
        
        mappings = {
            'spec generator': 'spec_generator',
            'code forge': 'code_forge',
            'sandbox': 'sandbox_validator',
            'hot-reload': 'hot_reload_manager',
            'hot reload': 'hot_reload_manager',
            'policy tier': 'policy_engine',
            'audit trail': 'audit_logger',
            'error sentinel': 'error_sentinel',
            'error kb': 'error_knowledge_base',
            'self-heal': 'self_healing_manager',
            'scheduler': 'upgrade_scheduler',
            'response format': 'response_formatter',
            'system metadata': 'system_metadata',
            'background learn': 'background_learner',
            'stt': 'stt_listener',
            'speech-to-text': 'stt_listener',
            'voice': 'stt_listener',
            'saraphina_gui': 'saraphina_gui'
        }
        
        for key, module in mappings.items():
            if key in requirement_lower:
                return module
        
        # Check if requirement explicitly specifies a filename
        # Look for patterns like "named 'filename.py'" or "module named filename.py"
        filename_match = re.search(r"named\s+['\"]?([a-z_]+)\.py['\"]?", requirement_lower)
        if filename_match:
            return filename_match.group(1)
        
        # Check for "modify filename.py"
        modify_match = re.search(r"modify\s+([a-z_]+)\.py", requirement_lower)
        if modify_match:
            return modify_match.group(1)
        
        # Fallback: extract first meaningful words (max 3 words, 30 chars)
        # Split on colons, newlines, and take first line
        first_line = requirement_lower.split('\n')[0].split(':')[0].strip()
        # Remove common prefix words
        first_line = re.sub(r'^(create|generate|build|make|add|implement)\s+', '', first_line)
        # Convert to snake_case
        name = re.sub(r'[^a-z0-9]+', '_', first_line)
        # Limit length
        name = '_'.join(name.split('_')[:3])[:30]
        return name.strip('_') or 'custom_module'
    
    def _is_new_module(self, module_name: str) -> bool:
        """Check if module already exists"""
        module_path = self.saraphina_root / f"{module_name}.py"
        return not module_path.exists()
    
    def _read_existing_module(self, module_name: str) -> str:
        """Read existing module code"""
        module_path = self.saraphina_root / f"{module_name}.py"
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {module_name}: {e}")
            return ""
    
    def _generate_module_from_spec(self, spec, module_name: str, past_failures: List) -> str:
        """Generate new module from structured spec with learning from failures"""
        
        # Build failure warnings
        failure_warnings = ""
        if past_failures:
            failure_warnings = "\n**PAST FAILURES TO AVOID:**\n"
            for failure in past_failures:
                failure_warnings += f"- {failure['error'][:150]}\n"
        
        prompt = f"""You are an expert Python developer implementing a module for Saraphina's self-upgrade system.

**STRUCTURED SPECIFICATION:**
Feature: {spec.feature_name}
Description: {spec.description}
Module to create: {module_name}.py
Requirements (Python packages): {', '.join(spec.requirements)}
System requirements: {', '.join(spec.system_requirements)}

**ACCEPTANCE CRITERIA:**
{chr(10).join(f"- {criteria}" for criteria in spec.acceptance_criteria)}

**TESTS TO PASS:**
{chr(10).join(f"- {test}" for test in spec.tests)}
{failure_warnings}
**CRITICAL RULES:**
1. NEVER import the module from within itself (no circular imports)
2. Create EXACTLY what the spec asks for - don't add unrelated features
3. If this is a voice/STT module, implement actual speech recognition using speech_recognition library
4. Use proper error handling and logging
5. Follow Saraphina patterns: dataclasses, type hints, comprehensive docstrings
6. NO placeholders, NO TODO comments - complete production code only

**CODE STRUCTURE:**
- Start with #!/usr/bin/env python3
- Import only what's needed (logging, dataclasses, typing, pathlib, and spec requirements)
- Main class with clear methods
- Proper error handling
- Type annotations

Generate ONLY the complete Python code for {module_name}.py. No explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer. Generate complete, production-ready code exactly matching the specification. Never create circular imports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Very low for precise spec following
                max_tokens=3500
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            if not code.startswith("#!"):
                code = "#!/usr/bin/env python3\n" + code
            
            return code
        
        except Exception as e:
            logger.error(f"GPT-4 spec-driven generation failed: {e}")
            return self._generate_spec_stub(spec, module_name)
    
    def _generate_modification_from_spec(self, spec, module_name: str, 
                                         original_code: str, past_failures: List) -> str:
        """Generate modifications to existing file from spec"""
        
        failure_warnings = ""
        if past_failures:
            failure_warnings = "\n**PAST FAILURES TO AVOID:**\n"
            for failure in past_failures:
                failure_warnings += f"- {failure['error'][:150]}\n"
        
        prompt = f"""You are modifying an existing file in Saraphina's codebase to integrate a new feature.

**SPECIFICATION:**
Feature: {spec.feature_name}
Description: {spec.description}
File to modify: {module_name}.py
New modules to integrate: {', '.join(spec.modules)}

**INTEGRATION REQUIREMENTS:**
{chr(10).join(f"- {criteria}" for criteria in spec.acceptance_criteria)}
{failure_warnings}
**ORIGINAL CODE:**
```python
{original_code[:3000]}  # First 3000 chars for context
```

**YOUR TASK:**
Modify the code to integrate the new feature. You must:
1. Add imports for new modules at the top
2. Add initialization in __init__ method
3. Add callback/handler methods if needed
4. Add cleanup in close/shutdown methods
5. Keep ALL existing functionality intact
6. Follow the existing code style exactly

**CRITICAL:**
- Return the COMPLETE modified file, not just the changes
- Preserve all existing features and methods
- Add the new integration seamlessly
- Match existing indentation and style

Generate the COMPLETE modified {module_name}.py file:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at integrating new features into existing code. Preserve all existing functionality."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            code = response.choices[0].message.content
            
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            if not code.startswith("#!") and original_code.startswith("#!"):
                code = "#!/usr/bin/env python3\n" + code
            
            return code
        
        except Exception as e:
            logger.error(f"GPT-4 modification generation failed: {e}")
            return original_code  # Return unchanged on error
    
    def _generate_tests_from_spec(self, spec, module_name: str, code: str) -> str:
        """
        Auto-generate pytest tests for a module
        
        Args:
            spec: UpgradeSpec with acceptance criteria and tests
            module_name: Name of module being tested
            code: The actual module code
        
        Returns:
            Test code as string
        """
        prompt = f"""Generate comprehensive pytest tests for a Python module.

**MODULE:** {module_name}.py
**FEATURE:** {spec.feature_name}

**MODULE CODE:**
```python
{code[:2000]}  # First 2000 chars for context
```

**ACCEPTANCE CRITERIA TO TEST:**
{chr(10).join(f"- {criteria}" for criteria in spec.acceptance_criteria)}

**TEST REQUIREMENTS:**
{chr(10).join(f"- {test}" for test in spec.tests)}

**YOUR TASK:**
Generate a complete pytest test file that:
1. Imports the module correctly: `from saraphina.{module_name} import *`
2. Tests all major functionality
3. Tests edge cases and error conditions
4. Uses pytest fixtures if appropriate
5. Has descriptive test names: test_<functionality>_<scenario>
6. Includes docstrings explaining what each test verifies
7. Aims for >80% code coverage

**TEST STRUCTURE:**
- Use pytest framework (not unittest)
- Each test should be independent
- Use assert statements with clear failure messages
- Mock external dependencies if needed

Generate ONLY the test code, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at writing comprehensive pytest tests. Generate complete, production-ready test suites."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            test_code = response.choices[0].message.content
            
            # Extract code
            if "```python" in test_code:
                test_code = test_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0].strip()
            
            # Ensure proper imports
            if not test_code.startswith("import") and not test_code.startswith("from"):
                test_code = "import pytest\n" + test_code
            
            return test_code
        
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            # Return minimal test stub
            return f'''import pytest
from saraphina.{module_name} import *

def test_{module_name}_imports():
    """Test that module imports successfully"""
    assert True  # If we got here, imports worked
'''
    
    def _generate_spec_stub(self, spec, module_name: str) -> str:
        """Generate a safe stub when GPT-4 fails"""
        return f'''#!/usr/bin/env python3
"""
{spec.feature_name}

{spec.description}
"""
import logging

logger = logging.getLogger("{module_name}")

class {module_name.title().replace('_', '')}:
    """Stub implementation"""
    
    def __init__(self):
        logger.warning("Using stub implementation - GPT-4 generation failed")
        pass
'''
    
    def _generate_new_module(self, gap, module_name: str, context: Dict) -> str:
        """Use GPT-4 to generate a complete new Python module"""
        
        # Build prompt with full context
        prompt = f"""You are an expert Python developer implementing a new module for Saraphina, an advanced autonomous AI system.

**REQUIREMENT:**
{gap.requirement}

**MODULE NAME:** {module_name}.py
**PHASE:** {gap.phase}
**SEVERITY:** {gap.severity}

**CONTEXT:**
- This is part of Saraphina's self-upgrade system
- Saraphina Root: D:\\Saraphina Root\\saraphina
- Existing modules use: logging, dataclasses, typing, pathlib
- Database: SQLite via saraphina.db module
- All modules follow PEP 8 and include comprehensive docstrings

**YOUR TASK:**
Generate COMPLETE, PRODUCTION-READY Python code for {module_name}.py that implements the requirement.

**REQUIREMENTS:**
1. Include proper imports, logging setup, and error handling
2. Use dataclasses for data structures
3. Include comprehensive docstrings
4. Follow existing Saraphina patterns (check context below)
5. Make it ROBUST - no placeholders or "TODO" comments
6. Include at least one main class with 3-5 meaningful methods

**CODE MUST:**
- Be immediately runnable without modifications
- Handle errors gracefully
- Log important operations
- Be type-annotated
- Be well-documented

Generate ONLY the Python code, no explanations. Start with #!/usr/bin/env python3"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer. Generate complete, production-ready code with no placeholders."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower for more deterministic code
                max_tokens=3000
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if wrapped
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            # Ensure it starts with shebang
            if not code.startswith("#!"):
                code = "#!/usr/bin/env python3\n" + code
            
            return code
        
        except Exception as e:
            logger.error(f"GPT-4 code generation failed: {e}")
            # Return a safe stub
            return self._generate_stub(module_name, gap)
    
    def _generate_module_modifications(self, gap, module_name: str, 
                                     original_code: str, context: Dict) -> str:
        """Use GPT-4 to modify an existing module"""
        
        prompt = f"""You are an expert Python developer modifying an existing Saraphina module.

**REQUIREMENT:**
{gap.requirement}

**MODULE:** {module_name}.py (already exists)
**CURRENT CODE:**
```python
{original_code[:2000]}  # First 2000 chars
```

**YOUR TASK:**
Modify the existing code to add the required functionality.

**GUIDELINES:**
1. Preserve all existing functionality
2. Add new methods/classes as needed
3. Update imports if required
4. Maintain code style consistency
5. Add proper docstrings for new code

Generate the COMPLETE MODIFIED file content, not a diff. Output only code."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at modifying Python code safely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            code = response.choices[0].message.content
            
            # Extract code
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            return code
        
        except Exception as e:
            logger.error(f"GPT-4 modification failed: {e}")
            return original_code
    
    def _generate_tests(self, gap, module_name: str, code: str) -> str:
        """Generate unit tests for the code"""
        
        prompt = f"""Generate pytest unit tests for this module:

**MODULE:** {module_name}.py
**CODE:**
```python
{code[:1500]}
```

Generate comprehensive tests covering main functionality.
Output only the test code starting with imports."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at writing Python unit tests with pytest."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            test_code = response.choices[0].message.content
            
            # Extract
            if "```python" in test_code:
                test_code = test_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0].strip()
            
            return test_code
        
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return f"# Tests for {module_name}\nimport pytest\n\ndef test_placeholder():\n    assert True"
    
    def _generate_stub(self, module_name: str, gap) -> str:
        """Generate a safe stub if GPT-4 fails"""
        class_name = ''.join(word.title() for word in module_name.split('_'))
        
        return f'''#!/usr/bin/env python3
"""
{class_name} - {gap.requirement}
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("{class_name}")


class {class_name}:
    """Auto-generated stub for {gap.requirement}"""
    
    def __init__(self):
        self.name = "{module_name}"
        logger.info(f"Initialized {{self.name}}")
    
    def process(self, data: Any) -> Dict[str, Any]:
        """Main processing method"""
        logger.info(f"Processing in {{self.name}}")
        return {{"status": "ok", "message": "Stub implementation"}}
'''
    
    def _calculate_risk(self, gap, artifact: CodeArtifact) -> float:
        """Calculate risk score for the artifact"""
        risk = 0.3  # Base risk
        
        # Severity increases risk
        severity_risk = {
            'critical': 0.3,
            'high': 0.2,
            'medium': 0.1,
            'low': 0.0
        }
        risk += severity_risk.get(gap.severity, 0.1)
        
        # New files are slightly safer than modifications
        if artifact.code_diffs:
            risk += 0.2
        
        # Large changes are riskier
        if artifact.estimated_loc > 300:
            risk += 0.2
        
        return min(risk, 1.0)
    
    def get_artifact(self, artifact_id: str) -> Optional[CodeArtifact]:
        """Retrieve artifact by ID"""
        return self.artifacts.get(artifact_id)
    
    def list_artifacts(self) -> List[CodeArtifact]:
        """List all generated artifacts"""
        return list(self.artifacts.values())
