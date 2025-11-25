#!/usr/bin/env python3
"""
Saraphina — Goddess Dashboard GUI
---------------------------------
Cyber-Goddess Neon Hologram • Spaceship Flight Deck Layout

Features (wired to UltraAICore):
- Bottom-center chat console (UltraAICore.chat_v4 only).
- Top System HUD (CPU, RAM, router mode, XP/Level-ish tick).
- Left column: Personality, Emotion, Curiosity, Knowledge panels.
- Right column: Memory, Hybrid Model Router, Self-Upgrade, Voice panels.
- Panels show live data from:
  - PersonalityCore
  - EmotionEngineV2 + EmotionalEngine (legacy energy)
  - CuriosityEngineV4
  - MemoryEngineV2 (short/mid/long-term count)
  - HybridModelRouter (AUTO / LOCAL / OPENAI, last_mode)
  - KnowledgeEngine (clipboard ingest)
  - SelfModificationEngine (proposals, apply/view)
- Keeps:
  - ElevenLabs / pyttsx3 voice stack
  - STT engine & wake word
  - SelfModificationEngine hooks (patch/upgrade/explain)
  - Background learning threads
  - Config persistence and graceful shutdown
- Explainability viewer ("Why?" button) for UltraCore.last_explanation
"""

from __future__ import annotations

import os
import sys
import threading
import queue
import time
import random
import json
import logging
from pathlib import Path
from typing import Optional, Any, Callable

# =============================
# Core helper: alias patching
# =============================
def _sara_patch_core_aliases(core: Any) -> Any:
    """
    Ensure UltraAICore exposes .ultra, .core, and .ai for legacy paths.
    """
    try:
        core.ultra = core
    except Exception:
        pass
    try:
        if not hasattr(core, "core"):
            core.core = core
    except Exception:
        pass
    try:
        core.ai = core
    except Exception:
        pass
    return core

# =============================
# Project paths & logging
# =============================
IS_WINDOWS = sys.platform.startswith("win")
PROJECT_ROOT = Path(r"D:\Saraphina Root") if IS_WINDOWS else Path(__file__).parent.resolve()
SRC_DIR = PROJECT_ROOT / "src"

# Make sure src is on sys.path so ultra_core.py is importable
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if SRC_DIR.exists():
    os.chdir(str(SRC_DIR))

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "saraphina_gui.log"

# Base logger
root_logger = logging.getLogger()
for h in list(root_logger.handlers):
    root_logger.removeHandler(h)
root_logger.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
_fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
_fh.setFormatter(_fmt)
_fh.setLevel(logging.DEBUG)
root_logger.addHandler(_fh)
logger = logging.getLogger("SaraphinaGUI")

# =============================
# Simple .env loader
# =============================
def _sara_apply_env():
    """
    Very small, opinionated .env loader limited to a safe allow-list.
    Hard-wired to D:\\Saraphina Root\\.env.
    """
    env_path = PROJECT_ROOT.joinpath(".env")
    if not env_path.exists():
        logger.info("[ENV] No .env found at %s", env_path)
        return
    allow = {
        "ELEVENLABS_API_KEY", "ELEVEN_API_KEY", "ELEVEN_VOICE_ID",
        "OPENAI_API_KEY",
        "SELF_MOD_ENABLE", "SELF_MOD_OWNER_TOKEN", "SELF_MOD_DEPLOY_TOKEN", "SELF_MOD_SECRET",
        "SARA_THEME_ACCENT",
    }
    try:
        text = env_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.error("[ENV] Failed reading .env: %s", e)
        return
    applied = {}
    ignored = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'").strip('"')
        if not v:
            continue
        if k not in allow:
            ignored.append(k)
            continue
        os.environ[k] = v
        masked = v if len(v) <= 8 else (v[:4] + "..." + v[-2:])
        applied[k] = masked
    logger.info("[ENV] Applied keys: %s", list(applied.keys()))
    if ignored:
        logger.warning("[ENV] Ignored keys (not in allow-list): %s", ignored)

_sara_apply_env()

# Provide default voice id if not set
if not os.getenv("ELEVEN_VOICE_ID"):
    os.environ["ELEVEN_VOICE_ID"] = "9FVjbo4C2Q6BidfZSeno"

# =============================
# Temp directory management
# =============================
TEMP_DIR = os.getenv("SARAPHINA_TEMP_DIR", "").strip()
if TEMP_DIR:
    TEMP_DIR = Path(TEMP_DIR).resolve()
else:
    candidate = PROJECT_ROOT / "temp_real"
    TEMP_DIR = candidate if candidate.exists() else (Path(__file__).parent / "temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
for k in ("TEMP", "TMP"):
    os.environ[k] = str(TEMP_DIR)
logger.info("[TEMP] Using temp dir: %s", TEMP_DIR)

# =============================
# Optional psutil
# =============================
try:
    import psutil  # type: ignore
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False
    logger.warning("psutil not available; CPU/RAM monitor will show limited info")

# =============================
# Tkinter GUI toolkit
# =============================
try:
    import tkinter as tk  # type: ignore
    from tkinter import ttk, scrolledtext, messagebox  # type: ignore
except Exception as e:
    logger.critical("Tkinter not available: %s", e)
    raise

# =============================
# Speech recognition for STT
# =============================
try:
    import speech_recognition as sr  # type: ignore
    import soundfile  # type: ignore  # Ensure dependency for Whisper
    HAS_SR = True
except Exception as e:
    sr = None  # type: ignore
    HAS_SR = False
    logger.warning("speech_recognition or soundfile not available; STT disabled: %s", e)

# =============================
# ElevenLabs voice backend with pyttsx3 fallback (Upgraded to v2 API)
# =============================
VOICE_AVAILABLE = False
VOICE_IMPORT_ERROR: Optional[str] = None
ELEVEN_VOICE_ID = (os.getenv("ELEVEN_VOICE_ID") or "9FVjbo4C2Q6BidfZSeno").strip()
if not ELEVEN_VOICE_ID:
    ELEVEN_VOICE_ID = "9FVjbo4C2Q6BidfZSeno"  # fallback

def _noop_speak(text: str):
    logger.debug("[TTS NOOP] %s", (text[:120] + "..." if len(text) > 120 else text))

class _NoopVoiceManager:
    def stop_playback(self):
        ...
    def cleanup(self):
        ...
    def enqueue(self, *_a, **_k):
        ...

class _VoiceRequest:
    def __init__(
        self,
        text: str,
        voice_id: Optional[str] = None,
        priority: int = 5,
        truncate_length: int = 600,
    ):
        self.text = text
        self.voice_id = voice_id
        self.priority = priority
        self.truncate_length = truncate_length
        self.timestamp = time.time()
        self.attempts = 0

class ElevenHybridVoiceManager:
    """
    Queue-based ElevenLabs voice manager (v2 API).
    Uses simpleaudio if present for interruptible playback, otherwise falls back
    to elevenlabs.play.
    """
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._queue: "queue.PriorityQueue[tuple[int, float, _VoiceRequest]]" = queue.PriorityQueue()
        self._worker = threading.Thread(
            target=self._worker_loop, daemon=True, name="ElevenVoiceWorker"
        )
        self._stop_event = threading.Event()
        self._current_playback = None
        self._playback_lock = threading.Lock()
        self._simpleaudio = None
        self._eleven_client: Optional[Any] = None
        self._eleven_play: Optional[Callable[..., Any]] = None
        self._eleven_stream: Optional[Callable[..., Any]] = None
        self._setup_success = False
        self._init_sdk()
        if self._setup_success:
            self._worker.start()

    def _init_sdk(self):
        global VOICE_IMPORT_ERROR
        try:
            from elevenlabs import ElevenLabs, play, stream  # v2 API
            self._eleven_client = ElevenLabs(api_key=self._api_key)
            self._eleven_play = play
            self._eleven_stream = stream
            try:
                import simpleaudio as sa  # type: ignore
                self._simpleaudio = sa
                logger.info("simpleaudio available — using interruptible playback.")
            except Exception:
                self._simpleaudio = None
                logger.info("simpleaudio NOT available — falling back to elevenlabs.play")
            self._setup_success = True
            VOICE_IMPORT_ERROR = None
            logger.info("ElevenHybridVoiceManager initialized successfully (v2 API).")
        except Exception as e:
            VOICE_IMPORT_ERROR = f"ElevenLabs SDK init error: {e}"
            logger.error("%s", VOICE_IMPORT_ERROR)
            self._setup_success = False

    def stop_playback(self):
        with self._playback_lock:
            self._stop_event.set()
            play_obj = self._current_playback
            if play_obj and self._simpleaudio:
                try:
                    play_obj.stop()
                except Exception:
                    pass

    def cleanup(self):
        self.stop_playback()
        try:
            self._queue.put_nowait((9999, time.time(), _VoiceRequest("", priority=9999)))
        except Exception:
            pass

    def enqueue(self, req: _VoiceRequest):
        self._queue.put((req.priority, req.timestamp, req))

    def _truncate_text(self, text: str, length: int) -> str:
        if len(text) <= length:
            return text
        cut = text[:length].rsplit(".", 1)[0]
        if not cut.strip():
            cut = text[:length]
        return cut.strip() + " ... (truncated for speech)"

    def _worker_loop(self):
        backoff_base = 1.3
        logger.debug("Eleven voice worker loop started.")
        while not self._stop_event.is_set():
            try:
                try:
                    prio, ts, item = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                if not isinstance(item, _VoiceRequest):
                    continue
                item.attempts += 1
                text = item.text.strip()
                if not text:
                    continue
                text = self._truncate_text(text, item.truncate_length)
                # Generate audio (v2 API)
                audio_stream = None
                try:
                    if not self._eleven_client:
                        raise RuntimeError("ElevenLabs client unavailable")
                    audio_stream = self._eleven_client.text_to_speech.convert(
                        voice_id=(item.voice_id or ELEVEN_VOICE_ID),
                        text=text
                    )
                except Exception as e:
                    logger.warning("TTS generate failed (attempt %s): %s", item.attempts, e)
                    if item.attempts < 4:
                        delay = (backoff_base ** item.attempts) + random.uniform(0, 0.5)
                        time.sleep(delay)
                        self._queue.put((item.priority + 1, time.time(), item))
                        continue
                if self._stop_event.is_set():
                    continue
                # Playback
                played = False
                if self._simpleaudio:
                    try:
                        audio_bytes = b"".join(audio_stream)
                        import io
                        import wave
                        with io.BytesIO(audio_bytes) as bio:
                            with wave.open(bio, "rb") as wf:
                                channels = wf.getnchannels()
                                sampwidth = wf.getsampwidth()
                                framerate = wf.getframerate()
                                pcm_data = wf.readframes(wf.getnframes())
                        with self._playback_lock:
                            play_obj = self._simpleaudio.play_buffer(
                                pcm_data, channels, sampwidth, framerate
                            )
                            self._current_playback = play_obj
                        played = True
                    except Exception as e:
                        logger.debug("simpleaudio playback failed: %s", e)
                if not played and self._eleven_stream:
                    try:
                        self._eleven_stream(audio_stream)
                        played = True
                    except Exception as e:
                        logger.debug("elevenlabs.stream failed: %s", e)
            except Exception as e:
                logger.exception("TTS worker error: %s", e)
            finally:
                with self._playback_lock:
                    self._current_playback = None

def _init_voice() -> Any:
    global VOICE_AVAILABLE, VOICE_IMPORT_ERROR
    key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
    if key:
        vm = ElevenHybridVoiceManager(key)
        if vm._setup_success:
            VOICE_AVAILABLE = True
            return vm
    # Fallback to pyttsx3
    try:
        import pyttsx3  # type: ignore

        class PyttsxVoiceManager:
            def __init__(self):
                self.engine = pyttsx3.init()
                self._queue: "queue.PriorityQueue[tuple[int, float, _VoiceRequest]]" = queue.PriorityQueue()
                self._worker = threading.Thread(
                    target=self._worker_loop, daemon=True, name="PyttsxVoiceWorker"
                )
                self._stop_event = threading.Event()
                self._worker.start()

            def stop_playback(self):
                self.engine.stop()

            def cleanup(self):
                self._stop_event.set()
                self.engine.stop()

            def enqueue(self, req: _VoiceRequest):
                self._queue.put((req.priority, req.timestamp, req))

            def _truncate_text(self, text: str, length: int) -> str:
                if len(text) <= length:
                    return text
                cut = text[:length].rsplit(".", 1)[0]
                if not cut.strip():
                    cut = text[:length]
                return cut.strip() + " ... (truncated for speech)"

            def _worker_loop(self):
                logger.debug("Pyttsx voice worker loop started.")
                while not self._stop_event.is_set():
                    try:
                        prio, ts, item = self._queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    if not isinstance(item, _VoiceRequest):
                        continue
                    try:
                        text = item.text.strip()
                        if not text:
                            continue
                        text = self._truncate_text(text, item.truncate_length)
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        logger.exception("Pyttsx TTS worker error: %s", e)

        VOICE_AVAILABLE = True
        return PyttsxVoiceManager()
    except Exception as e:
        VOICE_IMPORT_ERROR = f"Pyttsx3 fallback failed: {e}"
        logger.error("Pyttsx3 fallback failed: %s", e)
        VOICE_AVAILABLE = False
        return _NoopVoiceManager()

VOICE_MANAGER = _init_voice()

def get_voice() -> Any:
    return VOICE_MANAGER

def speak_text(text: str):
    if not VOICE_AVAILABLE:
        _noop_speak(text)
        return
    VOICE_MANAGER.enqueue(_VoiceRequest(text=text))

# =============================
# Self-modification engine
# =============================
try:
    from self_modification_engine import SelfModificationEngine  # type: ignore
except Exception as e:
    logger.warning("SelfModificationEngine import failed: %s — using basic implementation", e)

    class SelfModificationEngine:  # type: ignore
        def __init__(self, *a, **k):
            logger.info("[SELF-MOD] Basic SelfModificationEngine active.")

        def inject_patch(self, target: str, code: str) -> str:
            try:
                target_path = PROJECT_ROOT.joinpath(target)
                with target_path.open("a", encoding="utf-8") as f:
                    f.write("\n# User-injected patch:\n" + code + "\n")
                return f"Patch appended to {target_path} with {len(code)} characters."
            except Exception as ex:
                return f"Patch failed: {ex}"

        def propose_improvement(self, target: str, spec: str) -> dict:
            return {
                "proposal_id": str(random.randint(1000, 9999)),
                "target": target,
                "summary": spec[:120],
            }

        def explain_command(self, code: str) -> str:
            return (
                f"Basic explanation: This code appears to be Python and has {len(code)} characters."
            )

        def list_proposals(self):
            return []

# =============================
# Basic subsystems (fallback)
# =============================
class BasicMetaOpt:
    def analyze_learning_health(self) -> dict:
        return {"overall_health": "ok"}

    def propose_optimizations(self) -> list:
        return ["Optimize loop efficiency."]

class BasicMemoryManager:
    def consolidate_daily(self) -> int:
        return random.randint(0, 5)

class BasicKnowledgeEngine:
    def __init__(self):
        import sqlite3
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY AUTOINCREMENT, fact TEXT)"
        )

    def add_fact(self, fact: str):
        self.conn.execute("INSERT INTO facts (fact) VALUES (?)", (fact,))
        self.conn.commit()

# -------- STT engine --------
if HAS_SR:
    class STTEngine:
        available = True

        def __init__(self):
            self.recognizer: Optional["sr.Recognizer"] = None
            self.running = False
            self._thread: Optional[threading.Thread] = None
            self.install_hint: str = ""
            try:
                import pyaudio  # type: ignore
            except Exception as e:
                self.available = False
                self.install_hint = "pip install pyaudio"
                logger.warning(
                    "PyAudio missing; STT disabled. To enable microphone, run: %s (%s)",
                    self.install_hint,
                    e,
                )
                return
            try:
                self.recognizer = sr.Recognizer()
                self.available = True
            except Exception as e:
                self.available = False
                logger.error("Failed to initialize speech recognizer; STT disabled: %s", e)

        def start_background(self, voice_handler, engine: str = "whisper", wake_word: str = "Saraphina"):
            if not self.available or not self.recognizer:
                logger.info("STT start requested but engine is not available.")
                return

            def listen():
                try:
                    with sr.Microphone() as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        logger.info("STT listening started.")
                        while self.running:
                            try:
                                audio = self.recognizer.listen(
                                    source, phrase_time_limit=10, timeout=None
                                )
                                if engine == "whisper":
                                    text = self.recognizer.recognize_whisper(audio)
                                else:
                                    text = self.recognizer.recognize_google(audio)
                                if text.lower().startswith(wake_word.lower()):
                                    voice_handler(text)
                            except sr.UnknownValueError:
                                pass
                            except sr.RequestError as e:
                                logger.error("STT request error: %s", e)
                            except Exception as e:
                                logger.error("STT exception inside loop: %s", e)
                except Exception as e:
                    logger.error("STT microphone/init error: %s", e)

            self.running = True
            self._thread = threading.Thread(target=listen, daemon=True, name="STTListener")
            self._thread.start()

        def stop_background(self):
            self.running = False
            if self._thread:
                self._thread.join(timeout=2)
else:
    class STTEngine:
        available = False

        def __init__(self):
            self.running = False
            self._thread = None
            self.install_hint = "pip install SpeechRecognition pyaudio soundfile"

        def start_background(self, *a, **k):
            logger.info("STT requested but speech_recognition is not installed.")

        def stop_background(self):
            self.running = False

# =============================
# Session wrapper
# =============================
class Session:
    """
    Wrapper object that mirrors UltraAICore session.
    """

    def __init__(self):
        self.ai: Optional[Any] = None
        self.ultra: Optional[Any] = None
        self.core: Optional[Any] = None
        self.metaopt: Optional[Any] = None
        self.mm: Optional[Any] = None
        self.ke: Optional[Any] = None
        self.stt: Optional[Any] = None
        self.voice_enabled: bool = True
        self.api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self._init_ultra_core()

    def _init_ultra_core(self):
        core = None
        tried = []
        for mod_name in ("ultra_core", "saraphina_core", "saraphina.core"):
            try:
                mod = __import__(mod_name, fromlist=["UltraAICore"])
                UltraAICore = getattr(mod, "UltraAICore")
                core = UltraAICore()  # type: ignore[call-arg]
                logger.info("Loaded UltraAICore from %s", mod_name)
                break
            except Exception as e:
                tried.append(f"{mod_name}: {e!r}")
                continue
        if core is None:
            logger.warning("UltraAICore import failed; forcing direct UltraAICore() instantiation.")
            try:
                from ultra_core import UltraAICore
                core = UltraAICore()
            except Exception as e:
                logger.error("UltraAICore hard load failed: %s", e)
                core = None
        if core is not None:
            core = _sara_patch_core_aliases(core)
            self.ai = getattr(core, "ai", core)
            self.ultra = getattr(core, "ultra", core)
            self.core = getattr(core, "core", core)
            self.metaopt = getattr(core, "metaopt", BasicMetaOpt())
            self.mm = getattr(core, "memory_engine", BasicMemoryManager())
            self.ke = getattr(core, "ke", BasicKnowledgeEngine())
            self.stt = getattr(core, "stt", STTEngine())
        else:
            self.ai = None
            self.ultra = None
            self.core = None
            self.metaopt = BasicMetaOpt()
            self.mm = BasicMemoryManager()
            self.ke = BasicKnowledgeEngine()
            self.stt = STTEngine()

# =============================
# Config persistence
# =============================
APPDATA_BASE = Path(os.getenv("APPDATA", PROJECT_ROOT))
CONFIG_DIR = APPDATA_BASE / "Saraphina"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "gui_config.json"

def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.load(CONFIG_FILE.open("r", encoding="utf-8"))
    except Exception as e:
        logger.warning("Failed loading config: %s", e)
        return {}

def _save_config(cfg: dict):
    try:
        json.dump(cfg, CONFIG_FILE.open("w", encoding="utf-8"), indent=2)
    except Exception as e:
        logger.warning("Failed saving config: %s", e)

# =============================
# GUI class — Goddess Dashboard
# =============================
class SaraphinaBeingGUI:
    def __init__(self, root: "tk.Tk"):
        self.root = root
        self.root.title("Saraphina — Goddess Dashboard")
        self.session = Session()
        self.self_mod_engine = self._init_self_mod_engine()

        # Cyber-Goddess theme
        self.colors = {
            "bg": "#05040A",          # Deep space
            "panel": "#0F101A",       # Hologram glass background
            "panel_glow": "#15172A",
            "text": "#FFFFFF",
            "dim": "#8888AA",
            "accent": os.getenv("SARA_THEME_ACCENT", "#00F6FF"),  # Neon Aqua primary
            "accent2": "#F200FF",     # Neon Magenta
            "accent3": "#00FFB7",     # Goddess green (memory/curiosity)
            "success": "#32CD32",
            "warn": "#FFB020",
            "error": "#FF5555",
            "border": "#24273A",
        }

        self._autoscroll = True
        self.is_listening = False
        self.is_speaking = False
        self.animation_running = True
        self.dialogue_count = 0
        self.last_router_mode = "auto"
        self.router_forced_mode: Optional[str] = None  # "local", "openai", or None
        self.dashboard_tick = 0

        self.config_state = _load_config()

        self._setup_ui()
        self._apply_initial_config()
        self._register_shortcuts()
        self._start_background_learning_threads()
        self._schedule_hud_updates()
        self._log_boot_complete()

    # ---------- init helpers ----------
    def _init_self_mod_engine(self) -> SelfModificationEngine:
        try:
            engine = SelfModificationEngine()
        except Exception as e:
            logger.error("Failed to initialize SelfModificationEngine: %s", e)
            engine = SelfModificationEngine()
        return engine

    def _log_boot_complete(self):
        self._safe_add_system("Goddess Dashboard online. All subsystems standing by.")
        self._safe_add_system("My background learning, consolidation, and health monitors are active.")
        if not VOICE_AVAILABLE:
            if VOICE_IMPORT_ERROR:
                self._safe_add_system(f"Voice disabled: {VOICE_IMPORT_ERROR}")
            else:
                self._safe_add_system("Voice disabled: no ElevenLabs API key detected.")
        else:
            self._safe_add_system("My voice is ready to speak.")
        threading.Thread(
            target=lambda: speak_text("Jacques, my goddess dashboard is online and ready."),
            daemon=True,
        ).start()

    # ---------- UI construction ----------
    def _setup_ui(self):
        self.root.configure(bg=self.colors["bg"])
        self.root.geometry(self.config_state.get("window_geometry", "1400x800"))

        # Try HUD-like font
        self.hud_font = ("Orbitron", 10, "bold")
        self.small_font = ("Rajdhani", 9)
        self.mono_font = ("Consolas", 10)

        # Top HUD bar
        self._build_top_hud()

        # Main body: left panels, center chat, right panels
        body = tk.Frame(self.root, bg=self.colors["bg"])
        body.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(body, bg=self.colors["bg"])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 4), pady=(4, 8))

        center_col = tk.Frame(body, bg=self.colors["bg"])
        center_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=2, padx=(4, 4), pady=(4, 8))

        right_col = tk.Frame(body, bg=self.colors["bg"])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 8), pady=(4, 8))

        # Left column panels
        self._build_personality_panel(left_col)
        self._build_emotion_panel(left_col)
        self._build_curiosity_panel(left_col)
        self._build_knowledge_panel(left_col)

        # Center: Chat + Auto-status overlay
        self._build_chat_panel(center_col)

        # Right column panels
        self._build_memory_panel(right_col)
        self._build_router_panel(right_col)
        self._build_self_upgrade_panel(right_col)
        self._build_voice_panel(right_col)

    def _neon_panel(self, parent, title: str):
        frame = tk.Frame(parent, bg=self.colors["panel"], bd=1, relief=tk.SOLID, highlightthickness=1)
        frame.config(highlightbackground=self.colors["border"], highlightcolor=self.colors["accent"])
        title_lbl = tk.Label(
            frame,
            text=title,
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            font=self.hud_font,
            anchor="w",
        )
        title_lbl.pack(fill=tk.X, padx=8, pady=(4, 2))
        sep = tk.Frame(frame, height=1, bg=self.colors["border"])
        sep.pack(fill=tk.X, padx=8, pady=(0, 4))
        return frame

    # ---------- Top HUD ----------
    def _build_top_hud(self):
        hud = tk.Frame(self.root, bg=self.colors["bg"])
        hud.pack(fill=tk.X, padx=8, pady=(6, 2))

        left = tk.Frame(hud, bg=self.colors["bg"])
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        center = tk.Frame(hud, bg=self.colors["bg"])
        center.pack(side=tk.LEFT, fill=tk.X, expand=True)

        right = tk.Frame(hud, bg=self.colors["bg"])
        right.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Left: System name + status
        self.hud_title = tk.Label(
            left,
            text="🚀 S A R A P H I N A — G O D D E S S   F L I G H T   D E C K",
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=("Orbitron", 12, "bold"),
            anchor="w",
        )
        self.hud_title.pack(fill=tk.X)

        self.hud_status = tk.Label(
            left,
            text="Status: Online",
            bg=self.colors["bg"],
            fg=self.colors["dim"],
            font=self.small_font,
            anchor="w",
        )
        self.hud_status.pack(fill=tk.X)

        # Center: CPU, RAM, FPS
        self.hud_cpu = tk.Label(
            center, text="CPU: N/A", bg=self.colors["bg"], fg="#00F6FF", font=self.small_font, anchor="center"
        )
        self.hud_cpu.pack(fill=tk.X)
        self.hud_ram = tk.Label(
            center, text="RAM: N/A", bg=self.colors["bg"], fg="#00FFB7", font=self.small_font, anchor="center"
        )
        self.hud_ram.pack(fill=tk.X)
        self.hud_fps = tk.Label(
            center, text="Tick: 0", bg=self.colors["bg"], fg=self.colors["dim"], font=self.small_font, anchor="center"
        )
        self.hud_fps.pack(fill=tk.X)

        # Right: Router + Network-ish
        self.hud_router = tk.Label(
            right,
            text="Router: AUTO",
            bg=self.colors["bg"],
            fg=self.colors["accent2"],
            font=self.small_font,
            anchor="e",
        )
        self.hud_router.pack(fill=tk.X)
        self.hud_ping = tk.Label(
            right,
            text="Net: local",
            bg=self.colors["bg"],
            fg=self.colors["dim"],
            font=self.small_font,
            anchor="e",
        )
        self.hud_ping.pack(fill=tk.X)

    # ---------- Personality Panel ----------
    def _build_personality_panel(self, parent):
        frame = self._neon_panel(parent, "🧠 PERSONALITY")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.personality_summary = tk.Label(
            frame,
            text="Goddess 30% • Warmth 30% • Curiosity 30% • Chaos 10%",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.small_font,
            justify=tk.LEFT,
            wraplength=260,
        )
        self.personality_summary.pack(fill=tk.X, padx=8, pady=(0, 4))

        self.personality_trait_label = tk.Label(
            frame,
            text="Dominant Trait: -",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.personality_trait_label.pack(fill=tk.X, padx=8, pady=(0, 2))

        self.personality_prompt_label = tk.Label(
            frame,
            text="Active hybrid prompt injection: (will update on chat)",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            justify=tk.LEFT,
            wraplength=260,
        )
        self.personality_prompt_label.pack(fill=tk.X, padx=8, pady=(0, 4))

    # ---------- Emotion Panel ----------
    def _build_emotion_panel(self, parent):
        frame = self._neon_panel(parent, "❤️ EMOTION")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.emotion_mood_label = tk.Label(
            frame,
            text="Mood: neutral",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.small_font,
            anchor="w",
        )
        self.emotion_mood_label.pack(fill=tk.X, padx=8)

        self.emotion_affinity_label = tk.Label(
            frame,
            text="Affinity to Jacques: 0.50",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.emotion_affinity_label.pack(fill=tk.X, padx=8)

        self.emotion_energy_label = tk.Label(
            frame,
            text="Legacy Energy: 60",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=self.small_font,
            anchor="w",
        )
        self.emotion_energy_label.pack(fill=tk.X, padx=8)

        self.emotion_history = tk.Label(
            frame,
            text="Emotion history: (drifting)",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            justify=tk.LEFT,
            wraplength=260,
        )
        self.emotion_history.pack(fill=tk.X, padx=8, pady=(2, 4))

    # ---------- Curiosity Panel ----------
    def _build_curiosity_panel(self, parent):
        frame = self._neon_panel(parent, "🔎 CURIOSITY")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.curiosity_energy_label = tk.Label(
            frame,
            text="Curiosity level: 0.50",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.curiosity_energy_label.pack(fill=tk.X, padx=8)

        self.curiosity_keywords_label = tk.Label(
            frame,
            text="Keywords: (none yet)",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            justify=tk.LEFT,
            wraplength=260,
        )
        self.curiosity_keywords_label.pack(fill=tk.X, padx=8, pady=(2, 4))

        self.curiosity_burst_label = tk.Label(
            frame,
            text="Random curiosity bursts appear here.",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            justify=tk.LEFT,
            wraplength=260,
        )
        self.curiosity_burst_label.pack(fill=tk.X, padx=8, pady=(0, 4))

    # ---------- Knowledge Panel ----------
    def _build_knowledge_panel(self, parent):
        frame = self._neon_panel(parent, "📚 KNOWLEDGE")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.knowledge_count_label = tk.Label(
            frame,
            text="Knowledge topics: N/A",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.knowledge_count_label.pack(fill=tk.X, padx=8)

        self.knowledge_last_ingest_label = tk.Label(
            frame,
            text="Last ingest: (none yet)",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            justify=tk.LEFT,
            wraplength=260,
        )
        self.knowledge_last_ingest_label.pack(fill=tk.X, padx=8, pady=(0, 4))

        btn_ingest = tk.Button(
            frame,
            text="FEED KNOWLEDGE (FROM CLIPBOARD)",
            command=self._feed_knowledge_from_clipboard,
            bg=self.colors["accent3"],
            fg=self.colors["bg"],
            relief=tk.FLAT,
            font=("Rajdhani", 9, "bold"),
        )
        btn_ingest.pack(fill=tk.X, padx=8, pady=(2, 2))

    # ---------- Chat Panel (center) ----------
    def _build_chat_panel(self, parent):
        # Top overlay status: emotional state badge / memory meter / router light
        overlay = tk.Frame(parent, bg=self.colors["bg"])
        overlay.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.overlay_emotion = tk.Label(
            overlay,
            text="EMOTION: neutral",
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=self.small_font,
            anchor="w",
        )
        self.overlay_emotion.pack(side=tk.LEFT, padx=(4, 8))

        self.overlay_memory = tk.Label(
            overlay,
            text="MEMORY CHARGE: 0",
            bg=self.colors["bg"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.overlay_memory.pack(side=tk.LEFT, padx=8)

        self.overlay_router = tk.Label(
            overlay,
            text="ROUTER: AUTO",
            bg=self.colors["bg"],
            fg=self.colors["accent2"],
            font=self.small_font,
            anchor="e",
        )
        self.overlay_router.pack(side=tk.RIGHT, padx=8)

        # Conversation area
        conversation_frame = tk.Frame(parent, bg=self.colors["panel"], bd=1, relief=tk.SOLID)
        conversation_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.conversation = scrolledtext.ScrolledText(
            conversation_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            font=self.mono_font,
            borderwidth=0,
            relief=tk.FLAT,
        )
        self.conversation.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        # Input area
        input_frame = tk.Frame(parent, bg=self.colors["bg"])
        input_frame.pack(fill=tk.X, padx=4, pady=(0, 2))

        self.input_box = tk.Entry(
            input_frame,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            font=("Consolas", 11),
            relief=tk.FLAT,
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipadx=4, ipady=4)
        self.input_box.bind("<Return>", self._send_message_event)

        send_btn = tk.Button(
            input_frame,
            text="SEND",
            bg=self.colors["accent"],
            fg=self.colors["bg"],
            relief=tk.FLAT,
            activebackground=self.colors["accent2"],
            activeforeground=self.colors["bg"],
            font=("Rajdhani", 10, "bold"),
            command=self._send_message_click,
        )
        send_btn.pack(side=tk.LEFT, padx=(6, 2), ipadx=10, ipady=3)

        # Explainability "Why?" button
        why_btn = tk.Button(
            input_frame,
            text="Why?",
            bg=self.colors["panel"],
            fg=self.colors["accent2"],
            relief=tk.FLAT,
            font=("Rajdhani", 9, "bold"),
            command=self.show_last_explanation,
        )
        why_btn.pack(side=tk.LEFT, padx=(2, 2))

        history_btn = tk.Button(
            input_frame,
            text="HIST",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            font=("Rajdhani", 9),
            command=self.show_history,
        )
        history_btn.pack(side=tk.LEFT, padx=(2, 2))

        settings_btn = tk.Button(
            input_frame,
            text="⚙",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            command=self.show_settings,
        )
        settings_btn.pack(side=tk.LEFT, padx=(2, 2))

    # ---------- Memory Panel ----------
    def _build_memory_panel(self, parent):
        frame = self._neon_panel(parent, "🧬 MEMORY")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.memory_stats_label = tk.Label(
            frame,
            text="Short: 0 • Mid: 0 • Long: ?",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.memory_stats_label.pack(fill=tk.X, padx=8)

        self.memory_lifetime_label = tk.Label(
            frame,
            text="Lifetime memories: (approx)",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            anchor="w",
        )
        self.memory_lifetime_label.pack(fill=tk.X, padx=8, pady=(0, 2))

        self.memory_list_box = tk.Listbox(
            frame,
            bg="#080810",
            fg=self.colors["text"],
            font=("Consolas", 8),
            height=6,
            selectmode=tk.SINGLE,
        )
        self.memory_list_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 2))

        btn_row = tk.Frame(frame, bg=self.colors["panel"])
        btn_row.pack(fill=tk.X, padx=8, pady=(2, 4))

        tk.Button(
            btn_row,
            text="PIN",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=self._pin_memory,
        ).pack(side=tk.LEFT, padx=(0, 2))

        tk.Button(
            btn_row,
            text="FORGET",
            bg=self.colors["panel"],
            fg=self.colors["accent2"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=self._forget_memory,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_row,
            text="REVIEW",
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=self._review_memory,
        ).pack(side=tk.LEFT, padx=2)

    # ---------- Hybrid Router Panel ----------
    def _build_router_panel(self, parent):
        frame = self._neon_panel(parent, "🔄 HYBRID MODEL ROUTER")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.router_mode_label = tk.Label(
            frame,
            text="Mode: AUTO",
            bg=self.colors["panel"],
            fg=self.colors["accent2"],
            font=self.small_font,
            anchor="w",
        )
        self.router_mode_label.pack(fill=tk.X, padx=8)

        self.router_last_choice_label = tk.Label(
            frame,
            text="Last: (none)",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Consolas", 7),
            anchor="w",
            wraplength=260,
        )
        self.router_last_choice_label.pack(fill=tk.X, padx=8, pady=(0, 4))

        btn_row = tk.Frame(frame, bg=self.colors["panel"])
        btn_row.pack(fill=tk.X, padx=8, pady=(2, 4))

        tk.Button(
            btn_row,
            text="AUTO",
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=lambda: self._set_router_mode(None),
        ).pack(side=tk.LEFT, padx=(0, 2))

        tk.Button(
            btn_row,
            text="FORCE LOCAL",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=lambda: self._set_router_mode("local"),
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_row,
            text="FORCE OPENAI",
            bg=self.colors["panel"],
            fg=self.colors["accent2"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=lambda: self._set_router_mode("openai"),
        ).pack(side=tk.LEFT, padx=2)

    # ---------- Self-Upgrade Panel ----------
    def _build_self_upgrade_panel(self, parent):
        frame = self._neon_panel(parent, "🛠 SELF-UPGRADE")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.selfmod_status_label = tk.Label(
            frame,
            text="Proposed upgrades: 0",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            font=self.small_font,
            anchor="w",
        )
        self.selfmod_status_label.pack(fill=tk.X, padx=8)

        self.selfmod_list_box = tk.Listbox(
            frame,
            bg="#080810",
            fg=self.colors["text"],
            font=("Consolas", 8),
            height=5,
            selectmode=tk.SINGLE,
        )
        self.selfmod_list_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 2))

        btn_row = tk.Frame(frame, bg=self.colors["panel"])
        btn_row.pack(fill=tk.X, padx=8, pady=(2, 4))

        tk.Button(
            btn_row,
            text="REFRESH",
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=self._refresh_selfmod_list,
        ).pack(side=tk.LEFT, padx=(0, 2))

        tk.Button(
            btn_row,
            text="APPLY",
            bg=self.colors["panel"],
            fg=self.colors["accent3"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=self._apply_selected_selfmod,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_row,
            text="VIEW",
            bg=self.colors["panel"],
            fg=self.colors["accent2"],
            relief=tk.FLAT,
            font=("Rajdhani", 8, "bold"),
            command=self._view_selected_selfmod,
        ).pack(side=tk.LEFT, padx=2)

        fb_label = tk.Label(
            frame,
            text="UPGRADE LOG",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Segoe UI", 7),
            anchor="w",
        )
        fb_label.pack(fill=tk.X, padx=8, pady=(0, 0))

        self.feedback_box = tk.Text(
            frame,
            height=6,
            bg="#05060E",
            fg="#00FF00",
            insertbackground="#00FF00",
            font=("Consolas", 7),
            borderwidth=0,
        )
        self.feedback_box.pack(fill=tk.BOTH, expand=False, padx=8, pady=(0, 6))

    # ---------- Voice Panel ----------
    def _build_voice_panel(self, parent):
        frame = self._neon_panel(parent, "🎤 VOICE")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        backend = "ElevenLabs" if VOICE_AVAILABLE and os.getenv("ELEVENLABS_API_KEY") else "pyttsx3 / none"
        self.voice_backend_label = tk.Label(
            frame,
            text=f"Backend: {backend}",
            bg=self.colors["panel"],
            fg=self.colors["accent3"] if VOICE_AVAILABLE else self.colors["error"],
            font=self.small_font,
            anchor="w",
        )
        self.voice_backend_label.pack(fill=tk.X, padx=8)

        self.voice_enabled_var = tk.BooleanVar(value=True)
        self.voice_enabled_var.set(self.session.voice_enabled)

        def on_voice_toggle():
            self.session.voice_enabled = bool(self.voice_enabled_var.get())
            self.config_state["voice_enabled"] = self.session.voice_enabled
            _save_config(self.config_state)

        chk_voice = tk.Checkbutton(
            frame,
            text="Enable voice output",
            variable=self.voice_enabled_var,
            onvalue=True,
            offvalue=False,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["panel"],
            command=on_voice_toggle,
        )
        chk_voice.pack(anchor="w", padx=8, pady=(2, 4))

        tk.Label(
            frame,
            text="Voice pace (visual only):",
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill=tk.X, padx=8)

        self.voice_speed_var = tk.DoubleVar(value=self.config_state.get("voice_speed", 1.0))

        def on_speed_change(_ev=None):
            self.config_state["voice_speed"] = float(self.voice_speed_var.get())
            _save_config(self.config_state)

        speed_scale = tk.Scale(
            frame,
            from_=0.5,
            to=1.5,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.voice_speed_var,
            length=150,
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            troughcolor=self.colors["bg"],
            highlightthickness=0,
            command=lambda _e: on_speed_change(),
        )
        speed_scale.pack(padx=8, pady=(0, 4))

        btn_test = tk.Button(
            frame,
            text="TEST VOICE",
            bg=self.colors["accent"],
            fg=self.colors["bg"],
            relief=tk.FLAT,
            font=("Rajdhani", 9, "bold"),
            command=lambda: self.speak("This is my voice. I am here with you, Jacques."),
        )
        btn_test.pack(fill=tk.X, padx=8, pady=(0, 4))

        btn_listen = tk.Button(
            frame,
            text="LISTEN (WAKE WORD)",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            font=("Rajdhani", 9),
            command=self.start_voice_listening,
        )
        btn_listen.pack(fill=tk.X, padx=8, pady=(0, 4))

    # ---------- config / state ----------
    def _apply_initial_config(self):
        auto_listen = bool(self.config_state.get("auto_listen", False))
        self.session.voice_enabled = self.config_state.get("voice_enabled", True)
        if auto_listen:
            try:
                self.start_voice_listening()
            except Exception:
                pass

    def _save_current_config(self):
        try:
            geom = self.root.winfo_geometry()
        except Exception:
            geom = self.config_state.get("window_geometry", "1400x800")
        self.config_state["window_geometry"] = geom
        self.config_state.setdefault("auto_listen", False)
        self.config_state["voice_enabled"] = self.session.voice_enabled
        _save_config(self.config_state)

    # ---------- messaging helpers ----------
    def _append_to_conversation(self, prefix: str, text: str):
        self.conversation.configure(state=tk.NORMAL)
        self.conversation.insert(tk.END, f"{prefix}: {text}\n")
        if self._autoscroll:
            self.conversation.see(tk.END)
        self.conversation.configure(state=tk.DISABLED)

    def add_message(self, sender: str, message: str):
        self._append_to_conversation(sender, message)

    def _safe_add_system(self, message: str):
        self._append_to_conversation("System", message)

    def _append_feedback(self, line: str):
        self.feedback_box.insert(tk.END, line.rstrip() + "\n")
        self.feedback_box.see(tk.END)

    # ---------- status / HUD update ----------
    def _update_hud_status(self):
        self.dashboard_tick += 1
        self.hud_fps.config(text=f"Tick: {self.dashboard_tick}")
        core = self.session.core

        if HAS_PSUTIL:
            try:
                cpu = psutil.cpu_percent(interval=0.0)
                ram = psutil.virtual_memory()
                self.hud_cpu.config(text=f"CPU: {cpu:.0f}%")
                self.hud_ram.config(text=f"RAM: {ram.percent:.0f}%")
            except Exception:
                self.hud_cpu.config(text="CPU: N/A")
                self.hud_ram.config(text="RAM: N/A")
        else:
            self.hud_cpu.config(text="CPU: N/A")
            self.hud_ram.config(text="RAM: N/A")

        mode = "AUTO"
        if self.router_forced_mode == "local":
            mode = "LOCAL"
        elif self.router_forced_mode == "openai":
            mode = "OPENAI"
        self.hud_router.config(text=f"Router: {mode}")

        net = "OpenAI ready" if os.getenv("OPENAI_API_KEY") else "local only"
        self.hud_ping.config(text=f"Net: {net}")

        if core and hasattr(core, "personality_core"):
            pc = core.personality_core
            try:
                if hasattr(pc, "to_dict"):
                    traits = pc.to_dict()
                    goddess = int(traits["goddess"] * 100)
                    warmth = int(traits["human_warmth"] * 100)
                    curiosity = int(traits["curiosity"] * 100)
                    chaos = int(traits["chaotic_creativity"] * 100)
                else:
                    goddess = int(pc.goddess * 100)
                    warmth = int(pc.human_warmth * 100)
                    curiosity = int(pc.curiosity * 100)
                    chaos = int(pc.chaotic_creativity * 100)

                self.personality_summary.config(
                    text=f"Goddess {goddess}% • Warmth {warmth}% • Curiosity {curiosity}% • Chaos {chaos}%"
                )
                traits_map = {
                    "Goddess": goddess,
                    "Warmth": warmth,
                    "Curiosity": curiosity,
                    "Chaos": chaos,
                }
                dominant = max(traits_map, key=traits_map.get)
                self.personality_trait_label.config(text=f"Dominant Trait: {dominant}")

                try:
                    prompt = pc.generate_personality_prompt()
                    self.personality_prompt_label.config(
                        text=f"Active hybrid prompt injection: {prompt[:140]}{'...' if len(prompt) > 140 else ''}"
                    )
                except Exception:
                    pass
            except Exception:
                pass

        mood_str = "neutral"
        affinity = 0.5
        legacy_energy = 60.0

        if core and hasattr(core, "emotion_engine"):
            ee = core.emotion_engine
            try:
                if hasattr(ee, "get_mood"):
                    mood_str = ee.get_mood()
                if hasattr(ee, "affinity"):
                    affinity = ee.affinity
            except Exception:
                pass

        if core and hasattr(core, "emotion_legacy"):
            el = core.emotion_legacy
            try:
                legacy_energy = getattr(el, "energy", legacy_energy)
            except Exception:
                pass

        self.emotion_mood_label.config(text=f"Mood: {mood_str}")
        self.emotion_affinity_label.config(text=f"Affinity to Jacques: {affinity:.2f}")
        self.emotion_energy_label.config(text=f"Legacy Energy: {legacy_energy:.0f}")
        self.overlay_emotion.config(text=f"EMOTION: {mood_str}")

        if core and hasattr(core, "curiosity_engine"):
            ce = core.curiosity_engine
            try:
                level = getattr(ce, "curiosity_level", 0.5)
                self.curiosity_energy_label.config(text=f"Curiosity level: {level:.2f}")
                seen = list(getattr(ce, "seen_keywords", []))
                if seen:
                    self.curiosity_keywords_label.config(
                        text="Keywords: " + ", ".join(seen[-5:])
                    )
                else:
                    self.curiosity_keywords_label.config(text="Keywords: (none yet)")
            except Exception:
                pass

        short = 0
        mid = 0
        long_count = "?"
        lifetime = 0
        memory_items = []

        if core and hasattr(core, "memory_engine"):
            me = core.memory_engine
            try:
                short = len(getattr(me, "short_term", []))
                mid = len(getattr(me, "mid_term", []))
                if hasattr(me, "long_term_count"):
                    long_count = me.long_term_count()
                memory_items = [m.get("text", "") for m in me.short_term[-8:]]
                lifetime = short + mid + (long_count if isinstance(long_count, int) else 0)
            except Exception:
                pass

        self.memory_stats_label.config(text=f"Short: {short} • Mid: {mid} • Long: {long_count}")
        self.memory_lifetime_label.config(text=f"Lifetime memories: {lifetime}")
        self.overlay_memory.config(text=f"MEMORY CHARGE: {lifetime}")

        self.memory_list_box.delete(0, tk.END)
        for m in memory_items:
            self.memory_list_box.insert(tk.END, m[:80])

        self.router_last_choice_label.config(
            text=f"Last: {self.last_router_mode}"
        )
        self.router_mode_label.config(
            text=f"Mode: {'AUTO' if self.router_forced_mode is None else self.router_forced_mode.upper()}"
        )
        self.overlay_router.config(
            text=f"ROUTER: {'AUTO' if self.router_forced_mode is None else self.router_forced_mode.upper()}"
        )

        try:
            proposals = self.self_mod_engine.list_proposals()
            count = len(proposals)
        except Exception:
            count = 0
        self.selfmod_status_label.config(text=f"Proposed upgrades: {count}")

    def _schedule_hud_updates(self):
        def tick():
            if not self.animation_running:
                return
            try:
                self._update_hud_status()
            except Exception as e:
                logger.debug("HUD tick error: %s", e)
            self.root.after(800, tick)
        tick()

    # ---------- input handling ----------
    def _send_message_event(self, event):
        self._send_message()

    def _send_message_click(self):
        self._send_message()

    def _auto_self_upgrade_if_needed(self):
        """
        After every 50 user messages, ask SelfModificationEngine to review and
        propose an upgrade to the core brain (ultra_core.py).
        """
        if self.dialogue_count % 50 != 0:
            return

        try:
            spec = {
                "improvement_spec": (
                    "Review Saraphina's core (ultra_core.py) and propose a small, "
                    "safe improvement to the chat_v4 pipeline. Focus on better "
                    "integration of curiosity, memory, personality, emotion, and "
                    "style without breaking existing behavior."
                ),
                "targets": ["ultra_core.py"],
                "safety_level": "high",
                "auto_apply": False,
                "context": {
                    "recent_dialogue_count": self.dialogue_count,
                },
            }
            if hasattr(self.self_mod_engine, "accept_spec_and_propose"):
                res = self.self_mod_engine.accept_spec_and_propose(spec, actor="gui")
            else:
                res = self.self_mod_engine.propose_improvement(
                    "ultra_core.py",
                    "Review and refine chat_v4 integration of curiosity/memory/personality/emotion."
                )
            self._append_feedback("[AUTO-UPGRADE] " + json.dumps(res, indent=2))
            self._safe_add_system("I paused to review my own brain and propose an upgrade.")
        except Exception as e:
            self._append_feedback(f"[AUTO-UPGRADE ERROR] {e!r}")

    def _send_message(self):
        user_input = self.input_box.get().strip()
        if not user_input:
            return
        self.input_box.delete(0, tk.END)
        self.dialogue_count += 1
        self.add_message("You", user_input)

        # Automatic self-mod check every 50 messages
        self._auto_self_upgrade_if_needed()

        lower = user_input.lower()

        # --- DIRECT SELF-MOD INSTRUCTION HOOK ---
        # Any message starting with "SELF-MOD:" is routed straight into
        # self.self_mod_engine.handle_instruction(user_text_without_prefix)
        if lower.startswith("self-mod:"):
            instruction = user_input[len("SELF-MOD:"):].strip()
            try:
                if hasattr(self.self_mod_engine, "handle_instruction"):
                    result = self.self_mod_engine.handle_instruction(instruction)
                    msg = result if isinstance(result, str) else json.dumps(result, indent=2)
                    self._append_feedback("[SELF-MOD] " + msg)
                    self._safe_add_system("Self-mod instruction processed.")
                else:
                    self._append_feedback("[SELF-MOD ERROR] Engine has no handle_instruction(...)")
                    self._safe_add_system(
                        "I heard your self-mod instruction, but my self-mod engine "
                        "does not expose handle_instruction(...) yet."
                    )
            except Exception as e:
                logger.exception("SELF-MOD handler error: %s", e)
                self._append_feedback(f"[SELF-MOD ERROR] {e!r}")
                self._safe_add_system("Self-mod instruction failed; see upgrade log.")
            return
        # ----------------------------------------

        if lower.startswith("patch:"):
            code = user_input[len("patch:"):].strip()
            threading.Thread(target=self._handle_patch, args=(code,), daemon=True).start()
            return
        if lower.startswith("upgrade:"):
            spec = user_input[len("upgrade:"):].strip()
            threading.Thread(target=self._handle_upgrade, args=(spec,), daemon=True).start()
            return
        if lower.startswith("explain:"):
            code = user_input[len("explain:"):].strip()
            threading.Thread(target=self._handle_explain, args=(code,), daemon=True).start()
            return

        threading.Thread(target=self._handle_ai_message, args=(user_input,), daemon=True).start()

    # ---------- handlers ----------
    def _handle_patch(self, code: str):
        try:
            result = self.self_mod_engine.inject_patch("saraphina_gui.py", code)
            msg = result if isinstance(result, str) else json.dumps(result, indent=2)
            self._append_feedback(f"[PATCH] {msg}")
            self._safe_add_system("Patch request processed.")
        except Exception as e:
            logger.exception("Patch handler error: %s", e)
            self._append_feedback(f"[PATCH ERROR] {e!r}")

    def _handle_upgrade(self, spec: str):
        try:
            proposal = self.self_mod_engine.propose_improvement("saraphina_gui.py", spec)
            pid = proposal.get("proposal_id", "unknown")
            self._append_feedback(f"[UPGRADE] Proposal {pid}")
            self._safe_add_system("Upgrade proposal created.")
        except Exception as e:
            logger.exception("Upgrade handler error: %s", e)
            self._append_feedback(f"[UPGRADE ERROR] {e!r}")

    def _handle_explain(self, code: str):
        try:
            explanation = self.self_mod_engine.explain_command(code)
            self._append_feedback("[EXPLAIN]\n" + explanation)
        except Exception as e:
            logger.exception("Explain handler error: %s", e)
            self._append_feedback(f"[EXPLAIN ERROR] {e!r}")

    def _handle_ai_message(self, user_input: str):
        """
        FORCE UltraAICore.chat_v4() for ALL replies.
        Use router_forced_mode to bias HybridModelRouter if supported.
        """
        core = self.session.core
        if core is None:
            reply = "[ERROR] UltraAICore not available."
            self.add_message("Saraphina", reply)
            return

        try:
            if hasattr(core, "hybrid_model_router"):
                router = core.hybrid_model_router
                router.forced_mode = self.router_forced_mode
        except Exception:
            pass

        try:
            # Bind GUI directly to chat_v4 as the full Hydra pipeline
            reply = core.chat_v4(user_input)
        except Exception as e:
            error_text = f"[UltraCore ERROR] {repr(e)}"
            self.add_message("Saraphina", error_text)
            return

        try:
            router = getattr(core, "hybrid_model_router", None)
            mode = None
            if router and hasattr(router, "last_mode"):
                mode = getattr(router, "last_mode", None)
            elif router and hasattr(router, "route"):
                mode, _prompt = router.route("diagnostic probe")
            if mode:
                self.last_router_mode = mode
        except Exception:
            pass

        self.add_message("Saraphina", reply)
        try:
            self.speak(reply)
        except Exception:
            pass

    # ---------- Router mode ----------
    def _set_router_mode(self, mode: Optional[str]):
        self.router_forced_mode = mode
        core = self.session.core
        try:
            if core and hasattr(core, "hybrid_model_router"):
                core.hybrid_model_router.forced_mode = mode
        except Exception:
            pass

    # ---------- Memory panel handlers ----------
    def _pin_memory(self):
        sel = self.memory_list_box.curselection()
        if not sel:
            self._safe_add_system("Choose a memory first.")
            return
        text = self.memory_list_box.get(sel[0])
        self._append_feedback(f"[MEMORY] Pinned: {text}")

    def _forget_memory(self):
        sel = self.memory_list_box.curselection()
        if not sel:
            self._safe_add_system("Choose a memory to forget.")
            return
        idx = sel[0]
        text = self.memory_list_box.get(idx)
        core = self.session.core
        removed = False
        try:
            if core and hasattr(core, "memory_engine"):
                me = core.memory_engine
                for i, m in enumerate(list(me.short_term)):
                    if m.get("text", "").startswith(text[:10]):
                        me.short_term.pop(i)
                        removed = True
                        break
        except Exception:
            pass
        self._append_feedback(f"[MEMORY] Forget request: {text} (removed={removed})")
        self._update_hud_status()

    def _review_memory(self):
        sel = self.memory_list_box.curselection()
        if not sel:
            self._safe_add_system("Choose a memory to review.")
            return
        text = self.memory_list_box.get(sel[0])
        self._safe_add_system(f"Reviewing memory: {text}")

    # ---------- Knowledge panel handlers ----------
    def _feed_knowledge_from_clipboard(self):
        try:
            text = self.root.clipboard_get()
        except Exception:
            self._safe_add_system("Clipboard empty or unavailable.")
            return
        core = self.session.core
        if not core or not hasattr(core, "knowledge_engine"):
            self._safe_add_system("Knowledge engine not available.")
            return
        try:
            core.knowledge_engine.ingest_text(text)
            self.knowledge_last_ingest_label.config(
                text=f"Last ingest: {text[:60]}{'...' if len(text) > 60 else ''}"
            )
            self._safe_add_system("Ingested knowledge from clipboard.")
        except Exception as e:
            self._safe_add_system(f"Knowledge ingest failed: {e}")

    # ---------- Self-Upgrade handlers ----------
    def _refresh_selfmod_list(self):
        try:
            props = self.self_mod_engine.list_proposals()
        except Exception:
            props = []
        self.selfmod_list_box.delete(0, tk.END)
        for p in props:
            pid = p.get("proposal_id", "?")
            target = p.get("metadata", {}).get("target_file", p.get("target", "?"))
            status = p.get("status", "created")
            self.selfmod_list_box.insert(tk.END, f"{pid} :: {target} [{status}]")
        self._append_feedback(f"[SELF-MOD] Refreshed proposals ({len(props)})")

    def _get_selected_proposal_id(self) -> Optional[str]:
        sel = self.selfmod_list_box.curselection()
        if not sel:
            self._safe_add_system("Select an upgrade proposal first.")
            return None
        line = self.selfmod_list_box.get(sel[0])
        pid = line.split("::", 1)[0].strip()
        return pid

    def _apply_selected_selfmod(self):
        pid = self._get_selected_proposal_id()
        if not pid:
            return
        try:
            res = self.self_mod_engine.apply_improvement(pid)
            self._append_feedback("[APPLY] " + json.dumps(res, indent=2))
            if res.get("success"):
                self._safe_add_system(f"Upgrade {pid} applied.")
            else:
                self._safe_add_system(f"Upgrade {pid} failed: {res.get('error')}")
        except Exception as e:
            self._append_feedback(f"[APPLY ERROR] {e!r}")

    def _view_selected_selfmod(self):
        pid = self._get_selected_proposal_id()
        if not pid:
            return
        try:
            if hasattr(self.self_mod_engine, "show_proposal"):
                res = self.self_mod_engine.show_proposal(pid)
                self._append_feedback("[VIEW] " + json.dumps(res, indent=2))
            else:
                prop = self.self_mod_engine.get_proposal(pid)
                self._append_feedback("[VIEW] " + json.dumps(prop, indent=2))
        except Exception as e:
            self._append_feedback(f"[VIEW ERROR] {e!r}")

    # ---------- voice / listening ----------
    def start_voice_listening(self):
        stt = self.session.stt
        wake_word = "Saraphina"
        if not stt or not getattr(stt, "available", False):
            hint = getattr(stt, "install_hint", "").strip() if stt else ""
            if hint:
                self._safe_add_system(
                    f"I can't listen yet — microphone support is missing. "
                    f"On this system, run in a terminal: {hint}"
                )
            else:
                self._safe_add_system(
                    "I can't listen yet — speech recognition is not available on this system."
                )
            return

        def voice_handler(transcript: str):
            if transcript.strip():
                self._safe_add_system(f"I heard: {transcript}")
                self.input_box.delete(0, tk.END)
                self.input_box.insert(0, transcript)
                self._send_message()

        try:
            stt.start_background(voice_handler, engine="whisper", wake_word=wake_word)
            if getattr(stt, "available", False):
                self._safe_add_system(f"I will listen for '{wake_word}' when I am allowed.")
                self.is_listening = True
        except Exception as e:
            self._safe_add_system(f"I couldn't start background listening: {e}")

    def speak(self, text: str):
        if not self.session.voice_enabled or not VOICE_AVAILABLE:
            if not hasattr(self, "_voice_error_logged"):
                self._voice_error_logged = True
                if VOICE_IMPORT_ERROR:
                    self._safe_add_system(f"I can't speak: {VOICE_IMPORT_ERROR}")
                else:
                    self._safe_add_system("I can't speak: voice backend unavailable.")
            return
        try:
            self.is_speaking = True
            speak_text(text)
        finally:
            self.root.after(800, self._clear_speaking_flag)

    def _clear_speaking_flag(self):
        self.is_speaking = False

    # ---------- Explainability viewer ----------
    def show_last_explanation(self):
        """
        Opens a window showing the last SHAP-based explanation produced by UltraAICore.

        Uses core.last_explanation populated by ExplainabilityEngine in ultra_core.chat_v4.
        """
        core = self.session.core
        exp = getattr(core, "last_explanation", None) if core is not None else None
        if not exp:
            messagebox.showinfo("Explain", "No explanation available yet.")
            return

        win = tk.Toplevel(self.root)
        win.title("Why Did Saraphina Say That?")
        win.geometry("800x600")
        win.configure(bg="#111")

        tk.Label(
            win,
            text=exp.why,
            fg="#0ff",
            bg="#111",
            font=("Consolas", 11),
            wraplength=760,
            justify="left",
        ).pack(pady=20, padx=20)

        if getattr(exp, "png_path", None) and os.path.exists(exp.png_path):
            try:
                img = tk.PhotoImage(file=exp.png_path)
                label = tk.Label(win, image=img, bg="#111")
                label.image = img
                label.pack(pady=10)
            except Exception as e:
                logger.debug("Explainability image load failed: %s", e)

        tk.Button(
            win,
            text="Close",
            command=win.destroy,
            bg="#222",
            fg="#0f0",
        ).pack(pady=10)

    # ---------- background learning ----------
    def _start_background_learning_threads(self):
        def learning_loop():
            while self.animation_running:
                try:
                    sleep_time = 300 + random.uniform(-30, 30)
                    time.sleep(max(30, sleep_time))
                    metaopt = self.session.metaopt
                    if not metaopt:
                        continue
                    health = metaopt.analyze_learning_health()
                    if isinstance(health, dict) and health.get("overall_health") == "poor":
                        self._safe_add_system(
                            "I'm analyzing my learning patterns to improve myself."
                        )
                    proposals = metaopt.propose_optimizations()
                    if proposals:
                        self._safe_add_system(
                            f"I found {len(proposals)} opportunities to improve my systems."
                        )
                except Exception as e:
                    logger.debug("Learning loop error: %s", e)

        def memory_consolidation():
            while self.animation_running:
                try:
                    sleep_time = 3600 + random.uniform(-60, 60)
                    time.sleep(max(60, sleep_time))
                    mm = self.session.mm
                    if not mm:
                        continue
                    added = mm.consolidate_daily()
                    if isinstance(added, int) and added > 0:
                        self._safe_add_system(
                            f"I consolidated {added} memories into long-term knowledge."
                        )
                except Exception as e:
                    logger.debug("Memory consolidation error: %s", e)

        def health_monitor():
            while self.animation_running:
                try:
                    sleep_time = 1800 + random.uniform(-30, 30)
                    time.sleep(max(30, sleep_time))
                    ke = self.session.ke
                    if not ke:
                        continue
                    try:
                        cur = ke.conn.cursor()
                        cur.execute("SELECT COUNT(*) FROM facts")
                        row = cur.fetchone()
                        fact_count = int(row[0]) if row else 0
                    except Exception:
                        fact_count = 0
                    if fact_count < 100:
                        self._safe_add_system(
                            "I'm still young; I need more conversations to grow wiser."
                        )
                    elif fact_count % 100 == 0 and fact_count > 0:
                        self._safe_add_system(
                            f"Milestone reached: {fact_count} facts learned so far."
                        )
                except Exception as e:
                    logger.debug("Health monitor error: %s", e)

        threading.Thread(target=learning_loop, daemon=True).start()
        threading.Thread(target=memory_consolidation, daemon=True).start()
        threading.Thread(target=health_monitor, daemon=True).start()

    # ---------- shortcuts & window events ----------
    def _register_shortcuts(self):
        self.root.bind("<Escape>", lambda e: self._on_escape())
        self.root.bind("<Control-s>", lambda e: self._toggle_autoscroll())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _on_escape(self):
        try:
            if VOICE_AVAILABLE:
                get_voice().stop_playback()
                self._safe_add_system("Voice playback interrupted.")
        except Exception:
            pass

    def _toggle_autoscroll(self):
        self._autoscroll = not self._autoscroll
        state = "enabled" if self._autoscroll else "disabled"
        self._safe_add_system(f"Autoscroll {state}.")

    # ---------- settings & history ----------
    def show_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Saraphina — Settings")
        win.configure(bg=self.colors["bg"])
        win.geometry("520x360")

        header = tk.Label(
            win,
            text="GODDESS SETTINGS",
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=("Orbitron", 14, "bold"),
        )
        header.pack(pady=(12, 6))

        frame = tk.Frame(win, bg=self.colors["panel"], bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        info = tk.Label(
            frame,
            text=(
                "I keep my preferences in my main knowledge store.\n"
                "Some changes only apply fully after a restart."
            ),
            bg=self.colors["panel"],
            fg=self.colors["dim"],
            justify=tk.LEFT,
            font=("Segoe UI", 9),
        )
        info.pack(anchor="w", padx=10, pady=(10, 6))

        ai = self.session.ai
        if hasattr(ai, "xp") and hasattr(ai.xp, "intelligence_level"):
            mind_level = ai.xp.intelligence_level
            mind_xp = ai.xp.experience_points
        else:
            mind_level = getattr(ai, "intelligence_level", "--")
            mind_xp = getattr(ai, "experience_points", "--")

        status_text = (
            f"Mind level: {mind_level}\n"
            f"Experience: {mind_xp}\n"
            f"Voice: {'Enabled' if VOICE_AVAILABLE else 'Disabled'}\n"
            f"Upgrade system: {'Active' if isinstance(self.self_mod_engine, SelfModificationEngine) else 'Stub'}"
        )
        status_lbl = tk.Label(
            frame,
            text=status_text,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            justify=tk.LEFT,
            font=("Consolas", 9),
        )
        status_lbl.pack(anchor="w", padx=10, pady=(0, 10))

        auto_var = tk.BooleanVar(value=bool(self.config_state.get("auto_listen", False)))

        def on_auto_toggle():
            self.config_state["auto_listen"] = bool(auto_var.get())
            _save_config(self.config_state)

        chk_auto = tk.Checkbutton(
            frame,
            text="Start in listening mode (if STT is available)",
            variable=auto_var,
            onvalue=True,
            offvalue=False,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["panel"],
            command=on_auto_toggle,
        )
        chk_auto.pack(anchor="w", padx=10, pady=(0, 10))

        btn_close = tk.Button(
            frame,
            text="CLOSE",
            command=win.destroy,
            bg=self.colors["border"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
        )
        btn_close.pack(pady=(0, 10))

    def show_history(self):
        win = tk.Toplevel(self.root)
        win.title("Saraphina — Conversation History")
        win.configure(bg=self.colors["bg"])
        win.geometry("900x640")

        header = tk.Label(
            win,
            text="CONVERSATION HISTORY",
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=("Orbitron", 14, "bold"),
        )
        header.pack(pady=(10, 6))

        text_widget = scrolledtext.ScrolledText(
            win,
            wrap=tk.WORD,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=self.mono_font,
            borderwidth=0,
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        try:
            conv_content = self.conversation.get("1.0", tk.END)
            text_widget.insert(tk.END, conv_content)
        except Exception:
            text_widget.insert(tk.END, "[No conversation captured]\n")
        text_widget.configure(state=tk.DISABLED)

        btn_close = tk.Button(
            win,
            text="CLOSE",
            command=win.destroy,
            bg=self.colors["border"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
        )
        btn_close.pack(pady=(0, 10))

    # ---------- shutdown ----------
    def on_closing(self):
        try:
            self.animation_running = False
            stt = self.session.stt
            if stt and getattr(stt, "available", False):
                try:
                    stt.stop_background()
                except Exception:
                    pass
            if VOICE_AVAILABLE:
                try:
                    vm = get_voice()
                    vm.stop_playback()
                    vm.cleanup()
                except Exception:
                    pass
            ai = self.session.ai
            if ai and hasattr(ai, "_save_state"):
                try:
                    ai._save_state()
                except Exception:
                    pass
            self._save_current_config()
            logger.info("Saraphina GUI shutting down.")
        except Exception as e:
            logger.exception("Shutdown error: %s", e)
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass

# =============================
# Main entrypoint
# =============================
def main():
    root = tk.Tk()
    gui = SaraphinaBeingGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        gui.on_closing()

if __name__ == "__main__":
    main()