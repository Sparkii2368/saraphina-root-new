#!/usr/bin/env python3
"""
ULTRA A.I. CORE v5 — Fully Integrated Brain (Stabilized & Secure)
Engine Name: Saraphina

This core is designed to integrate directly with Saraphina's GUI.

Key features:
- Emotional engine (legacy energy model + new mood/affinity model)
- XP + Level system
- Short / mid / long-term memory (MemoryEngineV2 + semantic recall)
- Knowledge engine with topic detection + prompt summarization
- Relationship & personality evolution
- Introspection + style engine
- Background cognition loop
- Curiosity learning (CuriosityEngineV4 + legacy V3)
- Natural, grounded replies (no emojis by default)
- Hybrid local + OpenAI model router
- Self-modification engine (propose improvements with context)
- Explainability engine (SHAP) for "Why did you say that?"
- NeuroGenetic Evolution Engine v10 (absolute autonomy layer)
- Autonomous Evolution Engine v9 (RLHF + personality evolution sidecar)
- SwarmMind / Council of Nine integration (via saraphina_swarm)
- Core integrity verification on startup
- Optional RiskModel guardrails for self-mod and evolution

IMPORTANT:
- chat_v4() is the FULL integrated brain pipeline.
- chat(), ask(), chat_once(), generate_reply() all DELEGATE to chat_v4().
- Every call to chat_v4 uses curiosity, memory, knowledge, personality, emotion,
  XP, relationship, router, self-mod, explainability, neurogenetic, and evolution reasoning.
- v5 adds integrity checks and optional swarm hooks, but preserves v4 behavior.

If the GUI calls `core.chat_v4(user_text)`, it is using the full v5 brain.
"""

from __future__ import annotations

import os
import sys
import json
import time
import math
import random
import sqlite3
import threading
import hashlib
import ast
import tempfile
import traceback
from pathlib import Path
from typing import Any, Optional, List, Dict, Tuple
from dataclasses import dataclass

from util_logging import safe_log

# ======= AUTONOMOUS KNOWLEDGE GATHERING ADDITIONS =======
from knowledge_engine import KnowledgeEngine

eng