#!/usr/bin/env python3
"""
Saraphina GUI - Modern Futuristic Interface
A proper windowed application with smooth animations and always-on voice listening

Behavior change in this version:
- Only loads environment variables from a single authoritative .env file:
  D:/Saraphina Root/.env
- Keys present in that file are applied (overwrite) into os.environ so the runtime
  consistently uses that file as the single source of truth.
- Loaded secret values are printed masked for debugging (no full secrets are printed).
"""

import sys
import os
import threading
import queue
import time
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# ===== FORCE ALL TEMP FILES TO D: DRIVE =====
import tempfile
SARAPHINA_TEMP_DIR = Path("D:/Saraphina Root/temp")
SARAPHINA_TEMP_DIR.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(SARAPHINA_TEMP_DIR)
os.environ['TEMP'] = str(SARAPHINA_TEMP_DIR)
os.environ['TMP'] = str(SARAPHINA_TEMP_DIR)
print(f"[TEMP] All temporary files will use: {SARAPHINA_TEMP_DIR}")

# Add project root to path
REPO_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# -----------------------------
# Strict .env loading (single source of truth)
# Only load from: D:/Saraphina Root/.env
# This intentionally avoids loading any other .env files or relying on externally injected env vars
# for sensitive keys like OPENAI_API_KEY.
# -----------------------------
def _mask_key(k: Optional[str]) -> Optional[str]:
    if not k:
        return None
    k = str(k).strip()
    if len(k) <= 12:
        return k
    return k[:6] + "..." + k[-4:]

DOTENV_ENFORCED_PATH = Path("D:/Saraphina Root/.env")

try:
    from dotenv import dotenv_values
    if DOTENV_ENFORCED_PATH.exists():
        loaded = dotenv_values(DOTENV_ENFORCED_PATH)
        applied = {}
        # Apply overrides only for keys present in the authoritative file.
        for k, v in loaded.items():
            if v is None:
                continue
            # sanitize simple surrounding quotes and whitespace
            val = str(v).strip().strip('"').strip("'")
            os.environ[k] = val
            applied[k] = _mask_key(val)
        if applied:
            print(f"[ENV] Loaded and applied .env overrides from: {DOTENV_ENFORCED_PATH}")
            for kk, mv in applied.items():
                print(f"[ENV]   {kk} = {mv}")
        else:
            print(f"[ENV] {DOTENV_ENFORCED_PATH} found but no parsable keys.")
    else:
        print(f"[ENV] Enforced .env not found at: {DOTENV_ENFORCED_PATH}. No env overrides applied.")
except Exception as e:
    # If python-dotenv unavailable or something fails, do not modify environment and warn.
    print(f"[ENV] Warning: Could not load dotenv utilities: {e}. No .env overrides applied.")

# Try to import GUI library
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, font
    GUI_AVAILABLE = True
except ImportError:
    print("❌ Tkinter not available. GUI requires tkinter.")
    sys.exit(1)

# Import ALL Saraphina components - COMPLETE POWER
# Imports are best-effort; missing components will be handled in init
try:
    from saraphina.ai_core_enhanced import SaraphinaAIEnhanced
    from saraphina.ultra_ai_core import UltraAICore
    from saraphina.knowledge_engine import KnowledgeEngine
    from saraphina.db import init_db, get_preference, set_preference, write_audit_log
    from saraphina.stt import STT
    from saraphina.memory_manager import MemoryManager
    from saraphina.emotion_engine import EmotionEngine
    from saraphina.security import SecurityManager, SecurityError
    from saraphina.trust_firewall import TrustFirewall
    from saraphina.ethics import BeliefStore, EthicalReasoner
    from saraphina.planner import Planner
    from saraphina.risk_model import RiskModel
    from saraphina.review_manager import ReviewManager
    from saraphina.persona import PersonaManager
    from saraphina.intuition import IntuitionEngine
    from saraphina.knowledge_graph import KnowledgeGraphExplorer
    from saraphina.research_agent import ResearchAgent
    from saraphina.toolsmith import Toolsmith
    from saraphina.sentience_monitor import SentienceMonitor
    from saraphina.safety_gate import SafetyGate
    from saraphina.learning_journal import LearningJournal
    from saraphina.meta_optimizer import MetaOptimizer
    from saraphina.shadow_node import ShadowNode
    from saraphina.recovery_bootstrap import RecoveryBootstrap
    from saraphina.code_knowledge_db import CodeKnowledgeDB
    from saraphina.code_research_agent import CodeResearchAgent
    from saraphina.recursive_code_miner import RecursiveCodeMiner
    from saraphina.code_factory import CodeFactory
    from saraphina.test_harness import TestHarness
    from saraphina.code_proposal_db import CodeProposalDB
    from saraphina.refinement_engine import RefinementEngine
    from saraphina.self_modification_engine import SelfModificationEngine
    from saraphina.hot_reload_manager import HotReloadManager
    from saraphina.rollback_engine import RollbackEngine
    from saraphina.improvement_loop import ImprovementLoop
    from saraphina.improvement_db import ImprovementDB
    from saraphina.meta_architect import MetaArchitect
    from saraphina.simulation_sandbox import SimulationSandbox
    from saraphina.architecture_db import ArchitectureDB
    from saraphina.device_agent import DeviceAgent
    from saraphina.ood import is_text_ood, is_code_high_risk
    from saraphina.gui_ultra_processor import GUIUltraProcessor
    from saraphina.self_healing_manager import SelfHealingManager
    from saraphina.self_modification_api import SelfModificationAPI
except Exception as e:
    # Import errors will be handled during initialization. We print for debug.
    print(f"[IMPORT] Warning while importing saraphina modules: {e}")

# Use modern voice integration
try:
    from saraphina.voice_modern import speak_text, get_voice, VOICE_AVAILABLE
    VOICE_IMPORT_ERROR = None
except Exception as e:
    VOICE_IMPORT_ERROR = str(e)
    VOICE_AVAILABLE = False

    # Define dummy functions so GUI still runs without voice.
    def speak_text(text):
        pass

    def get_voice():
        return None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SaraphinaGUI")


class SaraphinaSession:
    """Session container for ALL Saraphina components - FULL TERMINAL POWER"""

    def __init__(self):
        self.ai = None
        self.ultra = None
        self.ke = None
        self.stt = None
        self.mm = None
        self.mem = None  # Episodic memory
        self.emotion = None
        self.sec = None
        self.trust = None
        self.beliefs = None
        self.reasoner = None
        self.planner = None
        self.risk = None
        self.reviews = None
        self.persona = None
        self.intuition = None
        self.graph_explorer = None
        self.research = None
        self.toolsmith = None
        self.sentience = None
        self.safety_gate = None
        self.journal = None
        self.metaopt = None
        self.shadow = None
        self.recovery = None
        self.code_kb = None
        self.code_research = None
        self.code_miner = None
        self.code_factory = None
        self.test_harness = None
        self.code_proposals = None
        self.refinement = None
        self.self_mod = None
        self.hot_reload = None
        self.rollback = None
        self.improvement_loop = None
        self.improvement_db = None
        self.meta_architect = None
        self.simulation = None
        self.arch_db = None
        self.device = None
        self.voice_enabled = False
        self.api_proc = None
        self.self_healing = None  # Phase 29: Autonomic error detection & healing
        self.self_mod_api = None  # Complete self-modification control


class SaraphinaGUI:
    """Modern GUI for Saraphina with futuristic styling and always-on voice"""

    def __init__(self, root):
        self.root = root
        self.root.title("Saraphina - Mission Control")
        self.root.geometry("1400x900")

        # Color scheme - Futuristic dark theme
        self.colors = {
            'bg': '#0a0e1a',           # Dark blue-black
            'panel': '#0f1729',        # Slightly lighter
            'border': '#1a2744',       # Border color
            'accent': '#00d9ff',       # Bright cyan
            'accent2': '#ff00ff',      # Magenta
            'text': '#e0e6f0',         # Light text
            'dim': '#6b7c9e',          # Dimmed text
            'success': '#00ff88',      # Green
            'warning': '#ffaa00',      # Orange
            'error': '#ff3366',        # Red
        }

        # Configure root
        self.root.configure(bg=self.colors['bg'])

        # Initialize Saraphina session
        self.sess = SaraphinaSession()
        self.message_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = False
        self.animation_running = True

        # Build UI
        self.create_widgets()
        self.init_saraphina()

        # Start processors
        self.process_messages()
        self.animate_status()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Create all UI widgets"""

        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ===== HEADER =====
        header_frame = tk.Frame(main_frame, bg=self.colors['panel'],
                                highlightbackground=self.colors['accent'],
                                highlightthickness=2)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Title
        title_font = font.Font(family="Segoe UI", size=24, weight="bold")
        title_label = tk.Label(header_frame, text="SARAPHINA",
                               font=title_font, fg=self.colors['accent'],
                               bg=self.colors['panel'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Status indicator
        self.status_label = tk.Label(header_frame, text="● ACTIVE",
                                     font=("Segoe UI", 10),
                                     fg=self.colors['success'],
                                     bg=self.colors['panel'])
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=15)

        # ===== MAIN CONTENT AREA =====
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left side - Conversation
        conv_frame = tk.Frame(content_frame, bg=self.colors['panel'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        conv_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Conversation title
        conv_title = tk.Label(conv_frame, text="CONVERSATION",
                              font=("Segoe UI", 11, "bold"),
                              fg=self.colors['dim'], bg=self.colors['panel'])
        conv_title.pack(anchor=tk.W, padx=15, pady=(10, 5))

        # Conversation display
        self.conversation = scrolledtext.ScrolledText(
            conv_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['bg'],
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=10
        )
        self.conversation.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.conversation.config(state=tk.DISABLED)

        # Configure tags for styling
        self.conversation.tag_config("user", foreground=self.colors['accent'],
                                     font=("Consolas", 10, "bold"))
        self.conversation.tag_config("saraphina", foreground=self.colors['accent2'],
                                     font=("Consolas", 10, "bold"))
        self.conversation.tag_config("system", foreground=self.colors['dim'],
                                     font=("Consolas", 9, "italic"))

        # Right side - Status panel
        status_frame = tk.Frame(content_frame, bg=self.colors['panel'],
                                highlightbackground=self.colors['border'],
                                highlightthickness=1, width=300)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        status_frame.pack_propagate(False)

        # Status title with settings button
        status_header = tk.Frame(status_frame, bg=self.colors['panel'])
        status_header.pack(fill=tk.X, padx=15, pady=(10, 15))

        status_title = tk.Label(status_header, text="SYSTEM STATUS",
                                font=("Segoe UI", 11, "bold"),
                                fg=self.colors['dim'], bg=self.colors['panel'])
        status_title.pack(side=tk.LEFT)

        settings_btn = tk.Button(status_header, text="⚙",
                                 font=("Segoe UI", 12),
                                 bg=self.colors['panel'], fg=self.colors['dim'],
                                 borderwidth=0, cursor="hand2",
                                 command=self.show_settings)
        settings_btn.pack(side=tk.RIGHT)

        # Stats display
        self.level_label = tk.Label(status_frame, text="Level: --",
                                    font=("Segoe UI", 10),
                                    fg=self.colors['text'], bg=self.colors['panel'])
        self.level_label.pack(anchor=tk.W, padx=20, pady=3)

        self.xp_label = tk.Label(status_frame, text="XP: --",
                                 font=("Segoe UI", 10),
                                 fg=self.colors['text'], bg=self.colors['panel'])
        self.xp_label.pack(anchor=tk.W, padx=20, pady=3)

        self.conv_label = tk.Label(status_frame, text="Conversations: --",
                                   font=("Segoe UI", 10),
                                   fg=self.colors['text'], bg=self.colors['panel'])
        self.conv_label.pack(anchor=tk.W, padx=20, pady=3)

        # Separator
        sep = tk.Frame(status_frame, height=1, bg=self.colors['border'])
        sep.pack(fill=tk.X, padx=15, pady=15)

        # Voice status
        self.voice_label = tk.Label(status_frame, text="🎤 Voice: Ready",
                                    font=("Segoe UI", 9),
                                    fg=self.colors['success'], bg=self.colors['panel'])
        self.voice_label.pack(anchor=tk.W, padx=20, pady=3)

        # Knowledge base
        self.kb_label = tk.Label(status_frame, text="📚 KB: -- facts",
                                 font=("Segoe UI", 9),
                                 fg=self.colors['text'], bg=self.colors['panel'])
        self.kb_label.pack(anchor=tk.W, padx=20, pady=3)

        # Chat history button
        sep2 = tk.Frame(status_frame, height=1, bg=self.colors['border'])
        sep2.pack(fill=tk.X, padx=15, pady=15)

        history_btn = tk.Button(status_frame, text="📜 View Chat History",
                                font=("Segoe UI", 9),
                                bg=self.colors['border'], fg=self.colors['text'],
                                borderwidth=0, cursor="hand2", padx=10, pady=5,
                                command=self.show_history)
        history_btn.pack(anchor=tk.W, padx=20, pady=5)

        # ===== INPUT AREA =====
        input_frame = tk.Frame(main_frame, bg=self.colors['panel'],
                              highlightbackground=self.colors['accent'],
                              highlightthickness=2)
        input_frame.pack(fill=tk.X, pady=(15, 0))

        # Input field
        self.input_field = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['accent'],
            borderwidth=0,
            highlightthickness=0
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=15, pady=12)
        self.input_field.bind('<Return>', self.send_message)
        self.input_field.focus()

        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="SEND",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['accent'],
            fg=self.colors['bg'],
            activebackground=self.colors['accent2'],
            activeforeground=self.colors['bg'],
            borderwidth=0,
            padx=25,
            pady=8,
            cursor="hand2",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=8)

    def init_saraphina(self):
        """Initialize Saraphina AI with full components in background"""
        def init():
            try:
                self.add_system_message("🚀 Initializing Saraphina Mission Control...")

                # Initialize database and knowledge engine
                try:
                    from saraphina.db import DB_FILE
                except Exception:
                    DB_FILE = REPO_ROOT / "ai_data" / "saraphina_knowledge.db"
                conn = init_db()  # This returns a connection
                try:
                    self.sess.ke = KnowledgeEngine(DB_FILE)
                except Exception:
                    # fallback: if KnowledgeEngine signature differs, try passing conn
                    try:
                        self.sess.ke = KnowledgeEngine(conn)
                    except Exception as e:
                        self.add_system_message(f"⚠ KnowledgeEngine init failed: {e}")

                # Initialize core AI
                try:
                    self.sess.ai = SaraphinaAIEnhanced(Path("ai_data"))
                except Exception as e:
                    self.add_system_message(f"⚠ SaraphinaAIEnhanced init failed: {e}")
                    self.sess.ai = None

                try:
                    self.sess.ultra = UltraAICore()
                except Exception:
                    self.sess.ultra = None

                if self.sess.ai:
                    self.add_system_message(f"✓ Core AI: Level {self.sess.ai.intelligence_level} | {self.sess.ai.experience_points} XP")
                else:
                    self.add_system_message("⚠ Core AI not fully initialized")

                # Initialize ALL support systems - FULL POWER
                systems_loaded = 0

                # Core systems (essential)
                try:
                    if self.sess.ke and hasattr(self.sess.ke, 'conn'):
                        ke_conn = self.sess.ke.conn
                    else:
                        ke_conn = conn
                    self.sess.mm = MemoryManager(ke_conn)
                    self.sess.mem = self.sess.mm
                    self.sess.emotion = EmotionEngine(ke_conn)
                    self.sess.sec = SecurityManager(Path("ai_data"))
                    self.sess.trust = TrustFirewall(ke_conn)
                    self.sess.beliefs = BeliefStore(ke_conn)
                    self.sess.reasoner = EthicalReasoner(self.sess.beliefs)
                    self.sess.planner = Planner()
                    self.sess.risk = RiskModel()
                    systems_loaded += 9
                except Exception as e:
                    self.add_system_message(f"⚠ Core system init issue: {e}")

                # Advanced systems (wrapped for safety)
                try:
                    self.sess.reviews = ReviewManager(DB_FILE)
                    systems_loaded += 1
                except:
                    pass

                try:
                    self.sess.persona = PersonaManager(ke_conn)
                    systems_loaded += 1
                except:
                    pass

                try:
                    self.sess.intuition = IntuitionEngine(ke_conn)
                    systems_loaded += 1
                except:
                    pass

                try:
                    self.sess.graph_explorer = KnowledgeGraphExplorer(ke_conn)
                    systems_loaded += 1
                except:
                    pass

                try:
                    self.sess.research = ResearchAgent(self.sess.ke)
                    systems_loaded += 1
                except:
                    pass

                try:
                    # Code factory may require CodeKnowledgeDB - lazy init
                    self.sess.code_kb = CodeKnowledgeDB(ke_conn)
                    self.sess.code_research = CodeResearchAgent(self.sess.code_kb)
                    self.sess.code_miner = RecursiveCodeMiner(self.sess.code_kb)
                    self.sess.code_factory = CodeFactory(self.sess.code_kb)
                    self.sess.test_harness = TestHarness()
                    systems_loaded += 4
                except:
                    pass

                try:
                    self.sess.code_proposals = CodeProposalDB(self.sess.ke.conn)
                    self.sess.refinement = RefinementEngine(self.sess.code_factory, self.sess.test_harness)
                    self.sess.improvement_db = ImprovementDB(self.sess.ke.conn)
                    self.sess.improvement_loop = ImprovementLoop(self.sess.improvement_db, self.sess.refinement)
                    systems_loaded += 4
                except:
                    pass

                try:
                    # Create hot_reload and rollback with sensible paths
                    self.sess.hot_reload = HotReloadManager(REPO_ROOT)
                    self.sess.rollback = RollbackEngine(Path("ai_data/backups"))
                    # SelfModificationEngine signature may vary; instantiate inside try
                    try:
                        # Preferred constructor if available: code_factory, proposal_db, security_manager, db
                        self.sess.self_mod = SelfModificationEngine(self.sess.code_factory, self.sess.code_proposals, self.sess.sec, ke_conn)
                    except Exception:
                        # Fallback: try older constructor signatures
                        try:
                            self.sess.self_mod = SelfModificationEngine(self.sess.ke.conn, self.sess.code_factory)
                        except Exception:
                            self.sess.self_mod = None
                    systems_loaded += 1
                except:
                    pass

                try:
                    self.sess.meta_architect = MetaArchitect(ke_conn)
                    self.sess.simulation = SimulationSandbox()
                    self.sess.arch_db = ArchitectureDB(ke_conn)
                    systems_loaded += 3
                except:
                    pass

                try:
                    self.sess.device = DeviceAgent()
                    systems_loaded += 1
                except:
                    pass

                self.add_system_message(f"✓ {systems_loaded} advanced systems loaded - FULL POWER!")

                # Initialize FULL Ultra processor if available
                try:
                    self.ultra_processor = GUIUltraProcessor(self.sess)
                except Exception:
                    self.ultra_processor = None

                # Initialize Self-Healing (Phase 29)
                try:
                    self.sess.self_healing = SelfHealingManager()
                    self.add_system_message("🏪 Self-Healing active - I auto-fix my own errors!")
                except Exception as e:
                    self.add_system_message(f"⚠ Self-Healing not initialized: {e}")

                # Initialize Self-Modification API - Complete control
                try:
                    self.sess.self_mod_api = SelfModificationAPI(self.sess, self)
                    self.add_system_message("⚙️ Self-Modification API active - I can change ANYTHING about myself!")
                except Exception as e:
                    self.add_system_message(f"⚠ Self-Modification API init failed: {e}")

                # Start background learning threads
                self.start_background_learning()

                # Initialize voice and STT
                try:
                    self.sess.stt = STT()
                    if VOICE_AVAILABLE and getattr(self.sess.stt, 'available', False):
                        self.sess.voice_enabled = True
                        self.add_system_message("✓ Voice system active - Always listening")
                        self.start_voice_listening()
                    else:
                        self.add_system_message("⚠ Voice system unavailable")
                except Exception:
                    self.add_system_message("⚠ STT initialization failed")

                # Set preferences
                try:
                    set_preference(conn, 'auto_listen', 'true')
                    if not get_preference(conn, 'wake_word'):
                        set_preference(conn, 'wake_word', 'saraphina')
                except Exception:
                    pass

                # Update status
                self.update_status()

                # Greeting
                try:
                    owner = get_preference(conn, 'owner_name') or 'there'
                except Exception:
                    owner = 'there'
                greeting = f"Hello {owner}! I'm Saraphina. I'm always listening and learning. How can I help you today?"
                self.add_message("Saraphina", greeting)

                if self.sess.voice_enabled:
                    threading.Thread(target=lambda: self.speak(greeting), daemon=True).start()

            except Exception as e:
                logger.error(f"Initialization error: {e}", exc_info=True)
                self.add_system_message(f"✗ Initialization error: {e}")

        threading.Thread(target=init, daemon=True).start()

    def update_status(self):
        """Update status panel"""
        if self.sess.ai:
            try:
                self.level_label.config(text=f"Level: {self.sess.ai.intelligence_level}")
                self.xp_label.config(text=f"XP: {self.sess.ai.experience_points}")
                self.conv_label.config(text=f"Conversations: {self.sess.ai.total_conversations}")
            except Exception:
                pass

        if self.sess.ke:
            try:
                cur = self.sess.ke.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM facts")
                fact_count = cur.fetchone()[0]
                self.kb_label.config(text=f"📚 KB: {fact_count} facts")
            except Exception:
                pass

        # Update voice status with animation
        if self.sess.voice_enabled:
            if self.is_speaking:
                self.voice_label.config(text="🔊 Speaking...", fg=self.colors['accent2'])
            elif self.is_listening:
                self.voice_label.config(text="🎤 Listening...", fg=self.colors['accent'])
            else:
                self.voice_label.config(text="🎤 Voice: Ready", fg=self.colors['success'])

    def add_message(self, speaker, message):
        """Add a message to conversation display"""
        try:
            self.conversation.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M")
            if speaker == "Saraphina":
                self.conversation.insert(tk.END, f"[{timestamp}] ", "system")
                self.conversation.insert(tk.END, f"{speaker}: ", "saraphina")
                self.conversation.insert(tk.END, f"{message}\n\n")
            else:
                self.conversation.insert(tk.END, f"[{timestamp}] ", "system")
                self.conversation.insert(tk.END, f"{speaker}: ", "user")
                self.conversation.insert(tk.END, f"{message}\n\n")
            self.conversation.see(tk.END)
            self.conversation.config(state=tk.DISABLED)
        except Exception:
            # If UI fails, log to console
            print(f"[MSG] {speaker}: {message}")

    def add_system_message(self, message):
        """Add a system message"""
        try:
            self.conversation.config(state=tk.NORMAL)
            self.conversation.insert(tk.END, f"[SYSTEM] {message}\n", "system")
            self.conversation.see(tk.END)
            self.conversation.config(state=tk.DISABLED)
        except Exception:
            print(f"[SYSTEM] {message}")

    def send_message(self, event=None):
        """Send user message"""
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        # Clear input
        self.input_field.delete(0, tk.END)

        # Increment conversation count
        if self.sess.ai:
            try:
                self.sess.ai.increment_conversation_count()
                # Update UI immediately
                self.conv_label.config(text=f"Conversations: {self.sess.ai.total_conversations}")
            except Exception:
                pass

        # Add to conversation
        owner = "You"
        if self.sess.ke:
            try:
                owner = get_preference(self.sess.ke.conn, 'owner_name') or "You"
            except:
                pass

        self.add_message(owner, user_input)

        # Stop current speech if speaking
        if self.sess.voice_enabled and VOICE_AVAILABLE:
            try:
                get_voice().stop_playback()
            except:
                pass

        # Process in background
        threading.Thread(target=self.process_input, args=(user_input,), daemon=True).start()

    def process_input(self, user_input):
        """Process user input with FULL Ultra AI integration"""
        try:
            if not self.sess.ai or not getattr(self, 'ultra_processor', None):
                self.add_system_message("⚠ AI not ready yet...")
                return

            # Use FULL Ultra processor with UI logging
            def ui_log(msg):
                self.add_system_message(msg)

            response = self.ultra_processor.process_query_with_ultra(user_input, ui_callback=ui_log)

            # Add response
            self.add_message("Saraphina", response)

            # Speak with emotion
            if self.sess.voice_enabled:
                self.speak(response)

            # Update stats
            self.update_status()

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            self.add_system_message(f"✗ Error: {e}")

    def process_messages(self):
        """Process message queue"""
        try:
            while True:
                msg = self.message_queue.get_nowait()
                # Placeholder for queued messages processing
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_messages)

    def animate_status(self):
        """Animate status indicators"""
        if not self.animation_running:
            return

        # Pulse the status indicator
        try:
            current_text = self.status_label.cget('text')
            if '●' in current_text:
                self.status_label.config(text=current_text.replace('●', '○'))
            else:
                self.status_label.config(text=current_text.replace('○', '●'))
        except Exception:
            pass

        # Schedule next animation frame (2 Hz = smooth pulse)
        self.root.after(500, self.animate_status)

    def start_voice_listening(self):
        """Start always-on voice listening in background"""
        if not self.sess.stt or not getattr(self.sess.stt, 'available', False):
            return

        try:
            wake_word = get_preference(self.sess.ke.conn, 'wake_word') or 'saraphina'
        except Exception:
            wake_word = 'saraphina'

        def voice_handler(text: str):
            """Handle voice input from background listening"""
            try:
                self.is_listening = True
                self.update_status()

                # Stop current playback (barge-in)
                if VOICE_AVAILABLE:
                    try:
                        get_voice().stop_playback()
                    except:
                        pass

                # Add to conversation
                try:
                    owner = get_preference(self.sess.ke.conn, 'owner_name') or 'You'
                except:
                    owner = 'You'
                self.add_message(f"{owner} (voice)", text)

                # Handle reminder intent
                if text.lower().startswith(('remind me', 'set a reminder')):
                    m = re.search(r"remind me to (.+) at (\d{1,2}:\d{2})", text, re.IGNORECASE)
                    if m and self.sess.mm:
                        what, when = m.group(1), m.group(2)
                        try:
                            self.sess.mm.add_reminder(what.strip(), datetime.now().strftime('%Y-%m-%d ') + when)
                            response = f"Okay, I'll remind you to {what} at {when}."
                            self.add_message("Saraphina", response)
                            if self.sess.voice_enabled:
                                self.speak(response)
                        except Exception:
                            self.add_system_message("⚠ Failed to schedule reminder.")
                        self.is_listening = False
                        self.update_status()
                        return

                # Process with Ultra AI using GUIUltraProcessor
                if getattr(self, 'ultra_processor', None):
                    response = self.ultra_processor.process_query_with_ultra(text)
                    self.add_message("Saraphina", response)

                    # Speak response
                    if self.sess.voice_enabled:
                        self.speak(response)

                # Update status
                self.update_status()
                self.is_listening = False

            except Exception as e:
                logger.error(f"Voice handler error: {e}", exc_info=True)
                self.is_listening = False
                self.update_status()

        # Start background listening
        try:
            self.sess.stt.start_background(voice_handler, engine='whisper', wake_word=wake_word)
            self.add_system_message(f"🎤 Always listening for '{wake_word}'...")
        except Exception as e:
            self.add_system_message(f"⚠ Failed to start background STT: {e}")

    def speak(self, text: str):
        """Speak text with emotion detection"""
        if not VOICE_AVAILABLE:
            if not hasattr(self, '_voice_error_logged'):
                self._voice_error_logged = True
                if VOICE_IMPORT_ERROR:
                    self.add_system_message(f"⚠️ Voice OUTPUT unavailable: {VOICE_IMPORT_ERROR}")
                else:
                    self.add_system_message("⚠️ Voice OUTPUT unavailable: VOICE_AVAILABLE = False")
            return

        try:
            self.is_speaking = True
            self.update_status()

            # Strip markdown
            clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)
            clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)
            clean_text = re.sub(r'`(.+?)`', r'\1', clean_text)
            # Additional sanitization to avoid saying symbols
            clean_text = re.sub(r"\[[^\]]+\]", " ", clean_text)  # remove [SYSTEM] tags
            clean_text = clean_text.replace('=', ' ')
            clean_text = re.sub(r"[_]{1,}", ' ', clean_text)
            clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()

            # Speak
            speak_text(clean_text)

            self.is_speaking = False
            self.update_status()

        except Exception as e:
            logger.error(f"Speech error: {e}", exc_info=True)
            self.is_speaking = False
            self.update_status()

    def on_closing(self):
        """Handle window close"""
        try:
            self.animation_running = False

            # Stop voice systems
            if self.sess.stt and getattr(self.sess.stt, 'available', False):
                try:
                    self.sess.stt.stop_background()
                except Exception:
                    pass

            if VOICE_AVAILABLE:
                try:
                    get_voice().cleanup()
                except:
                    pass

            # Save AI state
            if self.sess.ai:
                try:
                    self.sess.ai._save_state()
                except Exception:
                    pass

            logger.info("Shutting down Saraphina GUI")

        except Exception as e:
            logger.error(f"Shutdown error: {e}", exc_info=True)

        try:
            self.root.destroy()
        except Exception:
            pass

    def start_background_learning(self):
        """Start background threads for continuous learning and improvement"""

        def learning_loop():
            """Background learning - analyzes patterns and improves strategies"""
            import time
            while self.animation_running:
                try:
                    time.sleep(300)  # Every 5 minutes

                    if self.sess.metaopt:
                        # Analyze learning health
                        health = self.sess.metaopt.analyze_learning_health()
                        if health.get('overall_health') == 'poor':
                            self.add_system_message("🛠️ Analyzing learning patterns...")

                        # Propose optimizations
                        proposals = self.sess.metaopt.propose_optimizations()
                        if proposals:
                            self.add_system_message(f"💡 Found {len(proposals)} optimization opportunities")

                except Exception as e:
                    logger.debug(f"Learning loop error: {e}")

        def memory_consolidation():
            """Background memory consolidation - converts episodic to semantic"""
            import time
            while self.animation_running:
                try:
                    time.sleep(3600)  # Every hour

                    if self.sess.mm:
                        try:
                            added = self.sess.mm.consolidate_daily()
                            if added > 0:
                                self.add_system_message(f"🧠 Consolidated {added} memories")
                        except Exception:
                            pass

                except Exception as e:
                    logger.debug(f"Memory consolidation error: {e}")

        def health_monitor():
            """Monitor system health and optimize"""
            import time
            while self.animation_running:
                try:
                    time.sleep(1800)  # Every 30 minutes

                    # Check if need more knowledge
                    if self.sess.ke:
                        try:
                            cur = self.sess.ke.conn.cursor()
                            cur.execute("SELECT COUNT(*) FROM facts")
                            fact_count = cur.fetchone()[0]

                            if fact_count < 100:
                                self.add_system_message("👶 Still learning... Need more conversations to grow smarter!")
                            elif fact_count % 100 == 0:
                                self.add_system_message(f"🎉 Milestone: {fact_count} facts learned!")
                        except Exception:
                            pass

                except Exception as e:
                    logger.debug(f"Health monitor error: {e}")

        # Start background threads
        threading.Thread(target=learning_loop, daemon=True).start()
        threading.Thread(target=memory_consolidation, daemon=True).start()
        threading.Thread(target=health_monitor, daemon=True).start()

        self.add_system_message("🧠 Background learning active - I'm continuously improving!")

    def show_settings(self):
        """Show settings dialog"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("500x350")
        settings_win.configure(bg=self.colors['bg'])

        # Header
        header = tk.Label(settings_win, text="SARAPHINA SETTINGS",
                          font=("Segoe UI", 16, "bold"),
                          fg=self.colors['accent'], bg=self.colors['bg'])
        header.pack(pady=20)

        # Settings frame
        settings_frame = tk.Frame(settings_win, bg=self.colors['panel'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Info text
        info = tk.Label(settings_frame,
                        text="Settings are managed in the main database.\nRestart the GUI to apply changes.",
                        font=("Segoe UI", 9), fg=self.colors['dim'],
                        bg=self.colors['panel'], justify=tk.LEFT)
        info.pack(padx=15, pady=15)

        # Status info
        status_text = f"""Current Status:

Level: {self.sess.ai.intelligence_level if self.sess.ai else '--'}
XP: {self.sess.ai.experience_points if self.sess.ai else '--'}
Voice: {'Enabled' if self.sess.voice_enabled else 'Disabled'}
AI Model: GPT-4o via OpenAI"""

        status_label = tk.Label(settings_frame, text=status_text,
                                font=("Consolas", 9), fg=self.colors['text'],
                                bg=self.colors['bg'], justify=tk.LEFT)
        status_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Close button
        close_btn = tk.Button(settings_frame, text="CLOSE",
                              font=("Segoe UI", 10, "bold"),
                              bg=self.colors['border'], fg=self.colors['text'],
                              borderwidth=0, padx=30, pady=10,
                              cursor="hand2", command=settings_win.destroy)
        close_btn.pack(pady=20)

    def show_history(self):
        """Show chat history dialog"""
        history_win = tk.Toplevel(self.root)
        history_win.title("Chat History")
        history_win.geometry("700x600")
        history_win.configure(bg=self.colors['bg'])

        # Header
        header = tk.Label(history_win, text="CONVERSATION HISTORY",
                          font=("Segoe UI", 16, "bold"),
                          fg=self.colors['accent'], bg=self.colors['bg'])
        header.pack(pady=20)

        # History display
        history_frame = tk.Frame(history_win, bg=self.colors['panel'])
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        history_text = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=10
        )
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Get history from conversation display instead of DB (thread-safe)
        try:
            conv_content = self.conversation.get("1.0", tk.END)
            history_text.insert(tk.END, conv_content)
        except Exception:
            history_text.insert(tk.END, "[No conversation available]\n")
        history_text.config(state=tk.DISABLED)

        # Close button
        close_btn = tk.Button(history_win, text="CLOSE",
                              font=("Segoe UI", 10, "bold"),
                              bg=self.colors['border'], fg=self.colors['text'],
                              borderwidth=0, padx=30, pady=10,
                              cursor="hand2", command=history_win.destroy)
        close_btn.pack(pady=(0, 20))


def main():
    """Launch Saraphina GUI"""
    root = tk.Tk()

    # Set app icon if available
    try:
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
    except:
        pass

    # Create GUI
    app = SaraphinaGUI(root)

    # Start
    root.mainloop()


if __name__ == '__main__':
    main()