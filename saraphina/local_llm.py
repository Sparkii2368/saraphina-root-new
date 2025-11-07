#!/usr/bin/env python3
"""
LocalLLM: offline reasoning with llama-cpp-python (optional).
Install: pip install llama-cpp-python
"""
from __future__ import annotations
from typing import Optional, Dict, Any

class LocalLLM:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/llama-2-7b-chat.Q4_K_M.gguf"
        self.llm = None
        self._try_load()

    def _try_load(self):
        try:
            from llama_cpp import Llama
            from pathlib import Path
            if Path(self.model_path).exists():
                self.llm = Llama(model_path=self.model_path, n_ctx=2048, n_threads=4)
        except Exception:
            self.llm = None

    def available(self) -> bool:
        return self.llm is not None

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        if not self.llm:
            return "[Local LLM unavailable]"
        try:
            out = self.llm(prompt, max_tokens=max_tokens, stop=["</s>", "\n\n"])
            return out['choices'][0]['text'].strip() if out.get('choices') else ""
        except Exception as e:
            return f"[LLM error: {e}]"
