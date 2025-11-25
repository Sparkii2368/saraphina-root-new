#!/usr/bin/env python3
"""
Local LLM Client for Saraphina
Handles local inference with GPT4All, with safety, temperature, and graceful fallback.
"""

import os
from typing import Optional

try:
    from gpt4all import GPT4All
    HAS_GPT4ALL = True
except Exception:
    GPT4All = None  # type: ignore
    HAS_GPT4ALL = False


def safe_log(msg: str):
    # Mirror UltraCore's style without importing it to avoid circular deps
    print(f"[LocalLLM] {msg}")


class LocalLLMClient:
    """
    Thin wrapper around GPT4All with:

    - Configurable model path (env override)
    - Temperature & sampling controls
    - Graceful fallback if model or library are missing
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_tokens: int = 200,
    ):
        # Allow override via env if present
        env_path = os.getenv("SARAPHINA_LOCAL_MODEL")
        self.model_path = env_path or model_path or (
            r"D:\Saraphina Root\data\models\local\gpt4all-falcon-newbpe-q4_0.gguf"
        )

        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.max_tokens = int(max_tokens)

        self.model: Optional["GPT4All"] = None
        self.available = False

        self._init_model()

    def _init_model(self):
        if not HAS_GPT4ALL:
            safe_log("gpt4all library not available; local LLM disabled.")
            return

        if not os.path.exists(self.model_path):
            safe_log(f"Local model file not found at: {self.model_path}")
            return

        try:
            self.model = GPT4All(self.model_path)
            self.available = True
            safe_log(f"Local LLM loaded from {self.model_path}")
        except Exception as e:
            safe_log(f"Failed to load local LLM model: {e}")
            self.model = None
            self.available = False

    def generate_local_reply(self, prompt: str) -> str:
        """
        Generate a reply using the local GPT4All model.

        If the model is not available, return a safe fallback string instead of raising.
        """
        if not self.available or self.model is None:
            safe_log("Local model unavailable; falling back to safe stub reply.")
            return (
                "I heard what you said and I'm thinking about it. "
                "My local thinking engine isn't fully online right now, "
                "so this reply might be simpler than usual."
            )

        try:
            return self.model.generate(
                prompt,
                max_tokens=self.max_tokens,
                temp=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
            )
        except TypeError:
            # Older GPT4All API may not support all kwargs
            safe_log("GPT4All generate() signature mismatch; falling back to minimal call.")
            try:
                return self.model.generate(prompt, max_tokens=self.max_tokens)
            except Exception as e:
                safe_log(f"Local generation failed: {e}")
                return (
                    "I tried to think locally about this, but something went wrong. "
                    "I'm still here with you."
                )
        except Exception as e:
            safe_log(f"Local generation failed: {e}")
            return (
                "I tried to think locally about this, but something went wrong. "
                "I'm still here with you."
            )