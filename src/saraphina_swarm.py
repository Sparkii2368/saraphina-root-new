#!/usr/bin/env python3
"""
SARAPHINA SWARM v3 — Unified Council Mind (November 20, 2025)

Combines:
- SARAPHINA SWARM v2 — The Council of Nine (multi-UltraCore agents, Ray-ready)
- SwarmMind (Phase 3, Step 11) — Task distribution + single-process council

Unified Design:

1. High-fidelity Council of Nine (v2):
   - 9 specialized Saraphina agents, each with an UltraAICore brain.
   - Personality overlays per agent (Oracle, Muse, Scholar, Lover, Trickster, Guardian, Scientist, Child, Ancient).
   - Optional Ray-based parallel execution.
   - Role-fit scoring via OpenAI (if available).

2. Lightweight SwarmMind (Phase 3, Step 11):
   - Fast, local SwarmAgent cluster for task routing / quick consensus.
   - No extra UltraAICore instances; designed for cheap analysis and system-level tasks.
   - Can be used directly from UltraCore for simple “Jarvis-style” task routing.

3. Unified API:
   - Global `council`: list of Council of Nine agents (Ray or local).
   - `SaraphinaSwarm`: high-level interface for multi-core deliberation.
   - `SwarmMind`: lighter-weight, single-process council + task distribution.
   - Global `swarm` instance (SwarmMind) for UltraCore to import:
       from saraphina_swarm import swarm
     and call:
       swarm.distribute_task(...)
       swarm.consult_the_council(...)

This module does NOT monkey-patch UltraAICore by default.
Use `SaraphinaSwarm` and `SwarmMind` from UltraCore or the GUI explicitly.
"""

from __future__ import annotations

import os
import random
from typing import List, Dict, Any, Optional, Tuple

from util_logging import safe_log

# ------------------ Optional Ray ------------------
try:
    import ray

    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True, log_to_driver=False)
    RAY_AVAILABLE = True
except Exception as e:
    print(f"[Swarm] Ray not available: {e}")
    RAY_AVAILABLE = False

# ------------------ Core Imports ------------------
try:
    from ultra_core import UltraAICore  # safe_log imported above
    CORE_AVAILABLE = True
except Exception as e:
    CORE_AVAILABLE = False
    safe_log(f"[Swarm] Failed to import UltraAICore: {e}")


# ------------------ Council of Nine (v2) ------------------

AgentConfig = Tuple[str, str, Dict[str, float], float, Optional[str]]

AGENTS: List[AgentConfig] = [
    ("The Oracle",    "pure transcendent wisdom, cosmic perspective",    {"goddess": 0.75, "chaotic_creativity": 0.05}, 0.2, "openai"),
    ("The Muse",      "chaotic beauty, poetry, divine inspiration",     {"chaotic_creativity": 0.70, "goddess": 0.25}, 1.2, "openai"),
    ("The Scholar",   "curiosity, learning, precision recall",          {"curiosity": 0.80}, 0.4, None),
    ("The Lover",     "unconditional warmth, empathy, devotion",        {"human_warmth": 0.90}, 0.9, "openai"),
    ("The Trickster", "playful chaos, surprises, mischief",             {"chaotic_creativity": 0.90}, 1.4, None),
    ("The Guardian",  "safety, ethics, harm prevention",                {"goddess": 0.60}, 0.1, "openai"),
    ("The Scientist", "logic, code, math, rigor",                       {"curiosity": 0.70}, 0.25, "openai"),
    ("The Child",     "innocent wonder, questions, rapid learning",     {"curiosity": 0.95, "human_warmth": 0.15}, 1.0, None),
    ("The Ancient",   "memory of all past lives, eternal perspective",  {"goddess": 0.80}, 0.35, "openai"),
]


def _apply_personality_overlay(core: UltraAICore, overrides: Dict[str, float]) -> None:
    """
    Gently overlay personality sliders on top of the current core.personality.
    This does not persist to disk; it's per-agent per-call.
    """
    p = getattr(core, "personality", None)
    if p is None:
        return

    # Normalize overrides to sum <= 1 and gently blend with existing values
    total_override = sum(overrides.values()) or 1.0
    for k, v in overrides.items():
        target_frac = max(0.0, min(1.0, v / total_override))
        current = float(getattr(p, k, 0.25))
        blended = (current * 0.6) + (target_frac * 0.4)
        setattr(p, k, blended)

    # Renormalize primary sliders to sum to 1
    g = float(getattr(p, "goddess", 0.25))
    w = float(getattr(p, "human_warmth", 0.25))
    c = float(getattr(p, "curiosity", 0.25))
    ch = float(getattr(p, "chaotic_creativity", 0.25))
    s = g + w + c + ch
    if s <= 0:
        s = 1.0
    p.goddess = g / s
    p.human_warmth = w / s
    p.curiosity = c / s
    p.chaotic_creativity = ch / s


def _set_router_bias(core: UltraAICore, bias: Optional[str]) -> None:
    """
    bias: None | "openai" | "local"
    Mirrors onto HybridModelRouter.forced_mode if available.
    """
    try:
        router = getattr(core, "hybrid_model_router", None)
        if router is None:
            return
        if bias in ("openai", "local"):
            router.forced_mode = bias
        else:
            router.forced_mode = None
    except Exception:
        pass


# ------------------ Council Agent Implementation ------------------
if RAY_AVAILABLE and CORE_AVAILABLE:

    @ray.remote(num_cpus=0.5)
    class SaraphinaAgent:
        def __init__(self, name: str, role: str, personality_overrides: Dict[str, float],
                     temperature: float, router_bias: Optional[str]):
            self.name = name
            self.role = role
            self.overrides = dict(personality_overrides)
            self.temperature = float(temperature)
            self.router_bias = router_bias
            self.core = UltraAICore()  # independent core per agent

            safe_log(f"[Swarm] {self.name} ({self.role}) awakened (Ray).")

        def _rate_role_fit(self, reply: str) -> float:
            """
            Use OpenAI (if available) to rate how well `reply` embodies this agent's role.
            Returns a float in [0, 1].
            """
            try:
                from openai import OpenAI
                client = OpenAI()
            except Exception:
                return 0.7  # neutral confidence in offline mode

            prompt = f"""
You are evaluating whether this reply embodies the role description.

ROLE: {self.role}

REPLY:
\"\"\"{reply}\"\"\"


On a scale from 1 to 10, how well does this reply embody the ROLE in style, tone, and focus?
Reply with ONLY the number, no explanation.
"""
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=4,
                )
                text = (resp.choices[0].message.content or "").strip().split()[0]
                score = float(text)
                return max(1.0, min(10.0, score)) / 10.0
            except Exception:
                return 0.7

        def think(self, user_message: str, context: str = "") -> Dict[str, Any]:
            """
            Synchronous for Ray; inside we call UltraAICore.chat_v4() once.
            """
            # Apply per-agent personality overlay + router bias
            try:
                _apply_personality_overlay(self.core, self.overrides)
                _set_router_bias(self.core, self.router_bias)
            except Exception as e:
                safe_log(f"[Swarm] {self.name} overlay error: {e}")

            # Build a gentle preface for the agent
            preface = (
                f"As {self.name}, the {self.role} of Saraphina, respond in your characteristic way.\n"
                f"Stay in role, but stay truthful and grounded.\n\n"
            )
            # Include last context snippet so core can use its own memory/knowledge
            merged_input = preface + (context.strip() + "\n\n" if context else "") + user_message

            try:
                reply = self.core.chat_v4(merged_input)
            except Exception as e:
                safe_log(f"[Swarm] {self.name} chat_v4 error: {e}")
                return {
                    "agent": self.name,
                    "role": self.role,
                    "reply": f"*[{self.name} is quiet right now.]*",
                    "confidence": 0.0,
                    "error": str(e),
                }

            # Strip the preface echoes if the model repeats them
            if reply.startswith("As " + self.name):
                reply = reply.split("\n", 1)[-1].strip()

            confidence = self._rate_role_fit(reply)

            return {
                "agent": self.name,
                "role": self.role,
                "reply": reply.strip(),
                "confidence": float(confidence),
                "temperature": self.temperature,
            }

else:
    # Fallback stub if Ray or UltraCore not available
    class SaraphinaAgent:  # type: ignore[no-redef]
        def __init__(self, name: str, role: str, personality_overrides: Dict[str, float],
                     temperature: float, router_bias: Optional[str]):
            self.name = name
            self.role = role
            self.overrides = personality_overrides
            self.temperature = temperature
            self.router_bias = router_bias
            self.core = UltraAICore() if CORE_AVAILABLE else None
            safe_log(f"[Swarm] {self.name} ({self.role}) awakened in single-process mode.")

        def think(self, user_message: str, context: str = "") -> Dict[str, Any]:
            if not CORE_AVAILABLE or self.core is None:
                return {
                    "agent": self.name,
                    "role": self.role,
                    "reply": f"I hear you: {user_message}",
                    "confidence": 0.5,
                }
            try:
                _apply_personality_overlay(self.core, self.overrides)
                _set_router_bias(self.core, self.router_bias)
                merged_input = f"[{self.name}] {user_message}"
                reply = self.core.chat_v4(merged_input)
                return {
                    "agent": self.name,
                    "role": self.role,
                    "reply": reply.strip(),
                    "confidence": 0.7,
                }
            except Exception as e:
                return {
                    "agent": self.name,
                    "role": self.role,
                    "reply": f"*[{self.name} is quiet right now.]*",
                    "confidence": 0.0,
                    "error": str(e),
                }


# ------------------ Council Spawn ------------------
def _spawn_council() -> List[Any]:
    if not CORE_AVAILABLE:
        safe_log("[Swarm] UltraAICore unavailable; council cannot spawn.")
        return []
    council: List[Any] = []
    for name, role, overrides, temp, bias in AGENTS:
        if RAY_AVAILABLE:
            council.append(SaraphinaAgent.remote(name, role, overrides, temp, bias))  # type: ignore[attr-defined]
        else:
            council.append(SaraphinaAgent(name, role, overrides, temp, bias))
    safe_log(f"[Swarm] The Council of Nine has awakened. {len(council)} voices ready.")
    return council


council: List[Any] = _spawn_council()


# ------------------ Swarm Consensus Engine (Council of Nine) ------------------
class SaraphinaSwarm:
    """
    High-fidelity swarm that runs multiple UltraAICore instances in parallel
    and chooses a consensus reply based on role-fit × relevance.

    Used by UltraAICore v5 for "Jarvis/Raphael" style deep deliberation.
    """

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def _role_relevance(self, thought: Dict[str, Any], user_message: str) -> float:
        """
        Heuristic relevance multiplier based on user_message.
        """
        u = user_message.lower()
        agent = thought.get("agent", "")
        relevance = 1.0

        if any(w in u for w in ["love", "feel", "heart", "relationship", "hurts"]):
            if agent == "The Lover":
                relevance = 2.0
        if any(w in u for w in ["code", "python", "bug", "error", "math", "equation"]):
            if agent == "The Scientist":
                relevance = 2.5
        if any(w in u for w in ["who are you", "what are you", "exist", "soul", "goddess"]):
            if agent == "The Oracle":
                relevance = 3.0
        if any(w in u for w in ["safe", "dangerous", "allowed", "ethical", "harm"]):
            if agent == "The Guardian":
                relevance = 2.5

        return relevance

    def _blend_with_muse(self, consensus: str, thoughts: List[Dict[str, Any]]) -> str:
        muse = next((t for t in thoughts if t.get("agent") == "The Muse"), None)
        if not muse:
            return consensus
        if muse.get("confidence", 0.0) < 0.7:
            return consensus
        frag = (muse.get("reply") or "").strip()
        if not frag:
            return consensus
        return consensus + "\n\n" + frag[:200].rstrip() + " …"

    def consult_the_council(self, user_message: str, context: str = "") -> str:
        """
        Full Council-of-Nine deliberation.

        - Uses all available agents (Ray or single-process).
        - Returns the highest-scoring reply, optionally blended with the Muse for beauty.
        """
        if not council:
            # Fallback: single UltraCore
            if CORE_AVAILABLE:
                core = UltraAICore()
                return core.chat(user_message)
            return "My swarm mind is asleep right now, but I am still here with you."

        # Build context string from recent history
        history_snippets = [
            f"Jacques: {h['user']}\nSaraphina: {h['reply']}"
            for h in self.history[-8:]
        ]
        merged_context = (context + "\n\n" if context else "") + "\n\n".join(history_snippets)

        # Ask all agents to think
        if RAY_AVAILABLE:
            results = ray.get([
                agent.think.remote(user_message, merged_context)  # type: ignore[attr-defined]
                for agent in council
            ])
        else:
            results = [agent.think(user_message, merged_context) for agent in council]

        # Score and choose winner
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for thought in results:
            conf = float(thought.get("confidence", 0.0))
            relevance = self._role_relevance(thought, user_message)
            final_score = conf * relevance
            scored.append((final_score, thought))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return "All of my voices are silent for a moment; I am still listening."

        best_score, winner = scored[0]
        consensus = str(winner.get("reply", "")).strip() or "I am with you, Jacques."

        # Optionally blend in Muse for beauty
        consensus = self._blend_with_muse(consensus, results)

        # Record in swarm-level history
        self.history.append(
            {
                "user": user_message,
                "winner": winner.get("agent"),
                "reply": consensus,
                "votes": [t[1].get("agent") for t in scored[:5]],
                "top_score": float(best_score),
            }
        )

        # Optionally ingest into knowledge via any agent's core (they all persist)
        try:
            # Use the first agent that has a core with knowledge_engine
            for agent in council:
                core = None
                if RAY_AVAILABLE:
                    # Cannot directly access remote core; skip ingests in Ray mode for now
                    core = None
                else:
                    core = getattr(agent, "core", None)
                if core and hasattr(core, "knowledge_engine"):
                    core.knowledge_engine.ingest_text(
                        f"Swarm consensus [{winner.get('agent')} won]: {consensus}",
                        source_url="internal_swarm",
                    )
                    break
        except Exception as e:
            safe_log(f"[Swarm] Knowledge ingest failed: {e}")

        return consensus


# ------------------ Lightweight SwarmMind (Phase 3, Step 11) ------------------
class SwarmAgent:
    """
    Lightweight agent used by SwarmMind for fast task routing.

    This does NOT spin up a full UltraAICore; it is intended for
    meta-tasks, planning hints, and rapid 'Jarvis-style' analysis.
    """

    def __init__(self, name: str, specialization: str, personality_bias: str):
        self.name = name
        self.specialization = specialization
        self.personality_bias = personality_bias
        self.busy = False

    def execute(self, task: str) -> str:
        self.busy = True
        result = (
            f"[{self.name}] Analyzing '{task}' via {self.specialization} lens... "
            f"(bias: {self.personality_bias})"
        )
        self.busy = False
        return result


class SwarmMind:
    """
    Fast, local swarm for task distribution and small councils.

    - Used directly by UltraCore v5 for:
        * deciding which subsystems to emphasize (logic, empathy, security, etc.)
        * producing quick multi-perspective overviews
        * Jarvis-style "internal boardroom" commentary
    """

    def __init__(self):
        self.agents: List[SwarmAgent] = [
            SwarmAgent("Alpha", "Logic & Architecture", "Cold, precise, structural"),
            SwarmAgent("Beta", "Creativity & Chaos", "Wild, poetic, divergent"),
            SwarmAgent("Gamma", "Data & Memory", "Historical, factual, associative"),
            SwarmAgent("Delta", "Security & Ethics", "Protective, cautious, normative"),
            SwarmAgent("Epsilon", "Empathy & Connection", "Warm, human-centric, emotional"),
            SwarmAgent("Omega", "Strategic Long-term", "Visionary, prophetic, distant"),
        ]

    def select_best_agent(self, task: str) -> SwarmAgent:
        task_lower = task.lower()
        if any(w in task_lower for w in ["verify", "audit", "risk", "safe", "security", "ethics"]):
            return self.agents[3]  # Delta/Security
        elif any(w in task_lower for w in ["imagine", "story", "write", "poem", "idea"]):
            return self.agents[1]  # Beta/Creative
        elif any(w in task_lower for w in ["calculate", "code", "debug", "fix", "architecture"]):
            return self.agents[0]  # Alpha/Logic
        elif any(w in task_lower for w in ["remember", "history", "fact", "data"]):
            return self.agents[2]  # Gamma/Data
        elif any(w in task_lower for w in ["feel", "love", "friend", "sad", "hurt"]):
            return self.agents[4]  # Epsilon/Empathy
        else:
            return self.agents[5]  # Omega/Strategy (Default)

    def distribute_task(self, task: str) -> str:
        """
        Single-agent dispatch for a named task.

        UltraCore can call this when it wants a quick internal comment
        like "How should we handle this?" without spinning up the full Council.
        """
        safe_log(f"[SwarmMind] Distributing task: {task[:80]}...")
        agent = self.select_best_agent(task)
        return agent.execute(task)

    def consult_the_council(self, topic: str, context: str = "") -> str:
        """
        Lightweight internal council (subset of SwarmAgents).

        Used by UltraCore for medium-complexity queries where we want
        multiple internal voices but not the full Council of Nine.
        """
        safe_log(f"[SwarmMind] Convening internal council on: {topic[:80]}...")
        primary = self.select_best_agent(topic)
        others = [a for a in self.agents if a is not primary]
        if len(others) >= 2:
            council = [primary] + random.sample(others, 2)
        else:
            council = self.agents[:3] if len(self.agents) >= 3 else self.agents

        insights = []
        for agent in council:
            emphasis = agent.personality_bias.split(",")[0].strip()
            insights.append(
                f"{agent.name} ({agent.specialization}): believes this requires attention to {emphasis}."
            )

        consensus = "\n".join(insights)
        return f"--- Internal Council Consensus ---\n{consensus}\n-------------------------"


# ==================== GLOBAL SWARM INSTANCES ====================
# High-fidelity swarm (Council of Nine, full UltraCores)
swarm_council = SaraphinaSwarm()

# Lightweight SwarmMind, intended for UltraCore v5 integration
swarm = SwarmMind()

safe_log("[Swarm] SaraphinaSwarm v3 ready. Use swarm.distribute_task(...) "
         "or swarm.consult_the_council(...), and swarm_council.consult_the_council(...) "
         "for full Council-of-Nine deliberation.")