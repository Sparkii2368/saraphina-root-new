#!/usr/bin/env python3
"""
Hybrid Model Router for Saraphina
Decides between local and OpenAI based on criteria.
"""

import os
import random
from typing import Tuple, Optional

from openai import OpenAI


class HybridModelRouter:
    def __init__(self, local_client):
        self.local_client = local_client
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
        # New fields used by GUI / UltraCore
        self.forced_mode: Optional[str] = None  # None | "local" | "openai"
        self.last_mode: Optional[str] = None    # last resolved mode

    def route(self, prompt: str) -> Tuple[str, str]:
        """
        Returns (mode, adjusted_prompt).
        Mode is "local" or "openai".
        """
        # Forced override from GUI / UltraCore
        if self.forced_mode == "local":
            self.last_mode = "local"
            return "local", prompt
        if self.forced_mode == "openai" and self.openai_client is not None:
            self.last_mode = "openai"
            return "openai", prompt

        # Decision logic
        if len(prompt) > 500 or random.random() < 0.3:
            if self.openai_client:
                self.last_mode = "openai"
                return "openai", prompt

        self.last_mode = "local"
        return "local", prompt

    def generate(self, prompt: str) -> str:
        mode, adjusted_prompt = self.route(prompt)
        if mode == "openai" and self.openai_client is not None:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": adjusted_prompt}],
            )
            return resp.choices[0].message.content or ""
        # Fallback to local
        return self.local_client.generate_local_reply(adjusted_prompt)