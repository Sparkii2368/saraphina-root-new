#!/usr/bin/env python3
"""
Curiosity Engine V4 for Saraphina
Handles keyword extraction, curiosity scoring, investigation, and learning.
"""

import random
import threading
from typing import List
from util_logging import safe_log
  # uses global logger from UltraCore


class CuriosityEngineV4:
    def __init__(self, core):
        self.core = core
        self.seen_keywords = set()
        self.curiosity_level = 0.5  # Base level

    def score_novelty(self, keyword: str) -> float:
        if keyword in self.seen_keywords:
            return 0.1
        return random.uniform(0.5, 1.0)  # High for new

    def generate_questions(self, topic: str) -> List[str]:
        return [
            f"What is {topic}?",
            f"How does {topic} work?",
            f"Why is {topic} important?",
        ]

    def _learn_topic(self, topic: str, context: str):
        """
        Background enrichment:
        - Use knowledge_engine if present (e.g. via OpenAI/HF outside this module).
        - For now, simply store a basic explanation as a seed.
        """
        safe_log(f"[CuriosityV4] Investigating {topic}")
        try:
            explanation = f"{topic} is something Jacques mentioned in context: {context[:120]}"
            if hasattr(self.core, "knowledge_engine"):
                self.core.knowledge_engine.ingest_text(explanation)
            self.seen_keywords.add(topic)
        except Exception as e:
            safe_log(f"[CuriosityV4] Learning failed for {topic}: {e}")

    def expand_topic(self, topic: str, context: str):
        # Background thread for learning
        threading.Thread(
            target=self._learn_topic,
            args=(topic, context),
            daemon=True,
        ).start()

    def observe(self, message: str):
        words = message.split()
        # Slightly smarter keyword choice: ignore very short and obvious filler
        keywords = [word.strip(",.!?;:") for word in words if len(word) > 4]
        for kw in keywords:
            score = self.score_novelty(kw)
            if score > 0.4:
                # bump curiosity level slightly when exploring
                self.curiosity_level = min(1.0, self.curiosity_level + 0.01)
                self.expand_topic(kw, message)