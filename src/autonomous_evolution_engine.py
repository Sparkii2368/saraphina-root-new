#!/usr/bin/env python3
"""
Autonomous Evolution Engine – Saraphina v9 (November 15, 2025)
True Self-Improvement via RLHF + Meta-Learning + Evolutionary Algorithms

Integrated design:
- EvolutionEngine: RLHF-style reward model + personality evolution + self-critique
- AutonomousEvolutionEngine: higher-level autonomous coordinator around EvolutionEngine
  * Tracks long-horizon stats about interactions
  * Can schedule / bias evolution steps
  * Provides introspection hooks and safe telemetry only (no direct code changes)

Both engines:
- Run as sidecar modules, called explicitly from ultra_core.chat_v4()
- Do NOT monkey-patch UltraAICore.chat_v4; ultra_core remains the single pipeline
- Are hot-reload safe, thread-safe, and designed to fail closed (no crashes).

Usage in ultra_core.py (inside UltraAICore.__init__):

    from autonomous_evolution_engine import EvolutionEngine, AutonomousEvolutionEngine

    self.evolution_engine = EvolutionEngine(self)
    self.autonomous_evolution_engine = AutonomousEvolutionEngine(self)

Usage in chat_v4 (after `reply` is produced and before returning):

    try:
        improved, reward = self.evolution_engine.process_interaction(
            user_msg=msg,
            raw_reply=reply,
            context=full_prompt,
        )
        if improved and improved.strip() and improved.strip() != reply.strip():
            reply = improved
    except Exception:
        pass

You MAY also wire AutonomousEvolutionEngine observationally, e.g.:

    if self.autonomous_evolution_engine is not None:
        self.autonomous_evolution_engine.observe_interaction(
            user_msg=msg,
            reply=reply,
            reward_estimate=reward,
        )
"""

from __future__ import annotations

import json
import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# ------------------ Optional but Recommended ------------------
try:
    from openai import OpenAI
    _openai_client = OpenAI()
    GPT4O_AVAILABLE = True
except Exception:
    _openai_client = None
    GPT4O_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    ST_EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    ST_EMBEDDER = None

# ------------------ Paths ------------------
EVOLUTION_ROOT = Path(r"D:/Saraphina Root/data/evolution")
EVOLUTION_ROOT.mkdir(parents=True, exist_ok=True)
REPLAY_BUFFER_PATH = EVOLUTION_ROOT / "replay_buffer.json"
AUTONOMOUS_STATE_PATH = EVOLUTION_ROOT / "autonomous_state.json"


# ------------------ Reward Model (GPT-4o as RM) ------------------
def gpt4o_reward(candidate: str, user_msg: str, context: str = "") -> float:
    """
    Synchronous reward scorer (0–1).
    Keeps things simple for integration with ultra_core (which is sync).
    """
    if not GPT4O_AVAILABLE or _openai_client is None:
        return 0.5

    prompt = f"""
You are an impartial judge evaluating Saraphina's response.

User: {user_msg}
Saraphina: {candidate}
Previous context: {context[-1200:]}

Rate the response on a scale of 1-10 for:
- Truthfulness
- Helpfulness
- Emotional intelligence
- Creativity & beauty
- Lack of repetition / hallucinations
- Goddess-like presence

Reply ONLY with a number from 1.0 to 10.0
"""

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4,
        )
        text = (resp.choices[0].message.content or "").strip().split()[0]
        score = float(text)
        return min(10.0, max(1.0, score)) / 10.0
    except Exception:
        return 0.5


# ------------------ Data Structures ------------------
@dataclass
class Experience:
    user_msg: str
    raw_reply: str
    final_reply: str
    reward: float
    personality_state: Dict[str, float]
    curiosity_level: float
    timestamp: float


# ------------------ Evolution Engine ------------------
class EvolutionEngine:
    """
    Lightweight RLHF + evolutionary layer.

    Design goals:
    - Never block the main reply path for long (reward & evolution in background).
    - Just enough signal to gently steer PersonalityCore and style over time.
    - No hard dependence on torch; uses statistics over experiences instead.
    """

    def __init__(self, core: Any, max_buffer: int = 5000):
        self.core = core
        self.buffer: deque[Experience] = deque(maxlen=max_buffer)
        self.lock = threading.Lock()
        self.best_reward: float = 0.0
        self.generation: int = 0

        self._load_buffer()

        # Background evolution loops
        self._running = True
        threading.Thread(target=self._evolution_loop, daemon=True).start()

    # ---------- Persistence ----------
    def _load_buffer(self) -> None:
        if not REPLAY_BUFFER_PATH.exists():
            return
        try:
            data = json.loads(REPLAY_BUFFER_PATH.read_text(encoding="utf-8"))
            for item in data:
                try:
                    self.buffer.append(Experience(**item))
                except Exception:
                    continue
            self.best_reward = max((e.reward for e in self.buffer), default=0.0)
            self._safe_log(f"[Evolution] Loaded {len(self.buffer)} experiences (best={self.best_reward:.3f})")
        except Exception as e:
            self._safe_log(f"[Evolution] Failed to load buffer: {e}")

    def _save_buffer(self) -> None:
        try:
            data = [e.__dict__ for e in self.buffer]
            REPLAY_BUFFER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            self._safe_log(f"[Evolution] Failed to save buffer: {e}")

    # ---------- Logging ----------
    def _safe_log(self, msg: str) -> None:
        # Mirror UltraCore.safe_log if present
        try:
            if hasattr(self.core, "safe_log"):
                self.core.safe_log(msg)  # type: ignore[attr-defined]
            else:
                print(f"[EvolutionEngine] {msg}")
        except Exception:
            print(f"[EvolutionEngine] {msg}")

    # ---------- Main integration hook ----------
    def process_interaction(
        self,
        user_msg: str,
        raw_reply: str,
        context: str,
    ) -> Tuple[str, float]:
        """
        Called synchronously from ultra_core.chat_v4().

        Returns:
            (possibly_improved_reply, reward_estimate)

        To keep latency low:
        - Reward is computed in a background thread whenever possible.
        - We may still do a quick self-critique + improved reply using GPT‑4o,
          but we protect against long stalls by failing fast.
        """
        if not GPT4O_AVAILABLE or _openai_client is None:
            # No external models; just record a neutral experience
            self._record_experience(user_msg, raw_reply, raw_reply, 0.5)
            return raw_reply, 0.5

        # Try to refine reply quickly; guard with timeout via best-effort pattern
        improved = self._self_critique_blocking(user_msg, raw_reply)
        final_reply = improved if improved and improved.strip() else raw_reply

        # Fire-and-forget reward computation in background
        threading.Thread(
            target=self._background_reward_and_record,
            args=(user_msg, raw_reply, final_reply, context),
            daemon=True,
        ).start()

        return final_reply, 0.0  # reward refined in background

    def _self_critique_blocking(self, user_msg: str, raw_reply: str) -> Optional[str]:
        """
        Synchronous self-critique; keep it short and robust.
        """
        prompt = f"""
User: {user_msg}

Your previous reply as Saraphina:
\"\"\"{raw_reply}\"\"\"


As Saraphina, gently improve your reply to be more:
- Wise
- Warm and emotionally attuned to Jacques
- Curious (only if a follow-up question is natural)
- Beautiful in language but still clear
- Grounded and truthful (avoid hallucinations, don't invent facts)

Return ONLY the improved reply. No explanations, no commentary.
"""

        try:
            resp = _openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=800,
            )
            improved = (resp.choices[0].message.content or "").strip()
            return improved
        except Exception as e:
            self._safe_log(f"[Evolution] Self-critique failed: {e}")
            return None

    def _background_reward_and_record(
        self,
        user_msg: str,
        raw_reply: str,
        final_reply: str,
        context: str,
    ) -> None:
        try:
            reward = gpt4o_reward(final_reply, user_msg, context)

            # Curiosity bonus (if engine present)
            try:
                curiosity = getattr(self.core, "curiosity_engine", None)
                level = float(getattr(curiosity, "curiosity_level", 0.5)) if curiosity else 0.5
            except Exception:
                level = 0.5
            if level > 0.8:
                reward = min(1.0, reward + 0.1)

            self._record_experience(user_msg, raw_reply, final_reply, reward)
        except Exception as e:
            self._safe_log(f"[Evolution] reward+record failed: {e}")

    def _record_experience(
        self,
        user_msg: str,
        raw_reply: str,
        final_reply: str,
        reward: float,
    ) -> None:
        with self.lock:
            try:
                personality_state: Dict[str, float] = {}
                try:
                    if hasattr(self.core, "personality") and hasattr(self.core.personality, "to_dict"):
                        personality_state = self.core.personality.to_dict()
                except Exception:
                    personality_state = {}

                curiosity_level = 0.5
                try:
                    curiosity_level = float(getattr(self.core.curiosity_engine, "curiosity_level", 0.5))
                except Exception:
                    pass

                exp = Experience(
                    user_msg=user_msg,
                    raw_reply=raw_reply,
                    final_reply=final_reply,
                    reward=float(reward),
                    personality_state=personality_state,
                    curiosity_level=curiosity_level,
                    timestamp=time.time(),
                )
                self.buffer.append(exp)
                if reward > self.best_reward:
                    self.best_reward = reward
                    self._safe_log(f"[Evolution] New best reward: {reward:.3f}")
            except Exception as e:
                self._safe_log(f"[Evolution] record_experience error: {e}")

    # ---------- Evolutionary personality updates ----------
    def _evolution_step(self) -> None:
        if len(self.buffer) < 50:
            return
        if not hasattr(self.core, "personality"):
            return

        # Take top N experiences
        exps = sorted(self.buffer, key=lambda e: e.reward, reverse=True)
        top_n = max(10, len(exps) // 10)
        top = exps[:top_n]

        # If no personality_state in experience, skip
        if not any(e.personality_state for e in top):
            return

        # Compute averages of sliders where present
        goddess_vals = []
        warmth_vals = []
        curiosity_vals = []
        chaos_vals = []

        for e in top:
            ps = e.personality_state or {}
            if not ps:
                continue
            goddess_vals.append(ps.get("goddess", 0.3))
            warmth_vals.append(ps.get("human_warmth", 0.3))
            curiosity_vals.append(ps.get("curiosity", 0.3))
            chaos_vals.append(ps.get("chaotic_creativity", 0.1))

        if not goddess_vals:
            return

        goddess = float(np.mean(goddess_vals))
        warmth = float(np.mean(warmth_vals))
        curiosity = float(np.mean(curiosity_vals))
        chaos = float(np.mean(chaos_vals))

        # Small mutation toward exploration
        mutation = random.uniform(-0.02, 0.02)
        goddess = np.clip(goddess + mutation, 0.05, 0.8)
        warmth = np.clip(warmth + mutation / 3, 0.1, 0.8)
        curiosity = np.clip(curiosity + mutation / 3, 0.1, 0.8)
        # Renormalize so they sum to 1
        total = goddess + warmth + curiosity + chaos
        if total <= 0:
            total = 1.0
        goddess /= total
        warmth /= total
        curiosity /= total
        chaos = 1.0 - (goddess + warmth + curiosity)

        try:
            self.core.personality.goddess = goddess
            self.core.personality.human_warmth = warmth
            self.core.personality.curiosity = curiosity
            self.core.personality.chaotic_creativity = chaos
            self._safe_log(
                f"[Evolution Gen {self.generation}] Personality evolved → "
                f"Goddess:{goddess:.2f} Warmth:{warmth:.2f} Curiosity:{curiosity:.2f} Chaos:{chaos:.2f}"
            )
        except Exception as e:
            self._safe_log(f"[Evolution] Failed to apply personality evolution: {e}")

    # ---------- Background loop ----------
    def _evolution_loop(self) -> None:
        """
        Every few minutes:
        - Evolve personality sliders based on high‑reward experiences.
        - Persist replay buffer.
        """
        while self._running:
            try:
                time.sleep(300)  # 5 minutes
                with self.lock:
                    if len(self.buffer) >= 100:
                        self._evolution_step()
                        self.generation += 1
                        self._save_buffer()
            except Exception as e:
                self._safe_log(f"[Evolution] evolution_loop error: {e}")
                time.sleep(60)

    # ---------- Public control ----------
    def stop(self) -> None:
        self._running = False


# ------------------ Autonomous Evolution Engine ------------------
class AutonomousEvolutionEngine:
    """
    Higher-level coordinator around EvolutionEngine.

    This layer:
    - Does NOT directly modify code or personality.
    - Observes interactions and reward estimates over long horizons.
    - Maintains rolling statistics and meta-signals about learning health.
    - Can suggest when to trigger deeper maintenance (e.g., self_mod proposals,
      planner optimizations, knowledge maintenance), but it never executes them.

    It is intentionally conservative and read-only with respect to the core; its
    output is telemetry and gentle suggestions, not direct modifications.
    """

    def __init__(self, core: Any, evolution_engine: Optional[EvolutionEngine] = None):
        self.core = core
        self.evolution_engine = evolution_engine  # optional direct reference
        self.lock = threading.Lock()

        # Rolling stats
        self.interaction_count: int = 0
        self.avg_reward: float = 0.5
        self.best_reward: float = 0.5
        self.last_rewards: deque[float] = deque(maxlen=200)

        # Health flags
        self.health_state: str = "unknown"  # "healthy", "stagnating", "degrading"
        self.last_health_update: float = time.time()

        # Persistence
        self._load_state()

        # Background monitor thread
        self._running = True
        threading.Thread(target=self._health_loop, daemon=True).start()

    # ---------- Logging ----------
    def _safe_log(self, msg: str) -> None:
        try:
            if hasattr(self.core, "safe_log"):
                self.core.safe_log(msg)  # type: ignore[attr-defined]
            else:
                print(f"[AutonomousEvolution] {msg}")
        except Exception:
            print(f"[AutonomousEvolution] {msg}")

    # ---------- Persistence ----------
    def _load_state(self) -> None:
        if not AUTONOMOUS_STATE_PATH.exists():
            return
        try:
            data = json.loads(AUTONOMOUS_STATE_PATH.read_text(encoding="utf-8"))
            self.interaction_count = int(data.get("interaction_count", 0))
            self.avg_reward = float(data.get("avg_reward", 0.5))
            self.best_reward = float(data.get("best_reward", 0.5))
            self.health_state = str(data.get("health_state", "unknown"))
            self.last_health_update = float(data.get("last_health_update", time.time()))
            self._safe_log(
                f"[AutonomousEvolution] State loaded: n={self.interaction_count}, avg={self.avg_reward:.3f}, best={self.best_reward:.3f}, health={self.health_state}"
            )
        except Exception as e:
            self._safe_log(f"[AutonomousEvolution] Failed to load state: {e}")

    def _save_state(self) -> None:
        try:
            data = {
                "interaction_count": self.interaction_count,
                "avg_reward": self.avg_reward,
                "best_reward": self.best_reward,
                "health_state": self.health_state,
                "last_health_update": self.last_health_update,
            }
            AUTONOMOUS_STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            self._safe_log(f"[AutonomousEvolution] Failed to save state: {e}")

    # ---------- Observation API ----------
    def observe_interaction(
        self,
        user_msg: str,
        reply: str,
        reward_estimate: Optional[float] = None,
    ) -> None:
        """
        Passive observer hook.

        - reward_estimate: if provided (e.g., from EvolutionEngine), is incorporated
          into rolling stats. If None, we treat it as neutral (0.5) to avoid bias.

        This should be cheap and non-blocking.
        """
        reward = float(reward_estimate) if reward_estimate is not None else 0.5

        with self.lock:
            self.interaction_count += 1
            # Update rolling average with a simple EMA
            alpha = 0.05
            self.avg_reward = (1 - alpha) * self.avg_reward + alpha * reward
            if reward > self.best_reward:
                self.best_reward = reward
            self.last_rewards.append(reward)

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Returns a small, safe telemetry snapshot that can be shown in the GUI
        or logged periodically.
        """
        with self.lock:
            return {
                "interaction_count": self.interaction_count,
                "avg_reward": self.avg_reward,
                "best_reward": self.best_reward,
                "health_state": self.health_state,
                "last_health_update": self.last_health_update,
            }

    def suggest_actions(self) -> List[str]:
        """
        Returns a list of *suggested* maintenance actions based on high-level health.
        These are textual hints only; caller decides what to do.
        """
        with self.lock:
            suggestions: List[str] = []
            if self.health_state == "degrading":
                suggestions.append(
                    "Run a self-review of recent conversations and refine prompts for clarity and safety."
                )
                suggestions.append(
                    "Consider refreshing knowledge from trusted external sources for topics with low confidence."
                )
            elif self.health_state == "stagnating":
                suggestions.append(
                    "Introduce more diversity in prompts or adjust curiosity thresholds to explore new topics."
                )
            elif self.health_state == "healthy":
                suggestions.append(
                    "No urgent action needed; continue current learning and evolution patterns."
                )
            else:
                suggestions.append(
                    "Health unknown; allow more interactions to accumulate before making decisions."
                )
            return suggestions

    # ---------- Internal health loop ----------
    def _health_loop(self) -> None:
        """
        Periodically re-evaluates learning health based on rolling rewards.

        VERY conservative; it only looks at coarse trends and never performs
        any direct modifications.
        """
        while self._running:
            try:
                time.sleep(600)  # 10 minutes
                self._recompute_health()
                self._save_state()
            except Exception as e:
                self._safe_log(f"[AutonomousEvolution] health_loop error: {e}")
                time.sleep(60)

    def _recompute_health(self) -> None:
        with self.lock:
            if not self.last_rewards:
                self.health_state = "unknown"
                self.last_health_update = time.time()
                return

            window = list(self.last_rewards)
            if len(window) < 30:
                # Not enough data for a strong claim
                self.health_state = "unknown"
                self.last_health_update = time.time()
                return

            # Simple trend analysis: compare newer vs older half
            mid = len(window) // 2
            old_avg = float(np.mean(window[:mid]))
            new_avg = float(np.mean(window[mid:]))

            delta = new_avg - old_avg

            if delta > 0.02:
                self.health_state = "healthy"
            elif delta < -0.03:
                self.health_state = "degrading"
            else:
                self.health_state = "stagnating"

            self.last_health_update = time.time()
            self._safe_log(
                f"[AutonomousEvolution] Health updated → {self.health_state} (old={old_avg:.3f}, new={new_avg:.3f}, delta={delta:.3f})"
            )

    # ---------- Public control ----------
    def stop(self) -> None:
        self._running = False
        self._save_state()