#!/usr/bin/env python3
"""
OOD detection heuristics for text and code.
- Flags out-of-distribution queries (unknown topic ratio high)
- Flags high-risk code patterns for manual review
"""
import re
from typing import List

KNOWN_TOKENS = set([
    # domains
    'python','javascript','java','c#','go','rust','docker','kubernetes','aws','azure','gcp',
    'devops','terraform','ansible','react','vue','angular','api','database','postgres','mysql','mongodb',
    'security','jwt','oauth','mfa','tls','ssl','linux','windows','macos','ml','pytorch','tensorflow','nlp'
])

HIGH_RISK_CODE_PATTERNS = [
    r"\bos\.system\(",
    r"\bsubprocess\.",
    r"\bsocket\.",
    r"\brequests\.",
    r"\bopen\(.*['\"]w",
    r"rm -rf",
    r"format\s+c:",
]

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_#+.-]+", text.lower())

def is_text_ood(text: str) -> bool:
    toks = tokenize(text)
    if len(toks) < 8:
        return False
    unknown = sum(1 for t in toks if t not in KNOWN_TOKENS)
    ratio = unknown / max(1, len(toks))
    return ratio > 0.85

def is_code_high_risk(code: str) -> bool:
    src = code or ""
    for pat in HIGH_RISK_CODE_PATTERNS:
        if re.search(pat, src, re.IGNORECASE):
            return True
    return False
