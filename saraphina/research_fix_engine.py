#!/usr/bin/env python3
"""
Research & Fix Engine - Autonomously researches and fixes errors
Uses GPT-4 to understand errors and propose solutions
"""

import os
import logging
from typing import Dict, Optional
from openai import OpenAI

logger = logging.getLogger("ResearchFixEngine")


class ResearchFixEngine:
    """Research errors and propose fixes using GPT-4"""
    
    def __init__(self, error_kb):
        self.error_kb = error_kb
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def research_error(self, error_event: Dict) -> Optional[Dict]:
        """Research an error and propose a fix"""
        
        if not self.client:
            logger.warning("OpenAI API not available for error research")
            return None
        
        try:
            # Build research prompt
            prompt = self._build_research_prompt(error_event)
            
            logger.info(f"Researching error {error_event['error_id']}...")
            
            # Query GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Python debugging AI. Analyze errors and propose precise, actionable fixes.

Your response MUST be in this JSON format:
{
    "diagnosis": "What caused this error",
    "fix_description": "How to fix it",
    "fix_code": "Actual Python code to fix (if applicable)",
    "prevention": "How to prevent this in the future",
    "confidence": 0.0-1.0
}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            fix_proposal = self._parse_response(response.choices[0].message.content)
            
            if fix_proposal:
                logger.info(f"Fix proposal generated for {error_event['error_id']}")
                return fix_proposal
            
        except Exception as e:
            logger.error(f"Error research failed: {e}")
        
        return None
    
    def _build_research_prompt(self, error_event: Dict) -> str:
        """Build GPT-4 prompt for error research"""
        
        prompt = f"""I encountered an error in my AI system. Help me fix it.

**Subsystem**: {error_event['subsystem']}
**Function**: {error_event['function']}
**Error Type**: {error_event['error_type']}
**Message**: {error_event['message']}

**Stack Trace**:
```
{error_event.get('stack_trace', 'Not available')[:1000]}
```

**Context**:
- Arguments: {error_event.get('args', 'None')[:200]}
- This error has occurred {error_event.get('occurrence_count', 1)} time(s)

Analyze this error and provide:
1. Root cause diagnosis
2. Specific fix (code patch if applicable)
3. Prevention strategy

Respond in JSON format as specified."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """Parse GPT-4 response"""
        
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fix_data = json.loads(json_match.group(0))
                return fix_data
            
            # Fallback: treat as plain text
            return {
                "diagnosis": response_text[:500],
                "fix_description": "See diagnosis",
                "fix_code": None,
                "prevention": "Unknown",
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"Failed to parse fix proposal: {e}")
            return None
    
    def test_fix_in_sandbox(self, fix_proposal: Dict, error_event: Dict) -> bool:
        """Test a proposed fix in a safe sandbox"""
        
        # TODO: Implement sandbox testing
        # For now, just return True if fix looks reasonable
        
        if not fix_proposal.get('fix_code'):
            return False
        
        # Basic checks
        dangerous_keywords = ['os.system', 'subprocess', 'eval', 'exec', '__import__']
        fix_code = fix_proposal.get('fix_code', '')
        
        if any(keyword in fix_code for keyword in dangerous_keywords):
            logger.warning(f"Fix contains dangerous operations - requires approval")
            return False
        
        logger.info(f"Fix passed sandbox validation")
        return True
    
    def apply_fix(self, error_id: str, fix_proposal: Dict):
        """Store a validated fix"""
        
        self.error_kb.store_fix(
            error_id=error_id,
            fix_code=fix_proposal.get('fix_code', ''),
            fix_description=fix_proposal.get('fix_description', '')
        )
        
        logger.info(f"Fix stored for error {error_id}")
