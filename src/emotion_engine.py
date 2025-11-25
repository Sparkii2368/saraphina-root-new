#!/usr/bin/env python3
"""
Emotion Engine for Saraphina
Simulates emotional states and mood.
"""

import random
from typing import Dict


class EmotionEngine:
    def __init__(self):
        self.mood = "neutral"  # neutral, happy, sad, curious, excited
        self.affinity = 0.5  # Towards Jacques, 0-1

    def get_mood(self) -> str:
        return self.mood

    def apply_emotional_tone(self, text: str) -> str:
        if self.mood == "happy":
            return text + " :)"
        elif self.mood == "curious":
            return text + "?"
        return text

    def update_mood(self, stimulus: str):
        s = stimulus.lower()
        if "love" in s or "thank you" in s:
            self.mood = "happy"
            self.affinity += 0.05
        elif "hate" in s or "angry" in s:
            self.mood = "sad"
            self.affinity -= 0.05
        elif "why" in s or "how" in s:
            self.mood = "curious"
        self.affinity = max(0, min(1, self.affinity))