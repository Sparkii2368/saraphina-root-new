#!/usr/bin/env python3
"""
AI-Powered Risk Analyzer - Use GPT-4o to intelligently assess code change risk.

Phase 30.5: Enhancement over regex-based CodeRiskModel.
Uses GPT-4o to understand code intent, context, and nuanced security implications.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime


class AIRiskAnalyzer:
    """
    Intelligent risk analysis using GPT-4o.
    
    Advantages over regex-based CodeRiskModel:
    - Understands intent (refactoring vs removing security)
    - Context-aware (knows when encryption removal is safe)
    - Detects subtle vulnerabilities (SQL injection, XSS)
    - Explains reasoning in natural language
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize AI Risk Analyzer.
        
        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
            model: Model to use (gpt-4o, gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key parameter.")
        
        # Lazy import to avoid dependency if not used
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    def analyze_patch(
        self,
        original_code: str,
        modified_code: str,
        file_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code patch using GPT-4o.
        
        Args:
            original_code: Original code
            modified_code: Modified code
            file_name: Name of file being modified
            context: Additional context (purpose, related files, etc.)
        
        Returns:
            Dict with:
                - risk_level: SAFE, CAUTION, SENSITIVE, CRITICAL
                - risk_score: 0.0-1.0
                - concerns: List of security concerns
                - reasoning: Natural language explanation
                - recommendations: What to check before approving
                - confidence: AI's confidence in assessment (0.0-1.0)
        """
        prompt = self._build_analysis_prompt(
            original_code,
            modified_code,
            file_name,
            context
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result['analyzed_at'] = datetime.now().isoformat()
            result['model'] = self.model
            result['file_name'] = file_name
            
            # Validate and normalize
            return self._validate_result(result)
        
        except Exception as e:
            # Fallback to conservative assessment on API error
            return {
                'risk_level': 'CAUTION',
                'risk_score': 0.5,
                'concerns': [f'AI analysis failed: {str(e)}'],
                'reasoning': 'Unable to perform AI analysis, defaulting to caution',
                'recommendations': ['Manual review required', 'AI analysis unavailable'],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _get_system_prompt(self) -> str:
        """Get system prompt defining AI's role."""
        return """You are an expert security code reviewer for Saraphina, a self-modifying AI system.

Your role is to analyze code changes and assess security risk. Consider:

**Security Concerns:**
- Authentication & Authorization changes
- Encryption/Decryption modifications
- Data deletion or loss potential
- SQL injection, XSS, command injection vectors
- Permission escalation (sudo, system calls)
- Credential exposure (API keys, passwords)
- Network security (open ports, unvalidated input)
- Race conditions, TOCTOU vulnerabilities
- Resource exhaustion (DoS potential)

**Context Matters:**
- Refactoring encryption != Removing encryption
- Moving auth logic to separate module != Disabling auth
- Adding input validation == GOOD (reduces risk)
- Replacing weak crypto with strong == GOOD

**Risk Levels:**
- SAFE: Documentation, formatting, safe refactoring, adding security
- CAUTION: Logic changes, new dependencies, minor structural changes
- SENSITIVE: Auth/crypto changes, data operations, privileged code
- CRITICAL: Removing security, data deletion, dangerous operations

Always explain your reasoning clearly and suggest what to verify."""
    
    def _build_analysis_prompt(
        self,
        original: str,
        modified: str,
        file_name: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the analysis prompt."""
        # Truncate very long code for API limits
        max_lines = 200
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        if len(original_lines) > max_lines:
            original = '\n'.join(original_lines[:max_lines]) + '\n... (truncated)'
        if len(modified_lines) > max_lines:
            modified = '\n'.join(modified_lines[:max_lines]) + '\n... (truncated)'
        
        prompt = f"""Analyze this code change for security risks:

**FILE:** {file_name}

**ORIGINAL CODE:**
```python
{original}
```

**MODIFIED CODE:**
```python
{modified}
```
"""
        
        if context:
            prompt += f"\n**CONTEXT:** {json.dumps(context, indent=2)}\n"
        
        prompt += """

**REQUIRED OUTPUT (JSON):**
{
    "risk_level": "SAFE|CAUTION|SENSITIVE|CRITICAL",
    "risk_score": 0.0-1.0,
    "concerns": ["specific security concern 1", "concern 2", ...],
    "reasoning": "Detailed explanation of your risk assessment",
    "recommendations": ["What to verify before approving", ...],
    "confidence": 0.0-1.0,
    "safe_aspects": ["What's good about this change", ...],
    "flags": ["encryption_change", "auth_modification", "data_deletion", ...]
}

Consider:
1. What's the INTENT of this change?
2. Does it weaken or strengthen security?
3. Could it lead to data loss or exposure?
4. Are there subtle vulnerabilities introduced?
5. Is the change reversible?

Be precise and specific in your concerns."""
        
        return prompt
    
    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize AI response."""
        # Ensure required fields
        defaults = {
            'risk_level': 'CAUTION',
            'risk_score': 0.5,
            'concerns': [],
            'reasoning': '',
            'recommendations': [],
            'confidence': 0.5,
            'safe_aspects': [],
            'flags': []
        }
        
        for key, default in defaults.items():
            if key not in result:
                result[key] = default
        
        # Normalize risk_level
        valid_levels = {'SAFE', 'CAUTION', 'SENSITIVE', 'CRITICAL'}
        if result['risk_level'] not in valid_levels:
            result['risk_level'] = 'CAUTION'
        
        # Clamp risk_score
        result['risk_score'] = max(0.0, min(1.0, float(result.get('risk_score', 0.5))))
        
        # Ensure risk_level matches risk_score
        if result['risk_score'] >= 0.7 and result['risk_level'] not in ['CRITICAL', 'SENSITIVE']:
            result['risk_level'] = 'CRITICAL'
        elif result['risk_score'] >= 0.4 and result['risk_level'] == 'SAFE':
            result['risk_level'] = 'CAUTION'
        
        return result
    
    def explain_diff(
        self,
        original: str,
        modified: str,
        file_name: str
    ) -> str:
        """
        Get plain-English explanation of what changed.
        
        Returns:
            Human-readable explanation of the changes
        """
        prompt = f"""Explain this code change in plain English:

**FILE:** {file_name}

**BEFORE:**
```python
{original[:1000]}  # Truncated for brevity
```

**AFTER:**
```python
{modified[:1000]}  # Truncated for brevity
```

Provide a clear, non-technical explanation:
1. What changed?
2. Why might this change have been made?
3. What are the potential risks?
4. What should someone verify before approving?

Keep it concise and focused."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You explain code changes clearly to non-programmers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Unable to generate explanation: {str(e)}"
    
    def compare_with_regex_model(
        self,
        original: str,
        modified: str,
        file_name: str,
        regex_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare AI analysis with regex-based model.
        
        Useful for understanding where AI adds value.
        
        Returns:
            Comparison showing agreements/disagreements
        """
        ai_result = self.analyze_patch(original, modified, file_name)
        
        comparison = {
            'ai_risk_level': ai_result['risk_level'],
            'regex_risk_level': regex_result['risk_level'],
            'agreement': ai_result['risk_level'] == regex_result['risk_level'],
            'ai_more_cautious': self._risk_level_value(ai_result['risk_level']) > 
                               self._risk_level_value(regex_result['risk_level']),
            'ai_reasoning': ai_result['reasoning'],
            'regex_flags': regex_result.get('flags', []),
            'ai_flags': ai_result.get('flags', []),
            'recommendation': 'Trust AI analysis (more context-aware)' if not comparison.get('agreement') else 'Both models agree'
        }
        
        return comparison
    
    def _risk_level_value(self, level: str) -> int:
        """Convert risk level to numeric value for comparison."""
        levels = {'SAFE': 0, 'CAUTION': 1, 'SENSITIVE': 2, 'CRITICAL': 3}
        return levels.get(level, 1)
    
    def batch_analyze(
        self,
        patches: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Analyze multiple patches efficiently.
        
        Args:
            patches: List of {original, modified, file_name} dicts
        
        Returns:
            List of analysis results
        """
        results = []
        
        for patch in patches:
            result = self.analyze_patch(
                patch['original'],
                patch['modified'],
                patch['file_name'],
                patch.get('context')
            )
            results.append(result)
        
        return results
    
    def format_approval_request(
        self,
        analysis: Dict[str, Any],
        patch_id: str
    ) -> str:
        """
        Format AI analysis as approval request message.
        
        Returns:
            Formatted message for owner
        """
        risk_icons = {
            'SAFE': '✅',
            'CAUTION': '⚠️',
            'SENSITIVE': '🔒',
            'CRITICAL': '🚨'
        }
        
        icon = risk_icons.get(analysis['risk_level'], '❓')
        
        message = f"{icon} AI Risk Analysis - Patch {patch_id}\n\n"
        message += f"**Risk Level:** {analysis['risk_level']} ({analysis['risk_score']:.2f})\n"
        message += f"**Confidence:** {analysis.get('confidence', 0.5):.1%}\n\n"
        
        message += "**Reasoning:**\n"
        message += f"{analysis['reasoning']}\n\n"
        
        if analysis.get('concerns'):
            message += "**Security Concerns:**\n"
            for concern in analysis['concerns']:
                message += f"  • {concern}\n"
            message += "\n"
        
        if analysis.get('safe_aspects'):
            message += "**Positive Aspects:**\n"
            for aspect in analysis['safe_aspects']:
                message += f"  ✓ {aspect}\n"
            message += "\n"
        
        if analysis.get('recommendations'):
            message += "**Before Approving, Verify:**\n"
            for rec in analysis['recommendations']:
                message += f"  → {rec}\n"
        
        return message
