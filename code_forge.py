import os
import json
from typing import Optional, Dict, Any

from sandbox_validator import SandboxValidator
from upgrade_learning_journal import UpgradeLearningJournal

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class CodeForge:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.journal = UpgradeLearningJournal()
        self.validator = SandboxValidator()

        if not self.api_key:
            raise ValueError("OpenAI API key missing. Set OPENAI_API_KEY.")

    def _generate_code_with_gpt(self, prompt: str) -> str:
        import openai
        openai.api_key = self.api_key

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code generator. Follow the instructions strictly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response['choices'][0]['message']['content']

    def _build_prompt_from_spec(self, spec: dict) -> str:
        return (
            f"Your task is to write Python code for the following feature:\n\n"
            f"Feature: {spec.get('feature_name')}\n"
            f"Modules to create: {spec.get('modules')}\n"
            f"Files to modify: {spec.get('modifications')}\n\n"
            f"Requirements: {', '.join(spec.get('requirements', []))}\n\n"
            f"Acceptance Criteria:\n"
            + "\n".join(f"- {ac}" for ac in spec.get("acceptance_criteria", [])) +
            "\n\nOutput only valid Python code. No explanations or markdown formatting."
        )

    def generate_from_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt_from_spec(spec)

        try:
            print(f"[CodeForge] Generating code for: {spec.get('feature_name')}")

            generated_code = self._generate_code_with_gpt(prompt)

            # Run sandbox validation
            validation_result = self.validator.test(generated_code, spec).to_dict()

            if validation_result["passed"]:
                self.journal.log_success(spec, generated_code)
                return {
                    "success": True,
                    "code": generated_code,
                    "errors": [],
                    "spec": spec
                }
            else:
                self.journal.log_failure(spec, generated_code, validation_result, "Validation failed")
                return {
                    "success": False,
                    "code": generated_code,
                    "errors": validation_result["errors"],
                    "spec": spec
                }

        except Exception as e:
            print(f"[CodeForge] Unexpected error: {e}")
            self.journal.log_failure(spec, "", {"passed": False, "errors": [str(e)]}, str(e))
            return {
                "success": False,
                "code": "",
                "errors": [str(e)],
                "spec": spec
            }
