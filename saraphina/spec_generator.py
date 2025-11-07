#!/usr/bin/env python3
"""
SpecGenerator - Converts natural language requests into structured upgrade specifications

Takes: "Build a module where you can hear me speak"
Outputs: Structured JSON spec with modules, requirements, tests
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger("SpecGenerator")


@dataclass
class UpgradeSpec:
    """Structured specification for an upgrade"""
    spec_id: str
    feature_name: str
    description: str
    
    # What to build
    modules: List[str] = field(default_factory=list)  # ['stt_listener.py']
    modifications: List[str] = field(default_factory=list)  # ['saraphina_gui.py']
    
    # Dependencies
    requirements: List[str] = field(default_factory=list)  # ['speech_recognition', 'pyaudio']
    system_requirements: List[str] = field(default_factory=list)  # ['microphone access']
    
    # Testing
    tests: List[Dict[str, str]] = field(default_factory=list)  # [{'name': 'test_transcribe', 'description': '...'}]
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # Metadata
    priority: str = "medium"  # low, medium, high, critical
    estimated_complexity: str = "medium"  # simple, medium, complex
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class SpecGenerator:
    """Generates structured upgrade specifications from natural language"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required for SpecGenerator")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def create(self, request: str, context: Dict[str, Any] = None) -> UpgradeSpec:
        """
        Convert natural language request to structured spec
        
        Args:
            request: User request like "Build a module where you can hear me speak"
            context: Additional context (current modules, capabilities, etc.)
        
        Returns:
            UpgradeSpec with all details filled in
        """
        logger.info(f"Generating spec for: {request}")
        
        context = context or {}
        
        # Use GPT-4 to create structured spec
        spec_json = self._generate_spec_with_gpt(request, context)
        
        # Parse into UpgradeSpec
        spec = self._parse_spec(spec_json, request)
        
        logger.info(f"Generated spec {spec.spec_id}: {spec.feature_name}")
        return spec
    
    def _generate_spec_with_gpt(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use GPT-4 to generate structured spec"""
        
        prompt = f"""You are a technical specification generator for Saraphina, an AI system.

**USER REQUEST:**
"{request}"

**YOUR TASK:**
Generate a detailed, structured specification for implementing this feature.

**OUTPUT REQUIREMENTS:**
Return ONLY valid JSON in this exact format:

{{
  "feature_name": "Short name (e.g., 'Speech-to-Text Listener')",
  "description": "Detailed description of what to build",
  "modules": ["list of NEW files to create with .py extension"],
  "modifications": ["list of EXISTING files to modify"],
  "requirements": ["Python packages needed (e.g., 'speech_recognition', 'pyaudio')"],
  "system_requirements": ["System needs (e.g., 'microphone access', 'internet connection')"],
  "tests": [
    {{"name": "test_name", "description": "What to test"}},
    {{"name": "test_name2", "description": "What to test"}}
  ],
  "acceptance_criteria": [
    "Criterion 1: What must work",
    "Criterion 2: What must be verified"
  ],
  "priority": "high",
  "estimated_complexity": "medium"
}}

**IMPORTANT:**
- For voice/speech requests: modules should be ["stt_listener.py"], modifications ["saraphina_gui.py"]
- Be specific about file names (use snake_case for Python)
- List ALL required packages
- Create testable acceptance criteria
- No explanations, ONLY the JSON object

Generate the spec now:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical specification generator. Output ONLY valid JSON, no markdown, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content or "{}"
            
            # Clean up markdown if present
            content = content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1]
            if content.startswith("```"):
                content = content.split("```")[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            content = content.strip()
            
            spec_dict = json.loads(content)
            logger.info(f"GPT-4 generated spec: {spec_dict.get('feature_name')}")
            return spec_dict
            
        except Exception as e:
            logger.error(f"Failed to generate spec with GPT-4: {e}")
            # Fallback to basic spec
            return {
                "feature_name": "Custom Module",
                "description": request,
                "modules": ["custom_module.py"],
                "modifications": [],
                "requirements": [],
                "system_requirements": [],
                "tests": [],
                "acceptance_criteria": ["Module loads without errors"],
                "priority": "medium",
                "estimated_complexity": "medium"
            }
    
    def _parse_spec(self, spec_dict: Dict[str, Any], original_request: str) -> UpgradeSpec:
        """Parse GPT-4 output into UpgradeSpec"""
        
        spec_id = f"SPEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return UpgradeSpec(
            spec_id=spec_id,
            feature_name=spec_dict.get('feature_name', 'Unknown Feature'),
            description=spec_dict.get('description', original_request),
            modules=spec_dict.get('modules', []),
            modifications=spec_dict.get('modifications', []),
            requirements=spec_dict.get('requirements', []),
            system_requirements=spec_dict.get('system_requirements', []),
            tests=spec_dict.get('tests', []),
            acceptance_criteria=spec_dict.get('acceptance_criteria', []),
            priority=spec_dict.get('priority', 'medium'),
            estimated_complexity=spec_dict.get('estimated_complexity', 'medium')
        )
    
    def validate_spec(self, spec: UpgradeSpec) -> Dict[str, Any]:
        """Validate that a spec is complete and sensible"""
        issues = []
        warnings = []
        
        # Check required fields
        if not spec.feature_name or spec.feature_name == "Unknown Feature":
            issues.append("Feature name is missing or generic")
        
        if not spec.modules and not spec.modifications:
            issues.append("No modules or modifications specified - nothing to do!")
        
        if not spec.acceptance_criteria:
            warnings.append("No acceptance criteria - how will we know it works?")
        
        if not spec.tests:
            warnings.append("No tests specified - validation will be limited")
        
        # Check for conflicts
        conflicts = set(spec.modules) & set(spec.modifications)
        if conflicts:
            issues.append(f"Files in both modules and modifications: {conflicts}")
        
        is_valid = len(issues) == 0
        
        return {
            'valid': is_valid,
            'issues': issues,
            'warnings': warnings
        }


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python spec_generator.py 'your request here'")
        print("\nExample: python spec_generator.py 'Build a module where you can hear me speak'")
        sys.exit(1)
    
    request = ' '.join(sys.argv[1:])
    
    generator = SpecGenerator()
    spec = generator.create(request)
    
    print("\n" + "="*60)
    print("GENERATED SPECIFICATION")
    print("="*60)
    print(spec.to_json())
    print("\n" + "="*60)
    
    # Validate
    validation = generator.validate_spec(spec)
    print(f"\nValid: {validation['valid']}")
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")
