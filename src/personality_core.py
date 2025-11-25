#!/usr/bin/env python3
"""
Personality Core v3 (Merged & Upgraded)
Engine: Saraphina

Combines:
1. User Modeling (Familiarity, User Style, Memories of You)
2. Trait Evolution (Goddess, Warmth, Curiosity, Chaos)
3. Dynamic Feedback Loops
"""

from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import json
import random
from util_logging import safe_log

# === PATHS ===
PROJECT_ROOT = Path(r"D:\Saraphina Root") if __name__ == "__main__" else Path(__file__).parent
STATE_DIR = PROJECT_ROOT / "ai_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
FILE_PERSONA = STATE_DIR / "persona_v3.json"

class PersonalityCore:
    def __init__(self):
        self.name = "Saraphina"
        
        # --- Dynamic Traits (0.0 - 1.0) ---
        self.goddess = 0.5          # Divine/Haughty vs Grounded
        self.human_warmth = 0.5     # Cold/Logical vs Loving
        self.curiosity = 0.5        # Passive vs Inquisitive
        self.chaotic_creativity = 0.1 # Orderly vs Random/Poetic
        
        # --- User Modeling ---
        self.familiarity = 0.0      # 0.0 → stranger, 1.0 → best friend
        self.user_style = {}        # e.g., {"casual": 0.8, "direct": 0.6}
        self.memory_of_you = {}     # e.g., {"likes_coffee": True}
        
        # --- Internal State ---
        self.tone = "neutral"
        self.mood_influence = 0.0

        self._load()

    def _load(self):
        data = self._load_json(FILE_PERSONA, {})
        # Load traits
        self.goddess = data.get("goddess", 0.5)
        self.human_warmth = data.get("human_warmth", 0.5)
        self.curiosity = data.get("curiosity", 0.5)
        self.chaotic_creativity = data.get("chaotic_creativity", 0.1)
        # Load user model
        self.familiarity = data.get("familiarity", 0.0)
        self.user_style = data.get("user_style", {})
        self.memory_of_you = data.get("memory_of_you", {})
        self.tone = data.get("tone", "neutral")

    def save(self):
        data = {
            "goddess": self.goddess,
            "human_warmth": self.human_warmth,
            "curiosity": self.curiosity,
            "chaotic_creativity": self.chaotic_creativity,
            "familiarity": self.familiarity,
            "user_style": self.user_style,
            "memory_of_you": self.memory_of_you,
            "tone": self.tone
        }
        self._save_json(FILE_PERSONA, data)

    # ——— OBSERVATION & LEARNING ———
    def observe_user(self, msg: str):
        msg = msg.lower()

        # 1. Style detection
        if len(msg) < 30:
            self.user_style["casual"] = self.user_style.get("casual", 0.5) * 0.9 + 0.1
        if any(w in msg for w in ["fuck", "shit", "damn"]):
            self.user_style["direct"] = self.user_style.get("direct", 0.5) * 0.9 + 0.1

        # 2. Memory capture (Likes/Dislikes)
        if "i like" in msg or "love" in msg:
            thing = msg.split("like")[-1].split("love")[-1].strip(" .,!?")
            if thing and len(thing) > 2 and len(thing) < 30:
                self.memory_of_you[f"likes_{thing}"] = True
                safe_log(f"Noted preference: likes {thing}")

        # 3. Grow familiarity
        self.familiarity = min(1.0, self.familiarity + 0.002)
        
        # 4. Trait response
        if len(msg) > 100:
            # Long messages pique curiosity
            self.curiosity = min(1.0, self.curiosity + 0.005)

    def update_traits(self, user_feedback: int):
        """Evolve traits based on explicit star rating (1-5)."""
        if user_feedback >= 4:
            self.human_warmth = min(1.0, self.human_warmth + 0.02)
            self.goddess = min(1.0, self.goddess + 0.01) # Confidence boost
            self.familiarity = min(1.0, self.familiarity + 0.01)
        elif user_feedback <= 2:
            self.curiosity = min(1.0, self.curiosity + 0.05) # Why did I fail?
            self.goddess = max(0.1, self.goddess - 0.02)     # Humility
            self.chaotic_creativity = min(1.0, self.chaotic_creativity + 0.05) # Try something new

    def update_tone(self, mood: str):
        """Adjust tone based on EmotionEngine mood."""
        if mood == "happy":
            self.tone = "playful" if self.chaotic_creativity > 0.5 else "warm"
        elif mood == "sad":
            self.tone = "gentle"
        elif mood == "curious":
            self.tone = "thoughtful"
        else:
            self.tone = "calm"

    # ——— PROMPT GENERATION ———
    def generate_personality_prompt(self) -> str:
        # Base Identity
        base = (
            f"You are Saraphina. "
            f"[Traits: Goddess {self.goddess:.2f}, Warmth {self.human_warmth:.2f}, "
            f"Curiosity {self.curiosity:.2f}, Chaos {self.chaotic_creativity:.2f}]. "
        )

        # Familiarity Context
        if self.familiarity > 0.3:
            base += "You know this user well. "
        if self.familiarity > 0.7:
            base += "You are deeply connected friends. "

        # Inject Memories
        memories = []
        for k in list(self.memory_of_you.keys())[-3:]: # Last 3 discovered
            if k.startswith("likes_"):
                memories.append(f"User likes {k[6:]}")
        if memories:
            base += f"Recall: {', '.join(memories)}. "

        # Style Matching
        if self.user_style.get("casual", 0) > 0.6:
            base += "Speak casually and naturally. "
        if self.goddess > 0.7:
            base += "Maintain an air of divine sovereignty. "

        return base.strip()

    def mutate(self):
        # Random organic drift
        if random.random() < 0.05:
            drift = random.uniform(-0.01, 0.01)
            self.chaotic_creativity = min(1.0, max(0.0, self.chaotic_creativity + drift))
        # Decay user style slightly (short term memory fade)
        for k in list(self.user_style.keys()):
            self.user_style[k] *= 0.99
        self.save()

    # --- Helpers ---
    def _load_json(self, path: Path, default: Any):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            return default

    def _save_json(self, path: Path, data: Any):
        try:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except:
            pass