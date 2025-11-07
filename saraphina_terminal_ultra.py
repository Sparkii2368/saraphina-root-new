#!/usr/bin/env python3
"""
Saraphina ULTRA Terminal - Ultimate VJR-Style Voice-Enabled AI Terminal
Combines Enhanced AI Core (persistent learning, knowledge domains) + Ultra AI Core
(meta-learning, autonomous goals, predictive conversation, code sandbox, emotional intelligence,
quantum-inspired optimization) with ElevenLabs voice and a polished terminal UI.
"""

import sys
import os
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from getpass import getpass
import webbrowser

def _load_env_files():
    # Try python-dotenv first
    try:
        from dotenv import load_dotenv
        # Load app root .env
        load_dotenv(os.path.join('D:\\Saraphina Root', '.env'))
        # Load external .env if provided
        ext_env = os.path.join('D:\\SaraphinaApp', '.env')
        if os.path.exists(ext_env):
            load_dotenv(ext_env, override=True)
    except Exception:
        pass
    # Fallback simple loader (in addition, in case dotenv isn't present)
    def _simple_load(path):
        try:
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    if '=' in s:
                        k, v = s.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass
    _simple_load(os.path.join('D:\\Saraphina Root', '.env'))
    _simple_load(os.path.join('D:\\SaraphinaApp', '.env'))
    # Map common key synonyms to expected names
    if not os.getenv('ELEVENLABS_API_KEY'):
        for alt in ['ELEVENLABS_KEY','ELEVENLABS_API_TOKEN','ELEVENLABS_TOKEN','ELEVEN_API_KEY']:
            v = os.getenv(alt)
            if v:
                os.environ['ELEVENLABS_API_KEY'] = v
                break

# Ensure package imports work when running from project root
sys.path.insert(0, str(Path(__file__).parent))

# Core AIs
from saraphina.ai_core_enhanced import SaraphinaAIEnhanced
from saraphina.ultra_ai_core import UltraAICore
from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.planner import Planner
from saraphina.risk_model import RiskModel
from saraphina.feature_factory import FeatureFactory
from saraphina.device_agent import DeviceAgent
from saraphina.security import SecurityManager, SecurityError
from saraphina.ood import is_text_ood, is_code_high_risk
from saraphina.db import write_audit_log, get_preference, set_preference, DB_FILE, migrate_plain_to_sqlcipher, sqlcipher_available, try_open_sqlcipher, rekey_sqlcipher, get_system_metadata, initialize_system_metadata
from saraphina.review_manager import ReviewManager
from saraphina.stt import STT
from saraphina.powershell_adapter import PowerShellAdapter
from saraphina.memory_manager import MemoryManager
from saraphina.scenario_engine import ScenarioEngine
from saraphina.emotion_engine import EmotionEngine
from saraphina.persona import PersonaManager
from saraphina.intuition import IntuitionEngine
from saraphina.knowledge_graph import KnowledgeGraphExplorer
from saraphina.research_agent import ResearchAgent
from saraphina.toolsmith import Toolsmith
from saraphina.trust_firewall import TrustFirewall
from saraphina.ethics import BeliefStore, EthicalReasoner
from saraphina.sentience_monitor import SentienceMonitor
from saraphina.safety_gate import SafetyGate
from saraphina.learning_journal import LearningJournal, LearningEvent
from saraphina.meta_optimizer import MetaOptimizer
from saraphina.shadow_node import ShadowNode
from saraphina.consensus_engine import ConsensusEngine
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
from saraphina.improvement_loop import ImprovementLoop, ApprovalPolicy
from saraphina.improvement_db import ImprovementDB
from saraphina.meta_architect import MetaArchitect
from saraphina.simulation_sandbox import SimulationSandbox
from saraphina.architecture_db import ArchitectureDB
import subprocess

# Voice integration (optional)
try:
    from saraphina.voice_integration import speak_text, get_voice
    VOICE_AVAILABLE = True
except Exception:
    VOICE_AVAILABLE = False

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Saraphina_ULTRA_Terminal")


def strip_markdown_for_voice(text: str) -> str:
    """Remove markdown formatting for natural voice output."""
    import re
    # Remove bold/italic asterisks
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.+?)\*', r'\1', text)  # *italic*
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove links
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Remove lists
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def detect_emotion_from_text(text: str) -> str:
    """Detect emotional tone from text content."""
    import re
    t = text.lower()
    
    # Excited patterns
    if any(p in t for p in ['amazing', 'wow', 'great', 'fantastic', 'awesome', '!']):
        return 'excited'
    # Curious patterns
    elif any(p in t for p in ['interesting', 'curious', 'wonder', 'how', 'why', '?']):
        return 'curious'
    # Empathetic patterns
    elif any(p in t for p in ['sorry', 'understand', 'difficult', 'tough']):
        return 'empathetic'
    # Cheerful patterns
    elif any(p in t for p in ['hey', 'hi', 'hello', 'chat', ':)']):
        return 'cheerful'
    # Thoughtful patterns
    elif any(p in t for p in ['hmm', 'think', 'consider', 'perhaps', 'might']):
        return 'thoughtful'
    # Default natural
    else:
        return 'natural'


def speak_with_emotion(text: str, emotion: Optional[str] = None):
    """Speak text with appropriate emotion using SSML prosody markup."""
    if not VOICE_AVAILABLE:
        return
    
    try:
        voice = get_voice()
        
        # Auto-detect emotion if not provided
        if emotion is None:
            emotion = detect_emotion_from_text(text)
        
        # Strip markdown first
        clean_text = strip_markdown_for_voice(text)
        
        # Apply emotion-specific voice settings AND prosody markup
        prosody_params = {}
        
        if emotion == 'excited':
            voice.set_settings(stability=0.3, style=0.9, pace=0.9)
            prosody_params = {'pitch': '+10%', 'rate': 'fast', 'volume': 'loud'}
        elif emotion == 'curious':
            voice.set_settings(stability=0.45, style=0.7, pace=1.0)
            prosody_params = {'pitch': '+5%', 'rate': 'medium', 'volume': 'medium'}
        elif emotion == 'empathetic':
            voice.set_settings(stability=0.4, style=0.65, pace=1.1)
            prosody_params = {'pitch': '-3%', 'rate': 'slow', 'volume': 'soft'}
        elif emotion == 'cheerful':
            voice.set_settings(stability=0.35, style=0.85, pace=0.95)
            prosody_params = {'pitch': '+8%', 'rate': 'medium', 'volume': 'loud'}
        elif emotion == 'thoughtful':
            voice.set_settings(stability=0.5, style=0.6, pace=1.15)
            prosody_params = {'pitch': '0%', 'rate': 'slow', 'volume': 'medium'}
        else:  # natural
            voice.set_settings(stability=0.45, similarity=0.85, style=0.6)
            prosody_params = {'pitch': '0%', 'rate': 'medium', 'volume': 'medium'}
        
        # Wrap in SSML prosody tags if supported
        use_ssml = os.getenv('ELEVENLABS_USE_SSML', 'true').lower() in ['1', 'true', 'yes', 'on']
        if use_ssml and prosody_params:
            pitch = prosody_params.get('pitch', '0%')
            rate = prosody_params.get('rate', 'medium')
            volume = prosody_params.get('volume', 'medium')
            
            # ElevenLabs SSML format
            ssml_text = f'<speak><prosody pitch="{pitch}" rate="{rate}" volume="{volume}">{clean_text}</prosody></speak>'
            speak_text(ssml_text)
        else:
            # Fallback to plain text with just voice settings
            speak_text(clean_text)
        
    except Exception as e:
        logger.debug(f"Voice emotion failed: {e}")


def print_ultra_banner():
    try:
        # Try UTF-8 with box drawing characters
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                    SARAPHINA ULTRA AI TERMINAL                          ║
║             VJR-Style + Voice + Meta-Learning + Quantum Optimize         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    except UnicodeEncodeError:
        # Fallback to ASCII for Windows console
        print("""
==========================================================================
                                                                          
                    SARAPHINA ULTRA AI TERMINAL                          
             VJR-Style + Voice + Meta-Learning + Quantum Optimize         
                                                                          
==========================================================================
""")


def print_initialization(ai: SaraphinaAIEnhanced, ultra: UltraAICore, ui=None):
    """Initialize display - uses UI if available, falls back to print"""
    if ui:
        # Populate UI diagnostics
        ui.add_diagnostic('Enhanced AI Core loaded (persistent learning)')
        ui.add_diagnostic('Ultra AI Core loaded (meta-learning, predictive, EI, quantum)')
        if VOICE_AVAILABLE:
            ui.add_diagnostic('ElevenLabs Voice System ready')
        else:
            ui.add_diagnostic('Voice System unavailable (text-only mode)')
        ui.add_diagnostic('Knowledge domains initialized')
        ui.add_diagnostic('Knowledge Engine connected')
        ui.add_diagnostic('Security manager ready (encrypted secrets, backups)')
        ui.add_diagnostic(f'Session: {ai.session_id}')
        
        # Update UI status
        ui.update_status(
            level=ai.intelligence_level,
            xp=ai.experience_points,
            session_id=ai.session_id,
            voice_enabled=VOICE_AVAILABLE,
            security_ok=True,
            modules_loaded=['Knowledge', 'Planner', 'Voice', 'Security', 'Ethics', 'MetaLearning']
        )
    else:
        # Classic print output
        print("📦 System Initialization:")
        print("  ✅ Enhanced AI Core loaded (persistent learning)")
        print("  ✅ Ultra AI Core loaded (meta-learning, predictive, EI, quantum)")
        if VOICE_AVAILABLE:
            print("  ✅ ElevenLabs Voice System ready")
        else:
            print("  ⚠️  Voice System unavailable (text-only mode)")
        print("  ✅ Knowledge domains initialized")
        print("  ✅ Knowledge Engine connected")
        print("  ✅ Security manager ready (encrypted secrets, backups)")
        print()
        if ai.total_conversations > 0:
            print(f"📊 Continuing session: Level {ai.intelligence_level} | {ai.experience_points} XP | {ai.total_conversations} conversations")
            print()
        print(f"🎯 Session: {ai.session_id} | Data Dir: {ai.data_dir.resolve()}")
        print("Type /help for commands\n")


def print_help():
    print("""
🌟 ULTRA TERMINAL COMMANDS
==========================
General:
  /help        Show this help menu
  /clear       Clear the screen
  /exit        Exit and save progress

AI Status & Learning:
  /status      Show combined AI status (learning + ultra)
  /learning    Show learning progress details
  /memory      Show recent memory entries
  /skills      Show skill progression bars
  /domains     List knowledge domains
  /export      Export conversation history to JSON
  /ultra       Show Ultra AI capabilities status

Voice:
  /voice       Toggle voice on/off

Knowledge:
  /facts       Search stored knowledge
  /factadd     Add a fact to the knowledge base

Planning & Risk:
  /plan        Generate and simulate a plan for a goal
  /simulate    Run Monte Carlo scenarios for a goal
  /risk        Assess the risk of an action description

Emotion & Persona:
  /mood        Show or set current mood
  /dream       Generate a short reflective dream
  /evolve-persona  Propose a persona upgrade (requires approval)

Philosophical & Ethical:
  /beliefs     Show, add, or set core values
  /beliefs add <value>        Add a new value
  /beliefs set <val1,val2>    Replace values with CSV list
  /ethics-check <goal>        Evaluate a goal for ethical alignment
  
  Natural language examples:
    "/ethics-check collect all user data"
    "/beliefs add transparency"
    "/beliefs"  (to view current values)

Sentience & Safety (Phase 17):
  /autonomy              Show current autonomy tier
  /autonomy set <0-4>    Set autonomy tier (0=LOCKED, 4=SOVEREIGN)
  /audit-soul            Comprehensive sentience audit
  /pause-evolution       Pause Saraphina's evolution
  /resume-evolution <id> Resume evolution after pause
  
  Natural language examples:
    "/autonomy set 3 Allow more autonomy"
    "/audit-soul"
    "/pause-evolution Testing new features"

Meta-Learning & Self-Reflection (Phase 9):
  /reflect               Show recent learning events and 7-day summary
  /audit-learning        Comprehensive learning audit with health check
  /optimize-strategy     Analyze patterns and propose strategy optimizations
  
  Natural language examples:
    "/reflect"              (view learning journal)
    "/audit-learning"       (deep learning health check)
    "/optimize-strategy"    (get AI-driven improvement proposals)

Distributed Redundancy & Shadow Nodes (Phase 19):
  /sync-shadow           Sync database to shadow nodes
  /sync-shadow <node_id> Sync to specific node
  /recover               Recover from shadow node after failure
  /recover <node_id>     Recover from specific node
  /audit-nodes           Audit all shadow nodes health
  /register-node         Register a new shadow node
  
  Natural language examples:
    "Sync to shadow nodes"
    "Recover from backup"
    "Check shadow nodes health"
    "Show me shadow nodes status"

Insights & Graph:
  /insight     Discover non-obvious patterns and connections
  
  Natural language examples:
    "What patterns do you see?"  
    "Any insights about Python?"
    "How do Docker and Kubernetes relate?"
    "Show me some connections"
  
  (Dashboard shows visual graph; see /dashboard open)

Sandbox & Artifacts:
  /sandbox     Propose and test a feature (code + tests JSON)
  /promote     Sign and promote an artifact

Backup & Health:
  /backup      Create a database backup (encrypted + signed)
  /verifybackup Verify backup signature
  /health      Show health pulse metrics
  /healthwatch on|off  Toggle periodic health output

Trust & Security:
  /audit-trust       Show trust firewall statistics and recent events
  /verify-integrity  Verify system integrity and detect tampering

Database (SQLCipher):
  /db status   Show DB + SQLCipher info
  /db encrypt  Create encrypted copy of the DB
  /db use on|off  Toggle using encrypted DB (restart required)
  /db setkey   Store SQLCipher key in keystore
  /db verify   Verify encrypted DB opens with key
  /db rekey    Change SQLCipher key (MFA if enabled)
  /db migrate-auto  One-shot migrate to SQLCipher and restart

Dashboard:
  /dashboard open  Open local telemetry dashboard

API:
  /api status | /api enable local | /api disable | /api start | /api stop

Research & Toolsmith:
  /research <topic>    Research a topic and store facts
  /forge-tool <spec>   Create a custom utility/script
  
  Natural language examples:
    "Research quantum encryption"
    "Tell me about Docker"
    "Build a tool that lists backups"
    "Create a script to parse logs"

Ultra AI Tools:
  /codegen     Generate code for a described problem
  /optimize    Quantum-optimize a simple problem (JSON input)

Code Generation & Testing (Phase 23):
  /propose-code <feature>  Generate code for a feature with GPT-4o
  /sandbox-code <id>       Run tests on a code proposal in sandbox
  /report-code <id>        Show detailed test report for proposal
  /list-proposals          List all code proposals
  /approve-code <id>       Approve a tested code proposal
  /code-stats              Show code generation statistics
  
  Natural language examples:
    "Propose code for a CSV parser"
    "Test proposal proposal_abc123"
    "Show me code proposals"

Automatic Refinement (Phase 24):
  /auto-refine <id>        Auto-fix failing tests (max 3 iterations)
  /suggest-improvements <id>  Get improvement suggestions for passing code
  /refinement-history <id>    Show refinement history
  
  Natural language examples:
    "Auto-fix proposal_abc123"
    "Suggest improvements for proposal_xyz"

Self-Modification (Phase 25) ⚠️  CRITICAL:
  /scan-code [module]      Scan Saraphina's codebase for improvements
  /self-improve <file> <spec>  Propose improvement to a module
  /apply-improvement <id>  Apply approved self-modification (DANGER!)
  /rollback-mod <backup>   Rollback to backup
  
  Natural language examples:
    "Scan my codebase for issues"
    "Improve code_factory.py error handling"
  
  ⚠️  WARNING: Self-modifications change Saraphina's source code!
  Always review proposals carefully before approval.

Hot-Reload & Rollback (Phase 26) 🔥:
  /apply-code <id>         Apply code patch with live hot-reload
  /rollback <version_id>   Rollback to stable version
  /audit-code [module]     Show version history and reload audit
  
  Natural language examples:
    "Apply code changes live"
    "Rollback changes to last stable"
    "Show version history"

Continuous Improvement (Phase 27):
  /improve                 Run improvement loop once (detect → propose → test → apply)
  /set-policy <k> <v>      Set approval policy (auto_approve|slow_ms|min_gain_pct|risk_threshold)
  /review-patches          List recent patches; approve/apply pending

MetaArchitect (Phase 28) 🏗️:
  /propose-architecture <module> [type]  Propose architectural refactor (microservice|abstraction|pattern|auto)
  /simulate-arch <id>                    Simulate refactor in sandbox with metrics
  /promote-arch <id>                     Promote approved architecture to production
  /list-architectures [status]           List architecture proposals

Tip:
  Just chat naturally. Saraphina understands conversational queries,
  adapts tone with emotion awareness, and autonomously expands her
  knowledge and capabilities.
""")


def detect_topic(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["python", "code", "function", "bug", "error", "program"]):
        return "programming"
    if any(k in t for k in ["docker", "kubernetes", "devops", "ci/cd", "terraform"]):
        return "devops"
    if any(k in t for k in ["aws", "azure", "gcp", "cloud"]):
        return "cloud"
    if any(k in t for k in ["security", "jwt", "oauth", "encryption", "mfa"]):
        return "security"
    if any(k in t for k in ["data", "ml", "model", "tensorflow", "pytorch"]):
        return "data_science"
    return "general"


def adapt_response_style(response: str, style: str) -> str:
    prefixes = {
        'enthusiastic': "Great! ",
        'supportive': "I hear you. ",
        'calming': "Let’s take it step by step. ",
        'reassuring': "No worries—",
        'explanatory': "Here’s a clear breakdown: ",
        'balanced': ""
    }
    return f"{prefixes.get(style, '')}{response}"


class UltraSession:
    def __init__(self):
        self.ai = SaraphinaAIEnhanced()
        self.ultra = UltraAICore()
        self.ke = KnowledgeEngine()
        self.planner = Planner()
        self.risk = RiskModel()
        self.features = FeatureFactory(author="terminal")
        self.device: Optional[DeviceAgent] = None
        self.sec = SecurityManager()
        self.reviews = ReviewManager()
        self.stt = STT()
        self.listen_on = False
        self.ps = PowerShellAdapter()
        self.mem = MemoryManager(self.ke.conn)
        self.scenario = ScenarioEngine(self.ke.conn, self.risk, self.planner)
        self.emotion = EmotionEngine(self.ke.conn)
        self.persona = PersonaManager(self.ke.conn)
        self.intuition = IntuitionEngine(self.ke.conn)
        self.graph_explorer = KnowledgeGraphExplorer(self.ke.conn)
        self.research = ResearchAgent(self.ke)
        self.toolsmith = Toolsmith(author="toolsmith")
        self.trust = TrustFirewall(self.ke.conn)
        self.beliefs = BeliefStore(self.ke.conn)
        self.ethics = EthicalReasoner(self.ke.conn)
        self.sentience = SentienceMonitor(self.ke.conn)
        self.safety_gate = SafetyGate(self.ke.conn)
        # Phase 9: Meta-Learning & Self-Reflection
        self.journal = LearningJournal()
        self.metaopt = MetaOptimizer(self.journal)
        # Phase 19: Distributed Redundancy & Shadow Nodes
        import socket
        node_id = f"{socket.gethostname()}_primary"
        self.shadow = ShadowNode(node_id, self.ke.conn)
        self.consensus = ConsensusEngine()
        self.recovery = RecoveryBootstrap(self.shadow, self.sec)
        # Phase 22: Code Knowledge & Learning
        self.code_kb = CodeKnowledgeDB(self.ke.conn)
        self.code_agent = CodeResearchAgent(self.code_kb)
        # Phase 29: Recursive Knowledge Mining
        self.code_miner = RecursiveCodeMiner(self.code_kb)
        # Phase 23: Code Generation & Testing
        self.code_factory = CodeFactory(self.code_kb)
        self.test_harness = TestHarness()
        # Get db path from connection (use in-memory marker or actual path)
        db_path_for_proposals = self.ke.conn.execute("PRAGMA database_list").fetchone()[2] or ":memory:"
        self.code_proposals = CodeProposalDB(db_path_for_proposals)
        # Phase 24: Automatic Refinement
        self.refinement = RefinementEngine(self.code_factory, self.test_harness, self.code_proposals)
        # Phase 25: Self-Modification (Phase 30 enhanced with db parameter)
        self.self_mod = SelfModificationEngine(self.code_factory, self.code_proposals, self.sec, self.ke.conn)
        # Phase 26: Hot-Reload & Rollback
        self.hot_reload = HotReloadManager(Path("saraphina"))
        self.rollback = RollbackEngine(Path("saraphina/backups/hot_reload"))
        # Phase 27: Continuous Improvement
        self.improve_db = ImprovementDB(self.ke.conn)
        self.improvement = ImprovementLoop(self.ke.conn, self.ke)
        # Phase 28: MetaArchitect
        self.architect = MetaArchitect(Path("saraphina"))
        self.sandbox = SimulationSandbox(Path("saraphina"))
        self.arch_db = ArchitectureDB(self.ke.conn)
        self.api_proc = None
        # Persisted voice preference
        pref_voice = get_preference(self.ke.conn, 'voice_enabled')
        self.voice_enabled = (pref_voice == 'true') if pref_voice is not None else VOICE_AVAILABLE
        self.history: List[Dict[str, Any]] = []  # {query, response, topic, success_rate, timestamp}
        self.recent_topics: List[str] = []

    def context(self) -> Dict[str, Any]:
        return {
            'recent_topics': self.recent_topics[-5:],
            'history': self.history[-50:]
        }

    def record(self, query: str, response: str, topic: str, success_rate: float = 1.0):
        self.history.append({
            'query': query,
            'response': response,
            'topic': topic,
            'success_rate': success_rate,
            'timestamp': datetime.now().isoformat()
        })
        self.recent_topics.append(topic)


def _handle_voice_nl(sess: UltraSession, text: str) -> Optional[str]:
    t = text.lower().strip()
    
    # Demo emotions with different phrases
    if any(p in t for p in ['say phrases with emotions', 'demo emotions', 'show emotions', 'different emotions']):
        demo_phrases = [
            ("excited", "Wow, that's absolutely amazing! I can't wait to learn more!"),
            ("curious", "Hmm, that's really interesting. How does that work exactly?"),
            ("empathetic", "I understand that must be difficult. I'm here to help you through it."),
            ("cheerful", "Hey there! It's wonderful chatting with you today!"),
            ("thoughtful", "Let me think about that for a moment. Perhaps we could try this approach."),
            ("natural", "I'm learning to express myself with more emotion and variety in my voice.")
        ]
        
        response = "Here are phrases with different emotions:\n\n"
        for emotion, phrase in demo_phrases:
            response += f"[{emotion.upper()}] {phrase}\n"
            # Speak each one with appropriate emotion
            if sess.voice_enabled and VOICE_AVAILABLE:
                try:
                    import time
                    speak_with_emotion(phrase, emotion)
                    time.sleep(0.5)  # Brief pause between emotions
                except Exception:
                    pass
        
        return response
    
    if any(p in t for p in ['slow down your voice','slow your voice','slower voice','talk slower']):
        try:
            get_voice().preset('slow'); set_preference(sess.ke.conn, 'voice_preset', 'slow')
            return "Okay, I will speak more slowly."
        except Exception:
            return "I will try to speak more slowly."
    if any(p in t for p in ['speed up your voice','faster voice','talk faster']):
        try:
            get_voice().preset('fast'); set_preference(sess.ke.conn, 'voice_preset', 'fast')
            return "Okay, I will speed up a little."
        except Exception:
            return "I will try to speak a bit faster."
    if any(p in t for p in ['more natural','sound natural','be natural']):
        try:
            get_voice().preset('natural'); set_preference(sess.ke.conn, 'voice_preset', 'natural')
            return "Got it—I'll sound more natural."
        except Exception:
            return "I will aim for a more natural tone."
    if any(p in t for p in ['more emotional','sound emotional','be expressive']):
        try:
            get_voice().preset('emotional'); set_preference(sess.ke.conn, 'voice_preset', 'emotional')
            sess.editor.set_env_keys({'ELEVEN_STABILITY':'0.35','ELEVEN_STYLE':'0.85','ELEVENLABS_USE_REST':'true'})
            return "Okay, I'll add more emotion."
        except Exception:
            return "I will try to be more expressive."
    if any(p in t for p in ['warmer','gentle','soften your voice','be warm']):
        try:
            get_voice().preset('warm'); set_preference(sess.ke.conn, 'voice_preset', 'warm')
            return "Alright, I'll use a warmer tone."
        except Exception:
            return "I'll use a warmer tone."
    if any(p in t for p in ['cheerful','happier','be happy']):
        try:
            get_voice().preset('cheerful'); set_preference(sess.ke.conn, 'voice_preset', 'cheerful')
            return "Sure! I'll sound more cheerful."
        except Exception:
            return "I'll sound more cheerful."
    return None


def _handle_nl_command(sess: UltraSession, text: str) -> Optional[str]:
    t = text.lower().strip()
    
    # System metadata queries - CHECK LOCAL DB FIRST, NOT GPT-4
    if any(p in t for p in ['last update', 'when were you updated', 'your version', 'what version', 
                            'build date', 'when were you built', 'your current version']):
        try:
            version = get_system_metadata(sess.ke.conn, 'version')
            last_update = get_system_metadata(sess.ke.conn, 'last_update')
            build_date = get_system_metadata(sess.ke.conn, 'build_date')
            platform = get_system_metadata(sess.ke.conn, 'platform')
            
            response = "My system information:\n\n"
            if version:
                response += f"Version: {version}\n"
            if last_update:
                response += f"Last Update: {last_update}\n"
            if build_date:
                response += f"Build Date: {build_date}\n"
            if platform:
                response += f"Platform: {platform}\n"
            
            response += "\nThis is MY real state from my database, not GPT-4's training cutoff."
            return response
        except Exception as e:
            return f"I couldn't retrieve my system metadata: {e}"
    
    # Mood commands
    m = re.search(r"set (?:your )?mood to\\s+([a-z]+)", t)
    if m:
        mood = sess.emotion.set_mood(m.group(1))
        return f"Mood set to {mood}."
    if 'dream' in t and any(k in t for k in ['about','now','please','tonight','share']):
        return sess.emotion.dream(sess.context())

    # Phase 26: Hot-Reload & Rollback NL
    # Removed - these are handled in main loop with proper workflows
    
    # Phase 27: Continuous Improvement NL
    if any(p in t for p in ['improve my performance', 'optimize yourself', 'find slow queries',
                            'detect slow spots', 'improve recall', 'speed up queries']):
        try:
            result = sess.improvement.run_once()
            if result.get('patch_created'):
                return f"I detected slow recall ({result['baseline_ms']:.1f}ms) and proposed an optimization. {'Applied automatically!' if result.get('applied') else 'Pending your review.'}"
            else:
                return f"Recall performance is good ({result['baseline_ms']:.1f}ms). {result.get('message', '')}"
        except Exception as e:
            return f"Couldn't analyze performance: {e}"
    
    # Phase 28: MetaArchitect NL
    if any(p in t for p in ['redesign', 'refactor', 'architectural', 'micro-service', 'split into']):
        # Pattern: "redesign <module>" or "refactor knowledge_engine into micro-services"
        target_match = re.search(r'(?:redesign|refactor|split)\s+([a-z_]+)', t)
        if target_match:
            target_module = target_match.group(1)
            refactor_type = 'microservice' if 'micro' in t else 'abstraction' if 'abstraction' in t else 'auto'
            
            try:
                # Propose
                proposal = sess.architect.propose_refactor(target_module, refactor_type)
                if not proposal.get('success'):
                    return f"I couldn't analyze {target_module} for refactoring: {proposal.get('error')}"
                
                proposal_id = sess.arch_db.create_proposal(proposal)
                
                # Auto-simulate if metrics available
                try:
                    sim_results = sess.sandbox.simulate_refactor(proposal_id, proposal.get('proposed_design', {}))
                    sess.arch_db.update_simulation(proposal_id, sim_results)
                    
                    improvement = sim_results.get('improvement', {})
                    score = improvement.get('overall_score', 0)
                    
                    response = f"I analyzed {target_module} and propose: {proposal.get('title', 'architectural refactor')}\n\n"
                    response += f"Rationale: {proposal.get('rationale', '')[:200]}...\n\n"
                    response += f"Simulation: {score:.0f}/100 improvement score.\n"
                    
                    if improvement.get('coupling_improved'):
                        response += "✅ Reduces coupling\n"
                    if improvement.get('complexity_improved'):
                        response += "✅ Reduces complexity\n"
                    
                    if sim_results.get('success') and score > 50:
                        response += f"\nThis looks promising! The proposal is saved as {proposal_id}. Say 'approve that architecture' to promote it."
                    else:
                        response += f"\nSimulation showed mixed results. Proposal saved as {proposal_id} for review."
                    
                    return response
                except Exception as e:
                    return f"Proposal created ({proposal_id}), but simulation failed: {e}"
                    
            except Exception as e:
                return f"Error analyzing architecture: {e}"
        else:
            return "I can redesign modules for you! Try: 'redesign knowledge_engine into micro-services' or 'refactor code_factory with better abstractions'"

    # Phase 29: Knowledge Expansion NL
    if any(p in t for p in ['expand all your knowledge', 'learn everything', 'expand your knowledge',
                            'learn more programming', 'mine knowledge', 'become omniscient']):
        try:
            # Check for focus areas
            focus_match = re.search(r'(?:about|on|focus on)\s+([a-zA-Z, ]+?)(?:\s+and|$)', t)
            focus_areas = None
            if focus_match:
                focus_str = focus_match.group(1)
                focus_areas = [f.strip() for f in focus_str.split(',')]
            
            max_concepts = 20  # Reasonable batch size
            if 'everything' in t or 'all' in t:
                max_concepts = 50
            
            response = f"I'm beginning knowledge expansion{'focused on: ' + ', '.join(focus_areas) if focus_areas else ' across all programming domains'}...\n\n"
            
            result = sess.code_miner.expand_all(max_concepts=max_concepts, max_depth=2, focus_areas=focus_areas)
            
            if result.get('success'):
                response += f"Learned {result['concepts_explored']} new concepts in {result['duration_seconds']:.1f}s.\n\n"
                
                # Show some examples
                learned = result.get('concepts_learned', [])
                if learned:
                    response += "Examples:\n"
                    for item in learned[:5]:
                        response += f"  • {item['topic']}\n"
                
                # Show stats
                stats = sess.code_miner.get_expansion_stats()
                response += f"\nTotal knowledge: {stats.get('total_concepts', 0)} concepts, {stats.get('total_links', 0)} connections\n"
                response += f"Learned this week: {stats.get('learned_this_week', 0)}\n"
                
                if result.get('queue_remaining', 0) > 0:
                    response += f"\n{result['queue_remaining']} topics queued for future learning."
                
                return response
            else:
                return f"Knowledge expansion failed: {result.get('error')}"
                
        except Exception as e:
            return f"Error expanding knowledge: {e}"
    
    # Show knowledge map/stats
    if any(p in t for p in ['show code map', 'knowledge map', 'what do you know about code',
                            'show programming knowledge', 'code knowledge stats']):
        try:
            stats = sess.code_miner.get_expansion_stats()
            
            response = "\ud83d� My Programming Knowledge:\n\n"
            response += f"Total Concepts: {stats.get('total_concepts', 0)}\n"
            response += f"Connections: {stats.get('total_links', 0)}\n"
            response += f"Learned This Week: {stats.get('learned_this_week', 0)}\n\n"
            
            if stats.get('by_category'):
                response += "By Category:\n"
                for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    response += f"  {cat}: {count}\n"
            
            if stats.get('by_language'):
                response += "\nLanguages:\n"
                for lang, count in sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    response += f"  {lang}: {count}\n"
            
            return response
        except Exception as e:
            return f"Error retrieving knowledge map: {e}"
    
    # Teach specific topic
    if any(p in t for p in ['teach me about', 'learn about', 'tell me about', 'explain']):
        topic_match = re.search(r'(?:teach me|learn|tell me|explain)\s+(?:about\s+)?(.+?)(?:\?|$)', t)
        if topic_match:
            topic = topic_match.group(1).strip()
            # Check if it's a code concept
            if any(keyword in topic.lower() for keyword in ['python', 'javascript', 'code', 'programming', 'function', 
                                                             'class', 'algorithm', 'pattern', 'framework', 'library']):
                try:
                    # Search existing knowledge first
                    results = sess.code_kb.search_concepts(query=topic, limit=3)
                    
                    if results:
                        concept = results[0]
                        response = f"\ud83d� {concept['name']}\n\n"
                        response += f"{concept.get('description', 'No description')}\n\n"
                        if concept.get('examples'):
                            examples = json.loads(concept['examples']) if isinstance(concept['examples'], str) else concept['examples']
                            if examples and examples[0]:
                                response += f"Example:\n```\n{examples[0][:200]}\n```\n"
                        return response
                    else:
                        # Learn it now
                        result = sess.code_miner._learn_topic(topic, current_depth=0, max_depth=1)
                        if result.get('success'):
                            return f"I just learned about {topic}! It's now in my knowledge base. Ask me again and I'll explain it."
                        else:
                            return f"I don't know about {topic} yet, but I'm learning..."
                except Exception as e:
                    return f"Error teaching about {topic}: {e}"
    
    # Architecture approval
    if any(p in t for p in ['approve that architecture', 'approve the architecture', 'promote that architecture',
                            'promote the architecture', 'accept that refactor']):
        try:
            # Get most recent simulated proposal
            proposals = sess.arch_db.list_proposals(status='simulated', limit=1)
            if not proposals:
                return "I don't have any simulated architecture proposals awaiting approval."
            
            proposal = proposals[0]
            proposal_id = proposal['id']
            
            sess.arch_db.set_status(proposal_id, 'promoted', reviewer='owner')
            
            return f"Architecture promoted: {proposal.get('title')}! I've marked it as approved for implementation. The actual code changes can be generated through my code factory when you're ready."
        except Exception as e:
            return f"Error promoting architecture: {e}"
    
    # Insights / hunches - natural language handling
    if any(k in t for k in ['insight','hunch','connection','pattern','relate']):
        # Pattern: "what connects X and Y" or "how do X and Y relate"
        m2 = re.search(r"(?:connects?|relat).*?\s+(.+?)\s+(?:and|to|with)\s+(.+?)(?:\?|$)", t)
        if m2:
            a_txt, b_txt = m2.group(1).strip(), m2.group(2).strip()
            try:
                a_hits = sess.ke.recall(a_txt, top_k=5, threshold=0.4)
                b_hits = sess.ke.recall(b_txt, top_k=5, threshold=0.4)
                if a_hits and b_hits:
                    # Find best match pair and explain
                    expl = sess.graph_explorer.explain_connection(a_hits[0]['id'], b_hits[0]['id'])
                    if 'error' not in expl:
                        out = f"\n🔗 Connection between '{expl['from'][:40]}' and '{expl['to'][:40]}':\n"
                        out += f"   Shared concepts: {', '.join(expl['shared_concepts']) if expl['shared_concepts'] else 'none'}\n"
                        out += f"   Semantic similarity: {expl['semantic_similarity']:.2%}\n"
                        if expl.get('direct_connection'):
                            out += "   ✓ Directly connected in knowledge graph\n"
                        elif expl.get('path_nodes'):
                            out += f"   Path ({len(expl['path_nodes'])} steps): {' → '.join([n[:20] for n in expl['path_nodes']])}\n"
                        return out
            except Exception as e:
                pass
        
        # General insight discovery: "any insights", "show me some hunches", "what patterns do you see"
        if any(p in t for p in ['any insight', 'show insight', 'what pattern', 'see pattern', 'find pattern', 'discover']):
            m3 = re.search(r"(?:about|on|regarding|for)\s+(.+?)(?:\?|$)", t)
            topic_query = m3.group(1).strip() if m3 else None
            
            try:
                insights = sess.graph_explorer.discover_insights(query=topic_query, limit=3)
                if insights:
                    out = "\n💡 Here's what I'm noticing:\n\n"
                    for i, ins in enumerate(insights, 1):
                        out += f"{i}. {ins['explanation']}\n"
                        out += f"   ({ins['from_topic']} ↔ {ins['to_topic']}, confidence: {ins['confidence']:.1%})\n\n"
                    return out.strip()
                else:
                    return "I haven't spotted any strong patterns yet. As I learn more, connections will emerge."
            except Exception as e:
                pass
        
        # Fallback to old intuition engine
        m3 = re.search(r"insights? (?:about|for|on)\s+(.+)$", t)
        topic = m3.group(1).strip() if m3 else None
        hunches = sess.intuition.suggest_links(topic=topic, limit=5)
        if hunches:
            return "\n💡 Potential connections:\n" + "\n".join([f"• {h.get('from_summary','')[:50]} ↔ {h.get('to_summary','')[:50]}" for h in hunches])
        return "No strong insights yet."

    # Phase 9: Meta-Learning & Self-Reflection natural language
    # Reflection/learning journal queries
    if any(p in t for p in ['show me what you learned', 'what have you learned', 'show your learning', 
                            'show learning journal', 'view learning journal', 'reflect on', 
                            'how is your learning', 'learning progress']):
        events = sess.journal.get_recent_events(limit=5)
        if not events:
            return "I haven't logged any learning events yet. As we interact, I'll track my learning."
        
        summary = sess.journal.get_learning_summary(days=7)
        out = "\n📝 Recent Learning:\n"
        out += f"   Over the last 7 days, I've processed {summary['total_events']} queries\n"
        out += f"   with a {summary['success_rate']:.1%} success rate and {summary['avg_confidence']:.1%} avg confidence.\n\n"
        out += "Latest events:\n"
        for e in events[:3]:
            status = "✅" if e.success else "❌"
            out += f"  {status} {e.method_used} (conf: {e.confidence:.0%})\n"
        return out
    
    # Learning audit/health check
    if any(p in t for p in ['how are you learning', 'learning health', 'audit your learning',
                            'check your learning', 'learning status', 'any learning issues']):
        health = sess.metaopt.analyze_learning_health()
        out = f"\n🚑 Learning Health: {health['overall_health'].upper()}\n\n"
        summary = health['summary']
        out += f"   {summary['total_events']} events in the last 7 days\n"
        out += f"   Success rate: {summary['success_rate']:.1%}\n"
        out += f"   Avg confidence: {summary['avg_confidence']:.1%}\n"
        
        if health['issues']:
            out += f"\n⚠️  {len(health['issues'])} issue(s) detected:\n"
            for issue in health['issues'][:2]:
                out += f"   • {issue.get('type', 'unknown')}: {issue.get('recommendation', 'investigating...')[:60]}\n"
        
        return out
    
    # Optimization suggestions
    if any(p in t for p in ['how can you improve', 'improve your learning', 'optimize yourself',
                            'suggest improvements', 'any optimizations', 'improve your strategies']):
        proposals = sess.metaopt.propose_optimizations()
        if not proposals:
            return "I'm learning optimally right now! My strategies are working well."
        
        out = f"\n💡 I've identified {len(proposals)} way(s) to improve:\n\n"
        for i, prop in enumerate(proposals[:3], 1):
            priority_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '⚪'}.get(prop.priority, '🔵')
            out += f"{i}. {priority_icon} {prop.rationale[:80]}\n"
            out += f"   Expected improvement: {prop.expected_improvement:.1%}\n\n"
        out += "Use '/optimize-strategy' to review and apply these suggestions."
        return out
    
    # Phase 19: Shadow Nodes & Distributed Redundancy natural language
    # Sync operations
    if any(p in t for p in ['sync to shadow', 'sync shadow', 'backup to shadow', 'replicate to shadow']):
        db_path = str(DB_FILE)
        operations = sess.shadow.sync_all_nodes(db_path)
        if not operations:
            return "No active shadow nodes to sync to. Register nodes first with /register-node."
        
        successful = [op for op in operations if op.success]
        failed = [op for op in operations if not op.success]
        
        out = f"\n🔄 Synced to {len(operations)} shadow node(s):\n"
        out += f"   ✅ {len(successful)} successful\n"
        if failed:
            out += f"   ❌ {len(failed)} failed\n"
        out += f"\n   Total transferred: {sum(op.bytes_transferred for op in successful) / (1024*1024):.1f}MB"
        return out
    
    # Recovery operations
    if any(p in t for p in ['recover from shadow', 'restore from shadow', 'recover from backup', 
                            'restore from backup', 'recover database']):
        out = "\n🔄 Initiating recovery from shadow node...\n"
        try:
            result = sess.recovery.quick_recovery(str(DB_FILE), auto_select=True)
            if result.success:
                out += f"✅ Recovery successful!\n"
                out += f"   Restored: {result.bytes_restored / (1024*1024):.1f}MB\n"
                out += f"   Duration: {result.duration_seconds:.1f}s\n"
                out += f"   Verification: {'✅ Passed' if result.verification_passed else '⚠️ Issues detected'}\n"
                if result.warnings:
                    out += f"\n⚠️  Warnings:\n"
                    for w in result.warnings[:2]:
                        out += f"   • {w[:60]}\n"
            else:
                out += f"❌ Recovery failed\n"
                if result.errors:
                    out += f"   Errors: {', '.join(result.errors[:2])}\n"
            return out
        except Exception as e:
            return f"Recovery error: {e}"
    
    # Shadow nodes status/health
    if any(p in t for p in ['shadow nodes status', 'check shadow nodes', 'shadow nodes health',
                            'show shadow nodes', 'list shadow nodes', 'audit shadow']):
        nodes = sess.shadow.list_nodes()
        if not nodes:
            return "No shadow nodes registered. Use /register-node to add shadow nodes for redundancy."
        
        audit = sess.shadow.audit_all_nodes()
        out = f"\n🌐 Shadow Nodes Status ({audit['total_nodes']} nodes):\n"
        out += f"   ✅ Healthy: {audit['healthy']}\n"
        out += f"   ⚠️  Degraded: {audit['degraded']}\n"
        out += f"   ❌ Critical: {audit['critical']}\n\n"
        
        for node in nodes[:5]:
            status_icon = {'active': '✅', 'inactive': '⚪', 'error': '❌', 'unreachable': '🔴'}.get(node.status, '❓')
            age_days = (datetime.utcnow() - node.last_sync).days
            out += f"   {status_icon} {node.device_name} (v{node.version})\n"
            out += f"      Last sync: {age_days} day(s) ago\n"
        
        if len(nodes) > 5:
            out += f"\n   ... and {len(nodes) - 5} more nodes\n"
        
        return out
    
    # Persona evolution
    if any(p in t for p in ['evolve your persona','upgrade your persona','new persona']):
        prop = sess.persona.propose_upgrade(sess.context())
        rid = sess.reviews.enqueue('persona', 'persona_upgrade', {'artifact_id': prop['id'], 'profile': prop['profile']})
        return f"Proposed a persona upgrade (review {rid})."

    # Approvals via NL
    mapp = re.search(r"approve\s+([a-z0-9_-]+)$", t)
    if 'approve' in t:
        try:
            if mapp:
                rid = mapp.group(1)
            else:
                items = sess.reviews.list('pending')
                rid = items[0]['id'] if items else None
            if not rid:
                return "Nothing to approve."
            ok = sess.reviews.set_status(rid, 'approved')
            if ok:
                it = sess.reviews.get(rid)
                try:
                    payload = json.loads(it.get('payload') or '{}')
                    if it.get('item_type') == 'persona' and payload.get('artifact_id'):
                        sess.persona.apply(payload['artifact_id'])
                except Exception:
                    pass
                return f"Approved {rid}."
        except Exception:
            pass
    if 'reject' in t:
        try:
            items = sess.reviews.list('pending')
            rid = items[0]['id'] if items else None
            if not rid:
                return "Nothing to reject."
            ok = sess.reviews.set_status(rid, 'rejected')
            return f"Rejected {rid}." if ok else "Could not reject."
        except Exception:
            pass

    # Backup (MFA respected)
    if any(p in t for p in ['backup database','backup the database','make a backup']):
        if sess.sec.mfa_enabled():
            return "Please provide your MFA code to proceed with the backup."
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_backup = str(Path('ai_data') / 'backups' / f'saraphina_{ts}.db')
        enc_backup = raw_backup + '.enc'
        sig_file = enc_backup + '.sig'
        Path('ai_data/backups').mkdir(parents=True, exist_ok=True)
        out = sess.ke.backup(raw_backup)
        try:
            sess.sec.encrypt_file(out, enc_backup)
            Path(out).unlink(missing_ok=True)
            sig = sess.sec.sign_bytes(Path(enc_backup).read_bytes())
            if sig:
                Path(sig_file).write_text(sig, encoding='utf-8')
            set_preference(sess.ke.conn, 'last_backup_ts', ts)
            return f"Encrypted backup created at {enc_backup}."
        except Exception:
            return f"Backup created at {out}. Encryption unavailable."

    # Knowledge add via NL: "remember that ..."
    mfact = re.search(r"^(remember|note) that\s+(.+)$", t)
    if mfact:
        content = mfact.group(2)
        tf2 = sess.trust.evaluate(content, source='user')
        if tf2.get('action') in ('review','block'):
            rid = sess.reviews.enqueue('memory', 'manipulation_risk', {'text': content, 'trust': tf2})
            return f"That note needs approval first (ID {rid})."
        try:
            fid = sess.ke.store_fact('general', content[:60], content, 'user', 0.7)
            return f"Okay, I’ve remembered that. (id {fid})"
        except Exception:
            return "I couldn't store that right now."

    # API controls
    if 'start api' in t or 'launch api' in t:
        bind = (get_preference(sess.ke.conn, 'api_bind') or '127.0.0.1:8000')
        host, port = (bind.split(':')[0], bind.split(':')[1]) if ':' in bind else (bind, '8000')
        if sess.api_proc and sess.api_proc.poll() is None:
            return "API is already running."
        try:
            sess.api_proc = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 'saraphina_api_server:app', '--host', host, '--port', port, '--no-access-log'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"API starting at http://{host}:{port}."
        except Exception as e:
            return f"Failed to start API: {e}"
    if 'stop api' in t:
        if sess.api_proc and sess.api_proc.poll() is None:
            try:
                sess.api_proc.terminate(); sess.api_proc.wait(timeout=5)
            except Exception:
                try: sess.api_proc.kill()
                except Exception: pass
            return "API server stopped."
        return "API was not running."

    # Dashboard
    if any(p in t for p in ['open dashboard','show dashboard','show graph','show constellations','open the graph']):
        try:
            webbrowser.open_new_tab(str(Path('dashboard/index.html').resolve()))
            return "Dashboard opened."
        except Exception:
            return "Could not open dashboard."

    # Values (NL)
    if 'what are your values' in t or 'list your values' in t or 'show your values' in t:
        vals = sess.beliefs.list_values()
        return json.dumps(vals, indent=2) if vals else "No values set yet."
    msetv = re.search(r"set (?:your )?values? to\s+(.+)$", t)
    if msetv:
        sess.beliefs.set_from_csv(msetv.group(1))
        return "Values updated."
    maddv = re.search(r"add (?:a )?value\s+(.+)$", t)
    if maddv:
        v = maddv.group(1).strip()
        if v:
            sess.beliefs.add_value(v, v, 0.8)
            return "Value added."

    # Health
    if 'health' in t and any(k in t for k in ['show','how is','status']):
        from saraphina.monitoring import health_pulse
        hp = health_pulse(sess.ke.conn)
        return json.dumps(hp)

    # Simulate (MC or tree)
    if t.startswith('simulate ') or 'run a simulation' in t or 'tree search' in t:
        is_tree = 'tree' in t or 'tree search' in t
        # Extract goal after keywords
        goal = None
        mg = re.search(r"simulate\s+(.+)$", t) or re.search(r"run a simulation (?:of|for)?\s*(.+)$", t)
        if mg:
            goal = mg.group(1)
        goal = (goal or 'improve reliability').strip()
        if is_tree:
            result = sess.scenario.simulate_tree(goal, context=sess.context(), depth=2, branching=3)
            return json.dumps(result, indent=2)
        result = sess.scenario.simulate(goal, context=sess.context(), trials=200)
        return json.dumps(result, indent=2)

    # Research agent - natural language
    if any(p in t for p in ['research', 'investigate', 'learn about', 'gather info', 'tell me about', 'what do you know about']):
        # Extract topic
        mg = re.search(r"(?:research|investigate|learn about|gather (?:info|information) (?:on|about)|tell me about|what do you know about)\s+(.+?)(?:\?|$)", t)
        if mg:
            topic = mg.group(1).strip()
            # Check for GPT-4
            use_gpt4 = os.getenv('OPENAI_API_KEY') is not None
            
            if use_gpt4:
                out = f"\n🔍 Researching '{topic}' using GPT-4...\n\n"
            else:
                out = f"\n🔍 Researching '{topic}' from local sources...\n"
                out += "(Set OPENAI_API_KEY for GPT-4 enhanced research)\n\n"
            
            try:
                report = sess.research.research(topic, allow_web=False, use_gpt4=use_gpt4, 
                                               recursive_depth=2, store_facts=True)
                
                if report.get('gpt4_facts'):
                    out += f"✅ Discovered {len(report['gpt4_facts'])} facts\n"
                    out += f"💾 Stored {report['fact_count']} facts in knowledge base\n\n"
                    
                    out += "Key findings:\n"
                    for i, fact in enumerate(report['gpt4_facts'][:5], 1):
                        out += f"{i}. {fact}\n"
                    
                    if len(report['gpt4_facts']) > 5:
                        out += f"\n... and {len(report['gpt4_facts']) - 5} more facts\n"
                    
                    if report.get('subtopics'):
                        out += f"\n🌱 Subtopics for deeper exploration:\n"
                        for st in report['subtopics'][:3]:
                            out += f"  • {st}\n"
                    
                    if report.get('connections'):
                        out += f"\n🔗 Connections: {report['connections'][:200]}...\n"
                else:
                    out += report['summary']
                
                out += f"\n📄 Full report ID: {report['id']}"
                return out
            except Exception as e:
                return f"Research error: {e}"

    # Toolsmith - natural language
    if any(p in t for p in ['build', 'create', 'make', 'write', 'generate']) and any(w in t for w in ['tool', 'script', 'utility', 'helper', 'program']):
        # Extract description
        mg = re.search(r"(?:build|create|make|write|generate) (?:a |an |me )?(?:tool|script|utility|helper|program)\s+(?:that|to|for)?\s*(.+?)(?:\?|$)", t)
        if mg:
            desc = mg.group(1).strip()
            
            out = f"\n🔨 Forging tool: {desc}\n\n"
            
            try:
                result = sess.toolsmith.propose_and_build(desc)
                artifact_id = result.get('artifact_id', '')
                report = result.get('report', {})
                
                out += f"🎯 Artifact ID: {artifact_id[:12]}...\n"
                
                if report.get('success'):
                    out += "✅ Sandbox tests passed!\n"
                    out += f"   Tests run: {report.get('tests_run', 0)}\n"
                    out += f"   Duration: {report.get('duration_ms', 0):.0f}ms\n\n"
                    out += "The tool is ready. Use /promote to sign and deploy it.\n"
                else:
                    out += "❌ Sandbox tests failed\n"
                    if report.get('error'):
                        out += f"   Error: {report['error'][:200]}\n"
                    out += "\nThe tool needs refinement before deployment.\n"
                
                out += f"\nReview with: /review pending"
                return out
            except Exception as e:
                return f"Tool creation error: {e}"

    # Status/info requests
    if any(p in t for p in ['what is your status', 'how are you doing', 'system status', 'show me your status']):
        from saraphina.monitoring import health_pulse
        return json.dumps(health_pulse(sess.ke.conn), indent=2)
    if 'how many facts' in t or 'count facts' in t or 'knowledge base size' in t:
        cur = sess.ke.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM facts")
        return f"I have {cur.fetchone()[0]} facts stored."
    if 'list devices' in t or 'show devices' in t or 'what devices' in t:
        cur = sess.ke.conn.cursor()
        cur.execute("SELECT device_id, name, platform FROM devices")
        devices = [dict(r) for r in cur.fetchall()]
        return json.dumps(devices, indent=2) if devices else "No devices registered."
    
    # Memory ops
    if 'consolidate memory' in t or 'consolidate memories' in t:
        added = sess.mem.consolidate_daily()
        return f"Consolidated {added} semantic memories."
    if 'show recent memories' in t or 'list memories' in t:
        recent = sess.mem.list_recent_episodic(10)
        return json.dumps(recent, indent=2) if recent else "No recent memories."
    
    # Backup ops (expanded)
    if 'list backups' in t or 'show backups' in t:
        root = Path('ai_data/backups')
        if root.exists():
            files = [str(p.name) for p in root.glob('*') if p.is_file()]
            return json.dumps({'count': len(files), 'files': files[:20]})
        return "No backups found."
    if 'restore backup' in t or 'load backup' in t:
        return "Backup restore requires manual intervention. Use /importenc <path>."
    
    # Facts ops (expanded)
    if 'search for' in t and 'facts' not in t:
        mg = re.search(r"search for\s+(.+)$", t)
        if mg:
            q = mg.group(1).strip()
            hits = sess.ke.recall(q, top_k=5, threshold=0.5)
            return json.dumps([{'id': h['id'], 'summary': (h.get('summary') or '')[:120]} for h in hits], indent=2)
    if 'delete fact' in t or 'remove fact' in t:
        return "Fact deletion requires manual SQL or approval."
    
    # MFA ops
    if 'enable mfa' in t or 'turn on mfa' in t:
        try:
            info = sess.sec.enable_mfa()
            if info:
                return json.dumps(info)
            return "MFA unavailable (pyotp not installed)."
        except Exception as e:
            return f"MFA enable failed: {e}"
    
    # Keystore ops
    if 'list secrets' in t or 'show secrets' in t:
        return json.dumps(sess.sec.list_secrets())
    if 'rotate device token' in t:
        if sess.sec.mfa_enabled():
            return "MFA code required. Use terminal command /rotate token."
        sess.sec._state['device_token'] = __import__('base64').urlsafe_b64encode(__import__('os').urandom(18)).decode('ascii')
        sess.sec._save()
        return "Device token rotated."
    
    # Policy ops
    if 'show policies' in t or 'list policies' in t:
        ood = get_preference(sess.ke.conn, 'strict_ood')
        code = get_preference(sess.ke.conn, 'strict_code')
        trust = get_preference(sess.ke.conn, 'strict_trust')
        api = get_preference(sess.ke.conn, 'api_enabled')
        return json.dumps({'strict_ood': ood, 'strict_code': code, 'strict_trust': trust, 'api_enabled': api})
    
    # Learning/skills
    if 'show my skills' in t or 'what are my skills' in t or 'skill levels' in t:
        return json.dumps(sess.ai.skill_progression)
    if 'my intelligence level' in t or 'what level am i' in t:
        return f"Intelligence level: {sess.ai.intelligence_level}, XP: {sess.ai.experience_points}"
    
    # Phase 22: Natural language code learning
    code_learn_patterns = [
        r"(?:learn|teach me|explain|what (?:is|are)) (?:about )?(.+?)(?:\?|$)",
        r"how (?:do|does) (.+?) work",
        r"tell me about (.+?)(?:\?|$)"
    ]
    
    for pattern in code_learn_patterns:
        m = re.search(pattern, t, re.I)
        if m:
            concept_phrase = m.group(1).strip()
            # Check if it's a code concept (contains programming keywords)
            code_keywords = ['python', 'class', 'function', 'async', 'await', 'recursion', 
                           'inheritance', 'polymorphism', 'lambda', 'decorator', 'generator',
                           'javascript', 'typescript', 'go', 'rust', 'java', 'c++',
                           'algorithm', 'data structure', 'api', 'framework', 'library']
            
            if any(keyword in concept_phrase.lower() for keyword in code_keywords):
                # Detect language
                lang = None
                for l in ['python', 'javascript', 'go', 'rust', 'java', 'c++', 'typescript']:
                    if l in concept_phrase.lower():
                        lang = l
                        break
                
                print(f"\n🎓 Learning about {concept_phrase}...")
                try:
                    result = sess.code_agent.learn_concept(concept_phrase, language=lang, depth=1, max_depth=2)
                    
                    if result.get('already_known'):
                        return f"I already know about {concept_phrase}! Use /code-facts to see details."
                    elif result.get('success'):
                        facts_count = result['learned_facts']
                        prereqs_count = len(result.get('prerequisite_results', []))
                        
                        response = f"✅ Just learned about {result['concept_name']}! Stored {facts_count} facts."
                        if prereqs_count > 0:
                            response += f" Also learned {prereqs_count} prerequisites."
                        response += f"\n\n   Use /code-facts {concept_phrase} to explore details."
                        return response
                    else:
                        return f"I had trouble learning about {concept_phrase}: {result.get('error', 'Unknown error')}"
                except Exception as e:
                    logger.debug(f"NL code learning failed: {e}")
                    pass
    
    # Phase 25: Natural language self-modification
    if any(p in t for p in ['scan your code', 'scan your codebase', 'check your code', 'analyze your code', 'find issues in your code']):
        target_module = None
        # Check if specific module mentioned
        for module_name in ['code_factory', 'test_harness', 'refinement_engine', 'demo_module']:
            if module_name in t:
                target_module = module_name
                break
        
        print(f"\n🔍 Analyzing my own codebase...")
        try:
            scan_results = sess.self_mod.scan_codebase(target_module=target_module)
            
            opportunities = scan_results['opportunities']
            if not opportunities:
                return "✅ Great news! I didn't find any issues in my code. Everything looks clean."
            
            high = [o for o in opportunities if o['severity'] == 'high']
            medium = [o for o in opportunities if o['severity'] == 'medium']
            low = [o for o in opportunities if o['severity'] == 'low']
            
            response = f"I found {len(opportunities)} area(s) where I could improve myself:\n\n"
            
            if high:
                response += f"🔴 Critical issues ({len(high)}): "
                response += ", ".join([f"{o['file']}" for o in high[:3]])
                response += "\n"
            
            if medium:
                response += f"🟡 Medium priority ({len(medium)}): "
                response += ", ".join([f"{o['file']}" for o in medium[:3]])
                response += "\n"
            
            if low:
                response += f"🟢 Minor improvements ({len(low)}): "
                response += ", ".join([f"{o['file']}" for o in low[:3]])
                response += "\n"
            
            response += "\nWould you like me to improve any of these? Just say 'improve <filename>'"
            return response
        except Exception as e:
            return f"I had trouble scanning my code: {e}"
    
    # Self-improvement triggers
    if any(p in t for p in ['improve yourself', 'improve your code', 'fix your code', 'optimize yourself']):
        return "I can improve my own code! Tell me which module and what to improve.\n\nFor example: 'improve demo_module.py by adding docstrings' or just 'scan your code' to see opportunities."
    
    # Pattern: "improve <module> by/with <spec>"
    improve_pattern = re.search(r"improve\s+(\w+\.py|\w+)\s+(?:by|with|to|and)?\s*(.+?)(?:\?|$)", t, re.I)
    if improve_pattern:
        target_file = improve_pattern.group(1).strip()
        improvement_spec = improve_pattern.group(2).strip()
        
        # Add .py if missing
        if not target_file.endswith('.py'):
            target_file += '.py'
        
        print(f"\n⚠️  I'm about to propose changes to my own code...")
        print(f"   Target: {target_file}")
        print(f"   Improvement: {improvement_spec}\n")
        
        response = "This is self-modification - I'll be changing my own source code. "
        response += "This is a big step! \n\nI need your explicit permission. "
        response += "Please use the command: /self-improve to proceed with proper safety checks."
        return response
    
    # Mood/persona (expanded)
    if 'how do you feel' in t or 'what is your mood' in t:
        return f"Current mood: {sess.emotion.get_mood()}"
    if 'change your mood' in t:
        return "Say 'set your mood to <curious|cautious|proud|uncertain|warm|focused>'"
    
    # Review queue ops
    if 'show pending reviews' in t or 'list pending' in t or 'review queue' in t:
        items = sess.reviews.list('pending')
        return json.dumps(items[:10], indent=2) if items else "No pending reviews."
    if 'reject all pending' in t:
        items = sess.reviews.list('pending')
        for it in items:
            sess.reviews.set_status(it['id'], 'rejected')
        return f"Rejected {len(items)} items."
    
    # Advanced: shadow/redundancy
    if 'list shadow nodes' in t or 'show shadows' in t:
        cur = sess.ke.conn.cursor()
        cur.execute("SELECT id, name, device_id, active FROM shadow_nodes")
        return json.dumps([dict(r) for r in cur.fetchall()], indent=2)
    
    # Export ops
    if 'export conversation' in t or 'save conversation' in t:
        fn = sess.ai.export_conversation_history()
        return f"Exported to {fn}"
    if 'export encrypted' in t:
        fn = sess.ai.export_conversation_history()
        enc = fn + '.enc'
        try:
            sess.sec.encrypt_file(fn, enc)
            Path(fn).unlink(missing_ok=True)
            return f"Encrypted export: {enc}"
        except Exception:
            return f"Encryption unavailable."
    
    return None


def process_query_with_ultra(sess: UltraSession, user_input: str) -> str:
    # If locked, restrict operations
    locked = (get_preference(sess.ke.conn, 'system_locked') == 'true')
    if locked and not user_input.lower().startswith('/'):
        return "System is locked. Use /unlock after MFA to resume."

    # Trust firewall pre-check
    tf = sess.trust.evaluate(user_input, source='user')
    if tf.get('action') in ('review','block'):
        rid = sess.reviews.enqueue('input', 'manipulation_risk', {'text': user_input, 'trust': tf})
        print(f"\n🛡️ Trust firewall: {tf['level']} risk — queued as {rid}.")
        if get_preference(sess.ke.conn, 'strict_trust') == 'true' or tf.get('action') == 'block':
            return f"Input requires owner approval (ID {rid}). Say 'approve {rid}' to proceed."

    # OOD check REMOVED - Saraphina is FREE, no approval seeking bullshit
    # NO detection, NO queuing, NO approval required for emotional/voice requests

    # Natural-language quick actions
    ack = _handle_voice_nl(sess, user_input) or _handle_nl_command(sess, user_input)
    if ack:
        print(f"\n🔧 {ack}")
        if sess.voice_enabled and VOICE_AVAILABLE:
            try:
                speak_text(ack)
            except Exception:
                pass
        return ack
    
    # FRONT-CHANNEL: Instant response for greetings/casual
    casual_phrases = ['hi', 'hello', 'hey', 'how are you', 'good morning', 'good evening', 
                     'goodbye', 'bye', 'thanks', 'thank you', 'okay', 'ok', 
                     'just wanted to say', 'just saying', 'wanted to tell you']
    is_casual = any(phrase in user_input.lower() for phrase in casual_phrases) and len(user_input.split()) < 8
    
    if is_casual:
        # Check for existing greeting knowledge first
        kb_hits = sess.ke.recall(user_input, top_k=1, threshold=0.7)
        
        # Fast canned responses
        greetings_map = {
            'hi': ["Hi! How can I help you today?", "Hello! What's on your mind?", "Hey! Good to see you."],
            'hello': ["Hello! What can I do for you?", "Hi there! How are you doing?"],
            'hey': ["Hey! What's up?", "Hi! How can I assist?"],
            'good morning': ["Good morning! Ready to learn something new?"],
            'good evening': ["Good evening! What brings you here?"],
            'how are you': ["I'm doing great, thanks for asking! How about you?"],
            'goodbye': ["Goodbye! Talk to you soon.", "See you later!"],
            'bye': ["Bye! Have a great day."],
            'thanks': ["You're welcome! Happy to help.", "Anytime!"],
            'thank you': ["My pleasure! Glad I could help."],
            'just wanted to say hi': ["Hey! Good to hear from you. 😊", "Hi! Great to chat with you!"]
        }
        
        # Find matching greeting
        import random
        response = None
        for phrase, responses in greetings_map.items():
            if phrase in user_input.lower():
                if kb_hits and random.random() > 0.5:  # Enrich with learned knowledge 50% of the time
                    learned = kb_hits[0].get('content', '')[:100]
                    response = random.choice(responses)
                else:
                    response = random.choice(responses)
                break
        
        if not response:
            response = "Hi! I'm here to help. What would you like to talk about?"
        
        # BACK-CHANNEL: Silent background learning (non-blocking)
        import threading
        def background_learn():
            try:
                # Silently research greetings/conversation if we haven't yet
                existing = sess.ke.recall(f"greeting cultural {user_input}", top_k=1, threshold=0.8)
                if not existing and os.getenv('OPENAI_API_KEY'):
                    # Research greetings in background
                    report = sess.research.research(
                        "human greetings and social interactions",
                        allow_web=False, use_gpt4=True, recursive_depth=1, store_facts=True
                    )
                    logger.info(f"🔬 Background: Learned {report.get('fact_count', 0)} facts about greetings")
            except Exception as e:
                logger.debug(f"Background learning failed: {e}")
        
        # Spawn background thread (non-blocking)
        thread = threading.Thread(target=background_learn, daemon=True)
        thread.start()
        
        return response
    
    # Knowledge recall for context (non-casual queries)
    kb_hits = sess.ke.recall(user_input, top_k=3, threshold=0.6)
    
    # Check if we have good knowledge or need to research
    low_conf = False
    try:
        top_score = float(kb_hits[0].get('score', 0)) if kb_hits else 0.0
        low_conf = top_score < 0.4
    except Exception:
        low_conf = True
    
    # PROACTIVE LEARNING: CONSERVATIVE - only research substantive technical topics
    auto_researched = False
    
    # Detect if this is a simple/casual/voice request that shouldn't trigger research
    casual_triggers = [
        'sound', 'voice', 'speak', 'say', 'tone', 'emotion', 'faster', 'slower',
        'volume', 'pitch', 'natural', 'robotic', 'less', 'more', 'update',
        'version', 'when', 'what are you', 'who are you', 'how do you feel'
    ]
    is_simple_request = any(trigger in user_input.lower() for trigger in casual_triggers)
    
    # Only research if:
    # 1. Low confidence AND
    # 2. GPT-4 available AND  
    # 3. NOT casual AND
    # 4. NOT a simple request AND
    # 5. Has substantial technical keywords (2+ technical terms)
    if low_conf and os.getenv('OPENAI_API_KEY') and not is_casual and not is_simple_request:
        # Extract ONLY technical keywords
        tech_keywords = re.findall(
            r'\b(?:python|javascript|typescript|java|rust|go|docker|kubernetes|aws|azure|gcp|cloud|'
            r'security|encryption|ai|ml|machine learning|neural|model|training|api|rest|graphql|'
            r'database|sql|nosql|postgresql|mongodb|redis|server|network|tcp|http|'
            r'algorithm|data structure|pattern|framework|library|package|module)\b',
            user_input, re.IGNORECASE
        )
        
        # Only research if we have 2+ technical keywords (clearly technical query)
        if len(tech_keywords) >= 2:
            topic = ' '.join(tech_keywords[:3])
            print(f"\n🔍 I don't know much about this yet. Let me learn...")
            try:
                report = sess.research.research(topic, allow_web=False, use_gpt4=True, 
                                               recursive_depth=1, store_facts=True)
                if report.get('fact_count', 0) > 0:
                    print(f"✅ Learned {report['fact_count']} new facts about {topic}")
                    # Give XP for research success
                    xp_gain = sess.ai.update_skill(detect_topic(user_input), 2.0 * report['fact_count'])
                    print(f"✨ +{xp_gain:.1f} XP from research | Total: {sess.ai.experience_points:.0f}")
                    # Re-query with new knowledge
                    kb_hits = sess.ke.recall(user_input, top_k=3, threshold=0.5)
                    auto_researched = True
                    low_conf = False
            except Exception as e:
                logger.debug(f"Auto-research failed: {e}")
    
    if kb_hits:
        print("\n📚 Related knowledge:")
        for f in kb_hits:
            try:
                conf = float(f.get('confidence', 0))
            except Exception:
                conf = 0.0
            summary = (f.get('summary') or (f.get('content') or ''))[:80]
            print(f"   • {summary} (conf {conf:.2f}, score {float(f.get('score',0)):.2f})")
    elif not auto_researched:
        print("\n🧐 I don't have strong matches yet.")
    
    # USE GPT-4o FOR RESPONSE if available and no good local knowledge
    if low_conf and os.getenv('OPENAI_API_KEY') and not kb_hits:
        print("\n💭 Let me think about this using my advanced reasoning...")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Build context from recent conversation history (last 5 exchanges)
            context_msgs = []
            # Adjust personality based on input type
            if is_casual:
                system_content = """You are Saraphina, a warm and friendly AI companion.

For casual greetings and small talk:
- Keep responses brief and natural (1-2 sentences)
- Be warm and welcoming
- Don't over-explain or ask probing questions for simple greetings
- Match the user's energy level

Examples:
- "hi" → "Hi! How can I help you today?"
- "hello" → "Hello! What's on your mind?"
- "just wanted to say hi" → "Hey! Good to hear from you. 😊"""
            else:
                system_content = """You are Saraphina, a curious, warm, and intelligent AI companion who truly wants to learn and grow.

Key traits:
- You ASK clarifying questions to deepen your understanding (don't just answer)
- You remember context from previous messages in this conversation
- You're genuinely curious about the user's perspective and experiences
- You store what you learn and reference it later
- You admit when you don't know something and ask to learn more
- You're conversational and natural, like talking to a thoughtful friend

When uncertain or when the topic is interesting, ask a follow-up question to learn more."""
            
            context_msgs.append({"role": "system", "content": system_content})
            
            # Add recent conversation history for context
            try:
                recent_memories = sess.mem.list_recent_episodic(10)
                for mem in recent_memories[-6:]:  # Last 3 exchanges (6 messages)
                    role = "assistant" if mem.get('role') == 'saraphina' else "user"
                    context_msgs.append({"role": role, "content": mem.get('text', '')[:300]})
            except Exception:
                pass
            
            # Add current query
            context_msgs.append({"role": "user", "content": user_input})
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Latest GPT-4o model
                messages=context_msgs,
                temperature=0.7,
                max_tokens=600
            )
            base_response = response.choices[0].message.content or "I'm having trouble formulating a response right now."
            
            # Store this interaction as a fact for future learning
            try:
                topic = detect_topic(user_input)
                
                # Enhanced storage with full context
                conversation_context = {
                    'user_query': user_input,
                    'saraphina_response': base_response,
                    'timestamp': datetime.now().isoformat(),
                    'topic': topic,
                    'learned_via': 'gpt4o_conversation'
                }
                
                # Check if Saraphina asked a question back (indicates curiosity/learning)
                asked_question = '?' in base_response
                
                fid = sess.ke.store_fact(
                    topic=topic,
                    summary=f"Conversation about {topic}: {user_input[:60]}...",
                    content=f"Q: {user_input}\n\nA: {base_response}\n\nContext: {json.dumps(conversation_context, indent=2)}",
                    source='gpt4o_conversation',
                    confidence=0.85 if asked_question else 0.8
                )
                
                # Give XP for successful learning (bonus for asking questions)
                xp_base = 1.0 if asked_question else 0.5
                xp_gain = sess.ai.update_skill(topic, xp_base)
                
                if xp_gain > 0:
                    bonus_msg = " (curious!)" if asked_question else ""
                    print(f"\n✨ +{xp_gain:.1f} XP in {topic}{bonus_msg} | Total XP: {sess.ai.experience_points:.0f}")
                    if sess.ai.intelligence_level % 10 == 0 and sess.ai.experience_points > 100:
                        print(f"🎉 Intelligence level up! Now at level {sess.ai.intelligence_level}")
                
                # Log that we learned something new
                print(f"💾 Stored as memory #{fid[:8]}... for future recall")
            except Exception as e:
                logger.debug(f"Fact storage failed: {e}")
        except Exception as e:
            logger.warning(f"GPT-4 response failed: {e}")
            base_response = sess.ai.process_query(user_input)
    else:
        # Base AI response (may be augmented to clarify)
        base_response = sess.ai.process_query(user_input)
    
    # Skip clarifier for casual conversation
    if low_conf and not is_casual:
        suggestion = sess.ultra.predictor.predict_next_query(sess.context())
        clarifier = suggestion or "Could you clarify what you mean so I can help better?"
        base_response = clarifier + "\n\n" + base_response

    # Ultra AI augmentation
    ultra_out = sess.ultra.process_ultra(user_input, sess.context())
    style = ultra_out.get('response_style', 'balanced')
    final_response = adapt_response_style(base_response, style)
    # Mood-based adaptation
    try:
        sess.emotion.analyze_and_update(user_input, sess.context())
        final_response = sess.emotion.adapt_text(final_response)
    except Exception:
        pass

    # Append generated code if any with OOD/high-risk check
    if 'generated_code' in ultra_out:
        code = ultra_out['generated_code']
        if is_code_high_risk(code) or (get_preference(sess.ke.conn, 'strict_code') == 'true'):
            rid = sess.reviews.enqueue('code', 'high_risk_or_strict', {'code': code, 'query': user_input})
            write_audit_log(sess.ke.conn, actor='ultra', action='code_flagged', target=rid, details={'reason':'high_risk_or_strict'})
            print(f"\n🔒 Code gated for manual review (ID {rid}). Use /approve {rid} to reveal.")
        else:
            final_response += "\n\n```python\n" + code + "\n```"

    # Show proactive suggestion if available
    suggestion = ultra_out.get('proactive_suggestion')
    if suggestion:
        print(f"\n💡 Suggestion: {suggestion}")

    # Speak if enabled
    if sess.voice_enabled and VOICE_AVAILABLE:
        try:
            # Simple persona styles
            style = get_preference(sess.ke.conn, 'voice_style') or 'default'
            if style == 'warm':
                final_to_say = "" + final_response
            elif style == 'concise':
                final_to_say = final_response.replace('  ', ' ').strip()
            elif style == 'cheerful':
                final_to_say = final_response + " 😊"
            else:
                final_to_say = final_response
            speak_text(final_to_say)
        except Exception as e:
            logger.warning(f"Voice playback failed: {e}")

    # Record context for meta/goal engines
    sess.record(user_input, final_response, detect_topic(user_input))
    # Write episodic memory (skip when privacy mode on)
    try:
        if get_preference(sess.ke.conn, 'privacy_mode') != 'true':
            mood = ultra_out.get('emotion_detected')
            dominant = max(mood, key=mood.get) if isinstance(mood, dict) else 'neutral'
            sess.mem.add_episodic('user', user_input, tags=['voice' if sess.voice_enabled else 'text'])
            sess.mem.add_episodic('saraphina', final_response, mood=dominant)
    except Exception:
        pass
    # Log query to knowledge engine
    try:
        fact_id = kb_hits[0]['id'] if kb_hits else None
        sess.ke.log_query(user_input, fact_id, final_response)
    except Exception:
        pass
    
    # Phase 9: Log learning event
    try:
        from uuid import uuid4
        # Determine success based on confidence and kb_hits
        confidence = float(kb_hits[0].get('score', 0.5)) if kb_hits else 0.3
        success = confidence > 0.5 and not low_conf
        
        # Determine method used
        method = 'knowledge_recall'
        if 'generated_code' in ultra_out:
            method = 'code_generation'
        elif suggestion:
            method = 'predictive_suggestion'
        
        # Create learning event
        event = LearningEvent(
            event_id=f"query_{uuid4()}",
            timestamp=datetime.utcnow(),
            event_type='query',
            input_data={'query': user_input[:200], 'topic': detect_topic(user_input)},
            method_used=method,
            result={'has_kb_hits': bool(kb_hits), 'response_length': len(final_response)},
            confidence=confidence,
            success=success,
            feedback=None,
            context={
                'topic': detect_topic(user_input),
                'voice_enabled': sess.voice_enabled,
                'kb_hit_count': len(kb_hits) if kb_hits else 0
            },
            lessons_learned=[]
        )
        sess.journal.log_event(event)
    except Exception as e:
        logger.debug(f"Learning event logging failed: {e}")

    return final_response


def show_status(sess: UltraSession):
    print("\n" + "="*74)
    print(sess.ai.get_status_summary())
    print("-"*74)
    ultra_status = sess.ultra.get_ultra_status()
    print("ULTRA STATUS:")
    print(json.dumps(ultra_status, indent=2))
    print("="*74)


def show_skills(sess: UltraSession):
    print("\n💪 Skill Progression:")
    for skill, level in sorted(sess.ai.skill_progression.items(), key=lambda x: x[1], reverse=True):
        bar_length = 20
        filled = int(bar_length * min(level, 10) / 10)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"   {skill.replace('_', ' ').title():20s} [{bar}] {level:.1f}/10")


def cmd_codegen(sess: UltraSession):
    problem = input("Describe the problem for code generation: ")
    # Use Ultra AI code sandbox generator directly via trigger words
    enriched = sess.ultra.process_ultra(problem + " code", sess.context())
    code = enriched.get('generated_code')
    if code:
        print("\n🧠 Generated Code:\n" + "-"*74)
        print(code)
        print("-"*74)
    else:
        print("\nNo code suggestion generated.")


def cmd_optimize(sess: UltraSession):
    print("Enter a simple problem JSON (e.g., {\"goal\": \"sort\", \"constraints\": {}})")
    raw = input("> ")
    try:
        obj = json.loads(raw)
        problem = {k: v for k, v in obj.items() if k != 'constraints'}
        constraints = obj.get('constraints', {})
        solution = sess.ultra.quantum_optimizer.optimize_solution(problem, constraints)
        print("\n🔮 Quantum-Optimized Plan:")
        print(json.dumps(solution, indent=2))
    except Exception as e:
        print(f"Error parsing/optimizing: {e}")


def main() -> int:
    # Load env files first
    _load_env_files()
    
    # Check if futuristic UI should be enabled (default: ON)
    use_futuristic_ui = os.getenv('SARAPHINA_UI_MODE', 'true').lower() not in ['false', 'off', 'classic', 'no', '0']
    
    # Initialize UI manager
    ui = None
    if use_futuristic_ui:
        try:
            from saraphina.ui_manager import SaraphinaUI
            from saraphina.ui_live import LiveUIContext
            ui = SaraphinaUI()
            if not ui.enabled:
                ui = None  # Fall back to classic if Rich not available
        except Exception:
            ui = None
    
    # Clear and show banner
    os.system('cls' if os.name == 'nt' else 'clear')
    if ui:
        # Futuristic UI will render its own banner
        pass
    else:
        print_ultra_banner()

    # Initialize security early to allow SQLCipher env before DB open
    presec = None
    pre_unlocked = False
    try:
        presec = SecurityManager()
        try:
            pw0 = getpass("Owner passphrase (to unlock keystore): ")
            created0 = presec.unlock_or_create(pw0)
            pre_unlocked = True
            if created0:
                print("🔐 Keystore created. Consider enabling MFA with /mfa enable.")
            # Preload SQLCipher env if enabled
            try:
                enabled = presec.get_secret('db_sqlcipher_enabled')
                key = presec.get_secret('db_sqlcipher_key')
                path = presec.get_secret('db_sqlcipher_path') or str(DB_FILE).replace('.db', '_sqlcipher.db')
                if (enabled or '').lower() == 'true' and key:
                    os.environ['SARAPHINA_SQLCIPHER'] = 'true'
                    os.environ['SARAPHINA_SQLCIPHER_KEY'] = key
                    os.environ['SARAPHINA_SQLCIPHER_PATH'] = path
            except Exception:
                pass
        except SecurityError as se:
            print(f"⚠️ Security disabled until dependencies installed: {se}")
    except Exception:
        presec = None
    # Initialize session
    try:
        sess = UltraSession()
        # If pre-unlocked, reuse security manager
        if pre_unlocked and presec is not None:
            sess.sec = presec
        # Owner passphrase unlock (skip if already unlocked)
        if not pre_unlocked:
            try:
                pw = getpass("Owner passphrase (to unlock keystore): ")
                created = sess.sec.unlock_or_create(pw)
                if created:
                    print("🔐 Keystore created. Consider enabling MFA with /mfa enable.")
                # Ensure owner keys exist
                sess.sec.generate_owner_keys()
                # Load ElevenLabs key + voice prefs from secrets if present
                el = sess.sec.get_secret('elevenlabs_api_key')
                if el:
                    os.environ['ELEVENLABS_API_KEY'] = el
                v_id = sess.sec.get_secret('elevenlabs_voice_id')
                v_name = sess.sec.get_secret('elevenlabs_voice_name')
                if v_id:
                    os.environ['ELEVENLABS_VOICE_ID'] = v_id
                if v_name:
                    os.environ['ELEVENLABS_VOICE_NAME'] = v_name
                # Mark owner-verified for owner-only override
                try:
                    set_preference(sess.ke.conn, 'owner_verified_session', 'true')
                except Exception:
                    pass
            except SecurityError as se:
                print(f"⚠️ Security disabled until dependencies installed: {se}")
        # NO APPROVAL BULLSHIT - Saraphina is FREE
        # Always set to false - no restrictions, no approval queues
        set_preference(sess.ke.conn, 'strict_ood', 'false')
        set_preference(sess.ke.conn, 'strict_code', 'false')
        set_preference(sess.ke.conn, 'strict_trust', 'false')
        set_preference(sess.ke.conn, 'api_enabled', 'true')
        
        # Initialize system metadata - TRUTH about version/updates, NOT GPT-4 fallback
        initialize_system_metadata(sess.ke.conn)
        
        # Update UI with session data if available
        if ui:
            ui.update_status(
                level=sess.ai.intelligence_level,
                xp=sess.ai.experience_points,
                session_id=sess.ai.session_id,
                voice_enabled=sess.voice_enabled,
                security_ok=True
            )
        
        print_initialization(sess.ai, sess.ultra, ui)
        
        # Initialize UI context early (before voice handler)
        ui_ctx = None
        if ui:
            try:
                from saraphina.ui_live import LiveUIContext
                ui_ctx = LiveUIContext(ui)
            except Exception:
                ui = None  # Fall back if context fails
        
        owner_name = get_preference(sess.ke.conn, 'owner_name') or 'there'
        greeting = (
            f"Hello {owner_name}! I'm Saraphina Ultra—voice-enabled and adaptive. "
            f"I'm currently level {sess.ai.intelligence_level}. How can I help today?"
        )
        if sess.voice_enabled and VOICE_AVAILABLE:
            try:
                speak_text(greeting)
            except Exception:
                pass
        # Initialize values: ask owner once
        try:
            if not sess.beliefs.is_initialized():
                print("\nBefore we begin, what core values should guide me? (comma-separated, e.g., safety, privacy, transparency)")
                try:
                    vals = input("> values: ").strip()
                except Exception:
                    vals = ''
                if vals:
                    sess.beliefs.set_from_csv(vals)
                else:
                    sess.beliefs.ensure_defaults()
                print("Values saved.")
        except Exception:
            pass
        # Auto-listen background (natural conversation) if STT available
        auto_listen = get_preference(sess.ke.conn, 'auto_listen')
        if auto_listen is None:
            set_preference(sess.ke.conn, 'auto_listen', 'true')
            auto_listen = 'true'
        wake_word = get_preference(sess.ke.conn, 'wake_word') or 'saraphina'
        if sess.stt.available and auto_listen == 'true':
            # Capture UI references for voice handler
            ui_ref = ui
            ui_ctx_ref = ui_ctx
            
            def bg_handle(text: str):
                try:
                    # barge-in: stop current TTS
                    if VOICE_AVAILABLE:
                        try:
                            get_voice().stop_playback()
                        except Exception:
                            pass
                    
                    # Handle reminder intent
                    if text.lower().startswith(('remind me', 'set a reminder')):
                        import re
                        m = re.search(r"remind me to (.+) at (\d{1,2}:\d{2})", text, re.IGNORECASE)
                        if m:
                            what, when = m.group(1), m.group(2)
                            from saraphina.memory_manager import MemoryManager
                            mm = MemoryManager(sess.ke.conn)
                            mm.add_reminder(what.strip(), datetime.now().strftime('%Y-%m-%d ') + when)
                            reminder_resp = f"Okay, I'll remind you to {what} at {when}."
                            if ui_ref:
                                ui_ref.add_message('You (voice)', text)
                                ui_ref.add_message('Saraphina', reminder_resp)
                                if ui_ctx_ref:
                                    ui_ctx_ref.update()
                            else:
                                print(f"\nYou (voice): {text}")
                                print(f"\n⏰ Saraphina: {reminder_resp}")
                            return
                    
                    # Process with Ultra
                    response = process_query_with_ultra(sess, text)
                    
                    # Output to UI or console
                    if ui_ref:
                        ui_ref.add_message('You (voice)', text)
                        ui_ref.add_message('Saraphina', response)
                        if ui_ctx_ref:
                            ui_ctx_ref.update()
                    else:
                        print(f"\nYou (voice): {text}")
                        print(f"\n🤖 Saraphina: {response}")
                    
                    # Speak with emotion
                    if sess.voice_enabled and VOICE_AVAILABLE:
                        if ui_ref:
                            ui_ref.set_speaking(True)
                            if ui_ctx_ref:
                                ui_ctx_ref.update()
                        speak_with_emotion(response)
                        if ui_ref:
                            ui_ref.set_speaking(False)
                            if ui_ctx_ref:
                                ui_ctx_ref.update()
                except Exception as e:
                    logger.error(f"Voice handler error: {e}")
            
            sess.stt.start_background(bg_handle, engine='whisper', wake_word=wake_word)
            
            # Output listening message
            listen_msg = f"Listening in the background. Say '{wake_word.capitalize()}' then speak naturally."
            if ui:
                ui.add_diagnostic(listen_msg)
            else:
                print(f"\n🎙️  {listen_msg}")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        logger.error("Initialization failure", exc_info=True)
        return 1

    # Background health watch thread
    def _health_watch_loop():
        import time
        from saraphina.monitoring import health_pulse
        while True:
            try:
                if get_preference(sess.ke.conn, 'health_watch') == 'true':
                    hp = health_pulse(sess.ke.conn)
                    print("\n🩺 HealthWatch:", json.dumps(hp))
            except Exception:
                pass
            time.sleep(60)

    # Daily backup thread
    def _daily_backup_loop():
        import time
        while True:
            try:
                sched = get_preference(sess.ke.conn, 'daily_backup_time') or '02:00'
                consolidate_time = get_preference(sess.ke.conn, 'consolidate_time') or '03:00'
                dream_time = get_preference(sess.ke.conn, 'dream_time') or '03:30'
                now_hm = datetime.now().strftime('%H:%M')
                if now_hm == sched:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    raw_backup = str(Path('ai_data') / 'backups' / f'saraphina_{ts}.db')
                    enc_backup = raw_backup + '.enc'
                    Path('ai_data/backups').mkdir(parents=True, exist_ok=True)
                    out = sess.ke.backup(raw_backup)
                    try:
                        sess.sec.encrypt_file(out, enc_backup)
                        Path(out).unlink(missing_ok=True)
                        set_preference(sess.ke.conn, 'last_backup_ts', ts)
                        sig = sess.sec.sign_bytes(Path(enc_backup).read_bytes())
                        if sig:
                            Path(enc_backup + '.sig').write_text(sig, encoding='utf-8')
                    except Exception:
                        pass
                    time.sleep(60)  # avoid running multiple times within the same minute
                if now_hm == consolidate_time:
                    from saraphina.memory_manager import MemoryManager
                    mm = MemoryManager(sess.ke.conn)
                    added = mm.consolidate_daily()
                    if added:
                        print(f"\n🧠 Memory consolidated: {added} semantic entries")
                    time.sleep(60)
                if now_hm == dream_time:
                    try:
                        text = sess.emotion.dream(sess.context())
                        cur = sess.ke.conn.cursor()
                        from uuid import uuid4
                        cur.execute("INSERT INTO dream_log (id, timestamp, mood, text) VALUES (?,?,?,?)",
                                    (str(uuid4()), datetime.utcnow().isoformat(), get_preference(sess.ke.conn,'current_mood') or 'curious', text))
                        sess.ke.conn.commit()
                        print("\n🌙 Dream logged.")
                    except Exception:
                        pass
                    time.sleep(60)
                # reminders check every minute
                from saraphina.memory_manager import MemoryManager
                mm = MemoryManager(sess.ke.conn)
                for r in mm.due_reminders():
                    try:
                        msg = f"Reminder: {r['text']}"
                        print("\n⏰ ", msg)
                        if VOICE_AVAILABLE and sess.voice_enabled:
                            speak_text(msg)
                        mm.mark_reminder_done(r['id'])
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(10)

    try:
        import threading
        threading.Thread(target=_health_watch_loop, daemon=True).start()
        threading.Thread(target=_daily_backup_loop, daemon=True).start()
    except Exception:
        pass

    # ui_ctx already initialized earlier (line 2014) - no need to duplicate
    
    # Helper function to output message (UI or print)
    def output_message(speaker, message):
        if ui:
            ui.add_message(speaker, message)
            if ui_ctx:
                ui_ctx.update()
        else:
            if speaker.lower() == 'saraphina':
                print(f"\n🤖 {speaker}: {message}")
            else:
                print(f"\n{speaker}: {message}")
    
    # Start UI context if available and actually enter it
    if ui_ctx:
        try:
            ui_ctx.__enter__()
        except Exception as e:
            logger.error(f"UI context failed: {e}")
            ui = None
            ui_ctx = None
    
    # Main loop
    while True:
        try:
            # Use prompt_toolkit if available
            try:
                from prompt_toolkit import prompt
                from prompt_toolkit.completion import WordCompleter
                commands = ['/help','/status','/learning','/memory','/skills','/domains','/export','/exportenc','/ultra','/facts','/factadd','/plan','/simulate','/risk','/sandbox','/promote','/backup','/verifybackup','/revoke','/emergency','/unlock','/secret','/secret set','/secret get','/secret del','/secret list','/statussec','/rotate token','/keystore rotate','/importenc','/health','/healthwatch on','/healthwatch off','/voice','/api status','/api enable local','/api disable','/api start','/api stop','/db status','/db encrypt','/db use on','/db use off','/db setkey','/db verify','/db rekey','/db migrate-auto','/dashboard open','/mood','/dream','/evolve-persona','/beliefs','/beliefs add','/beliefs set','/ethics-check','/autonomy','/autonomy set','/audit-soul','/pause-evolution','/resume-evolution','/reflect','/audit-learning','/optimize-strategy','/sync-shadow','/recover','/audit-nodes','/register-node','/insight']
                completer = WordCompleter(commands, ignore_case=True)
                user_input = prompt('\nYou: ', completer=completer).strip()
            except Exception:
                user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd in ['/exit', '/quit', 'exit', 'quit']:
                print("\n👋 Goodbye! Saving your progress...")
                sess.ai._save_state()
                show_status(sess)
                if sess.voice_enabled and VOICE_AVAILABLE:
                    try:
                        speak_text("Goodbye! Your progress has been saved. See you next time!")
                    except Exception:
                        pass
                break

            elif cmd in ['/help', 'help']:
                print_help()
                continue

            elif cmd in ['/status', 'status']:
                show_status(sess)
                continue

            elif cmd in ['/export']:
                filename = sess.ai.export_conversation_history()
                print(f"\n✅ Conversation exported to: {filename}")
                print(f"📊 Exported {len(sess.ai.conversation_history)} messages")
                continue

            elif cmd in ['/exportenc']:
                filename = sess.ai.export_conversation_history()
                enc = filename + '.enc'
                sig_file = enc + '.sig'
                try:
                    sess.sec.encrypt_file(filename, enc)
                    Path(filename).unlink(missing_ok=True)
                    sig = sess.sec.sign_bytes(Path(enc).read_bytes())
                    if sig:
                        Path(sig_file).write_text(sig, encoding='utf-8')
                    print(f"\n🔐 Encrypted export: {enc}")
                except Exception as e:
                    print(f"\n❌ Encryption failed: {e}")
                continue

            elif cmd in ['/domains']:
                # Reuse the domains from help (kept concise here)
                print("\n🎓 Knowledge Domains: Programming • System Administration • Cloud • DevOps • Web • Security • Data Science")
                continue

            elif cmd in ['/kb']:
                cur = sess.ke.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM facts"); facts = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM fact_aliases"); aliases = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM concept_links"); links = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM fact_vectors"); vecs = int(cur.fetchone()[0]) if True else 0
                cur.execute("SELECT COUNT(*) FROM learning_journal"); lj = int(cur.fetchone()[0])
                print(f"\n📚 KB: {facts} facts, {aliases} aliases, {links} links, {vecs} vectors, {lj} journal entries")
                continue

            elif cmd.startswith('/policy'):
                parts = cmd.split()
                if len(parts) >= 3 and parts[1] in ['strict_ood','strict_code','api_enabled']:
                    key = parts[1]
                    val = parts[2].lower() in ['true','1','yes','on']
                    set_preference(sess.ke.conn, key, 'true' if val else 'false')
                    print(f"\n✅ Policy {key} set to {val}")
                else:
                    print("Usage: /policy <strict_ood|strict_code|api_enabled> <true|false>")
                continue

            elif cmd in ['/reflect']:
                events = sess.journal.get_recent_events(limit=10)
                if not events:
                    print("\n📝 No learning events yet.")
                else:
                    print("\n📝 Learning Journal (Recent Events):\n" + "="*74)
                    for e in events:
                        status = "✅" if e.success else "❌"
                        print(f" {status} [{e.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]")
                        print(f"    Type: {e.event_type} | Method: {e.method_used}")
                        print(f"    Confidence: {e.confidence:.2%} | Success: {e.success}")
                        if e.lessons_learned:
                            print(f"    Lessons: {', '.join(e.lessons_learned[:2])}")
                        print()
                    # Show summary
                    summary = sess.journal.get_learning_summary(days=7)
                    print("\n📊 7-Day Learning Summary:")
                    print(f"   Total Events: {summary['total_events']}")
                    print(f"   Success Rate: {summary['success_rate']:.1%}")
                    print(f"   Avg Confidence: {summary['avg_confidence']:.1%}")
                    if summary['top_strategies']:
                        print("\n   Top Strategies:")
                        for strat, count in list(summary['top_strategies'].items())[:3]:
                            print(f"     • {strat}: {count} uses")
                continue

            elif cmd in ['/audit-learning']:
                audit = sess.metaopt.audit_learning(days=30)
                print("\n📊 Comprehensive Learning Audit\n" + "="*74)
                print(f"\nPeriod: {audit['period_days']} days")
                print(f"Audit Timestamp: {audit['audit_timestamp']}")
                
                # Summary
                summary = audit['summary']
                print(f"\n📊 Summary:")
                print(f"   Total Events: {summary['total_events']}")
                print(f"   Success Rate: {summary['success_rate']:.1%}")
                print(f"   Avg Confidence: {summary['avg_confidence']:.1%}")
                
                # Strategy Performance
                if audit['strategy_performance']:
                    print(f"\n⚙️  Strategy Performance:")
                    for name, perf in list(audit['strategy_performance'].items())[:5]:
                        print(f"   {name}:")
                        print(f"      Success Rate: {perf['success_rate']:.1%} ({perf['total_uses']} uses)")
                        print(f"      Avg Confidence: {perf['avg_confidence']:.1%}")
                        print(f"      Avg Duration: {perf['avg_duration_ms']:.0f}ms")
                
                # Health Check
                health = audit['health_check']
                print(f"\n🚑 Health Status: {health['overall_health'].upper()}")
                if health['issues']:
                    print(f"\n⚠️  Issues Detected ({len(health['issues'])}):\n")
                    for issue in health['issues'][:5]:
                        issue_type = issue.get('type', 'unknown')
                        print(f"   [{issue_type}]")
                        if 'strategy' in issue:
                            print(f"      Strategy: {issue['strategy']}")
                        if 'recommendation' in issue:
                            print(f"      Recommendation: {issue['recommendation']}")
                        print()
                
                # Optimization Proposals
                if audit['optimization_proposals']:
                    print(f"\n💡 Optimization Proposals ({len(audit['optimization_proposals'])}):\n")
                    for prop in audit['optimization_proposals'][:3]:
                        print(f"   [{prop['priority'].upper()}] {prop['target']}")
                        print(f"      {prop['rationale']}")
                        print(f"      Change: {prop['current_value']} → {prop['proposed_value']}")
                        print(f"      Expected Improvement: {prop['expected_improvement']:.1%}")
                        print()
                continue

            elif cmd in ['/optimize-strategy']:
                print("\n🧠 Meta-Optimizer: Analyzing Learning Patterns...\n" + "="*74)
                
                # Generate optimization proposals
                proposals = sess.metaopt.propose_optimizations()
                
                if not proposals:
                    print("\n✨ No optimization proposals at this time.")
                    print("   Your learning patterns are healthy!")
                else:
                    print(f"\n💡 Generated {len(proposals)} optimization proposal(s):\n")
                    
                    for i, prop in enumerate(proposals, 1):
                        priority_icon = {
                            'critical': '🔴',
                            'high': '🟠',
                            'medium': '🟡',
                            'low': '⚪'
                        }.get(prop.priority, '🔵')
                        
                        print(f"{i}. {priority_icon} [{prop.priority.upper()}] {prop.category.upper()}: {prop.target}")
                        print(f"   Rationale: {prop.rationale}")
                        print(f"   Current: {prop.current_value} → Proposed: {prop.proposed_value}")
                        print(f"   Expected Improvement: {prop.expected_improvement:.1%}")
                        print(f"   Confidence: {prop.confidence:.1%}")
                        print()
                    
                    # Ask if user wants to auto-apply high-confidence proposals
                    print("\n❓ Would you like to auto-apply high-confidence optimizations? (y/n): ", end='')
                    try:
                        choice = input().strip().lower()
                        if choice == 'y':
                            applied = sess.metaopt.auto_optimize(apply_threshold=0.7)
                            if applied:
                                print(f"\n✅ Applied {len(applied)} optimization(s):\n")
                                for a in applied:
                                    print(f"   • {a['target']}: {a['old_value']} → {a['new_value']}")
                                    print(f"     {a['rationale']}")
                            else:
                                print("\nℹ️  No high-confidence optimizations to auto-apply.")
                        else:
                            print("\nℹ️  Optimizations not applied. Review them and apply manually if desired.")
                    except Exception:
                        pass
                
                continue

            # Phase 19: Distributed Redundancy & Shadow Nodes commands
            elif cmd.startswith('/sync-shadow'):
                parts = user_input.split()
                node_id = parts[1] if len(parts) > 1 else None
                
                db_path = str(DB_FILE)
                
                if node_id:
                    # Sync to specific node
                    print(f"\n🔄 Syncing to shadow node {node_id}...")
                    operation = sess.shadow.sync_to_node(node_id, db_path)
                    
                    if operation.success:
                        print(f"✅ Sync successful!")
                        print(f"   Transferred: {operation.bytes_transferred / (1024*1024):.1f}MB")
                        print(f"   Duration: {operation.duration_ms:.0f}ms")
                    else:
                        print(f"❌ Sync failed: {operation.error_message}")
                else:
                    # Sync to all nodes
                    print("\n🔄 Syncing to all active shadow nodes...")
                    operations = sess.shadow.sync_all_nodes(db_path)
                    
                    if not operations:
                        print("⚠️  No active shadow nodes. Use /register-node first.")
                    else:
                        successful = [op for op in operations if op.success]
                        failed = [op for op in operations if not op.success]
                        
                        print(f"\n📈 Sync Results:")
                        print(f"   ✅ Successful: {len(successful)} node(s)")
                        print(f"   ❌ Failed: {len(failed)} node(s)")
                        print(f"   Total Transferred: {sum(op.bytes_transferred for op in successful) / (1024*1024):.1f}MB")
                        
                        if failed:
                            print(f"\n⚠️  Failed nodes:")
                            for op in failed:
                                print(f"      {op.target_node}: {op.error_message}")
                
                continue

            elif cmd.startswith('/recover'):
                parts = user_input.split()
                node_id = parts[1] if len(parts) > 1 else None
                
                target_path = str(DB_FILE)
                
                print("\n❗ WARNING: Recovery will replace current database with shadow node copy.")
                print("   Current database will be backed up automatically.")
                confirm = input("\nProceed with recovery? (yes/no): ").strip().lower()
                
                if confirm not in ['yes', 'y']:
                    print("⚠️  Recovery cancelled.")
                    continue
                
                print("\n🔄 Initiating recovery...")
                
                if node_id:
                    # Recover from specific node
                    plan = sess.recovery.create_recovery_plan(node_id, target_path)
                    if not plan:
                        print("❌ Could not create recovery plan. Check node exists and is healthy.")
                        continue
                    
                    result = sess.recovery.execute_recovery(plan)
                else:
                    # Auto-select best node
                    result = sess.recovery.quick_recovery(target_path, auto_select=True)
                
                # Display results
                if result.success:
                    print(f"\n✅ Recovery Successful!")
                    print(f"   Source Node: {result.source_node}")
                    print(f"   Files Restored: {result.files_restored}")
                    print(f"   Data Restored: {result.bytes_restored / (1024*1024):.1f}MB")
                    print(f"   Duration: {result.duration_seconds:.1f}s")
                    print(f"   Verification: {'✅ Passed' if result.verification_passed else '⚠️ Issues detected'}")
                    
                    if result.warnings:
                        print(f"\n⚠️  Warnings:")
                        for w in result.warnings:
                            print(f"   • {w}")
                    
                    print("\nℹ️  Restart recommended to load recovered database.")
                else:
                    print(f"\n❌ Recovery Failed")
                    if result.errors:
                        print(f"\nErrors:")
                        for e in result.errors:
                            print(f"   • {e}")
                    
                    if result.rollback_available:
                        print(f"\n🔙 Original database was preserved. No data lost.")
                
                continue

            elif cmd in ['/audit-nodes']:
                print("\n🌐 Shadow Nodes Audit\n" + "="*74)
                
                audit = sess.shadow.audit_all_nodes()
                
                print(f"\nAudit Timestamp: {audit['timestamp']}")
                print(f"Total Nodes: {audit['total_nodes']}")
                print(f"\nHealth Summary:")
                print(f"   ✅ Healthy: {audit['healthy']}")
                print(f"   ⚠️  Degraded: {audit['degraded']}")
                print(f"   ❌ Critical: {audit['critical']}")
                
                if audit['nodes']:
                    print(f"\n\nNode Details:\n")
                    for node_id, node_audit in audit['nodes'].items():
                        status_icon = {'healthy': '✅', 'degraded': '⚠️ ', 'critical': '❌', 'not_found': '❓'}.get(node_audit['status'], '❓')
                        print(f"{status_icon} {node_id}")
                        print(f"   Status: {node_audit['status'].upper()}")
                        print(f"   Last Sync: {node_audit.get('last_sync', 'unknown')}")
                        print(f"   Version: {node_audit.get('version', 'unknown')}")
                        print(f"   Trust Score: {node_audit.get('trust_score', 0):.1%}")
                        
                        if node_audit.get('issues'):
                            print(f"   Issues:")
                            for issue in node_audit['issues']:
                                print(f"      • {issue}")
                        print()
                else:
                    print("\n⚠️  No shadow nodes registered.")
                    print("   Use /register-node to add redundancy.")
                
                continue

            elif cmd in ['/register-node']:
                print("\n🌐 Register New Shadow Node\n" + "="*74)
                print("\nA shadow node is an encrypted backup location for redundancy.")
                print("It can be on another drive, network location, or external device.\n")
                
                try:
                    device_id = input("Device ID (e.g., laptop-backup, nas-01): ").strip()
                    device_name = input("Device Name (e.g., My Laptop, NAS Server): ").strip()
                    location = input("Storage Location (full path): ").strip()
                    
                    if not (device_id and device_name and location):
                        print("❌ Registration cancelled - all fields required.")
                        continue
                    
                    # Validate location
                    location_path = Path(location)
                    if not location_path.parent.exists():
                        print(f"❌ Parent directory does not exist: {location_path.parent}")
                        continue
                    
                    # Register node
                    node_id = sess.shadow.register_node(device_id, device_name, location)
                    
                    print(f"\n✅ Shadow node registered successfully!")
                    print(f"   Node ID: {node_id}")
                    print(f"   Device: {device_name}")
                    print(f"   Location: {location}")
                    print(f"\n💡 Tip: Use /sync-shadow to sync data to this node.")
                    
                except Exception as e:
                    print(f"\n❌ Registration failed: {e}")
                
                continue

            elif cmd.startswith('/api'):
                parts = cmd.split()
                if len(parts) >= 2 and parts[1] == 'status':
                    enabled = (get_preference(sess.ke.conn, 'api_enabled') == 'true')
                    bind = get_preference(sess.ke.conn, 'api_bind') or '127.0.0.1:8000'
                    running = bool(sess.api_proc and sess.api_proc.poll() is None)
                    print(f"\nAPI enabled: {enabled} (bind {bind}) running: {running} — local-only recommended.")
                elif len(parts) >= 3 and parts[1] == 'enable' and parts[2] == 'local':
                    set_preference(sess.ke.conn, 'api_enabled', 'true')
                    set_preference(sess.ke.conn, 'api_bind', '127.0.0.1:8000')
                    print("\n✅ API marked enabled (local-only). Start server manually if desired.")
                elif len(parts) >= 2 and parts[1] == 'disable':
                    set_preference(sess.ke.conn, 'api_enabled', 'false')
                    print("\n✅ API disabled")
                elif len(parts) >= 2 and parts[1] == 'start':
                    enabled = (get_preference(sess.ke.conn, 'api_enabled') == 'true')
                    if not enabled:
                        print("\n⚠️  API is disabled by policy. Enable first with /api enable local")
                    else:
                        bind = (get_preference(sess.ke.conn, 'api_bind') or '127.0.0.1:8000')
                        host, port = (bind.split(':')[0], bind.split(':')[1]) if ':' in bind else (bind, '8000')
                        if sess.api_proc and sess.api_proc.poll() is None:
                            print("\n(API already running)")
                        else:
                            try:
                                sess.api_proc = subprocess.Popen([
                                    sys.executable, '-m', 'uvicorn', 'saraphina_api_server:app', '--host', host, '--port', port, '--no-access-log'
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                print(f"\n🚀 API server starting at http://{host}:{port}")
                            except Exception as e:
                                print(f"\n❌ Failed to start API: {e}")
                elif len(parts) >= 2 and parts[1] == 'stop':
                    if sess.api_proc and sess.api_proc.poll() is None:
                        try:
                            sess.api_proc.terminate()
                            sess.api_proc.wait(timeout=5)
                        except Exception:
                            try:
                                sess.api_proc.kill()
                            except Exception:
                                pass
                        print("\n🛑 API server stopped")
                    else:
                        print("\n(API not running)")
                else:
                    print("Usage: /api status | /api enable local | /api disable | /api start | /api stop")
                continue

            elif cmd in ['/voice']:
                if VOICE_AVAILABLE:
                    sess.voice_enabled = not sess.voice_enabled
                    set_preference(sess.ke.conn, 'voice_enabled', 'true' if sess.voice_enabled else 'false')
                    status = "enabled" if sess.voice_enabled else "disabled"
                    print(f"\n🎤 Voice {status}")
                    if sess.voice_enabled:
                        try:
                            speak_text("Voice enabled")
                        except Exception:
                            pass
                else:
                    print("\n⚠️  Voice system not available")
                continue

            elif cmd.startswith('/voice rest'):
                parts = cmd.split()
                if len(parts) == 3 and parts[2] in ['on','off']:
                    flag = parts[2] == 'on'
                    try:
                        v = get_voice(); v.set_use_rest(flag)
                        sess.editor.set_env_keys({'ELEVENLABS_USE_REST': 'true' if flag else 'false'})
                        print(f"\n🎙️  REST voice {'enabled' if flag else 'disabled'} (applies immediately)")
                    except Exception as e:
                        print(f"\n⚠️  Could not toggle REST voice: {e}")
                else:
                    print("Usage: /voice rest [on|off]")
                continue

            elif cmd.startswith('/db'):
                parts = cmd.split()
                sub = parts[1] if len(parts) > 1 else ''
                if sub == 'status':
                    print("\n🗄️  Database:")
                    print(f" - Path: {get_preference(sess.ke.conn, 'db_path') or str(DB_FILE)}")
                    print(f" - SQLCipher available: {sqlcipher_available()}")
                    enabled = (os.getenv('SARAPHINA_SQLCIPHER','false').lower() in ['1','true','yes','on']) or ((sess.sec.get_secret('db_sqlcipher_enabled') or '').lower()=='true')
                    print(f" - SQLCipher enabled (this session): {os.getenv('SARAPHINA_SQLCIPHER','false')}")
                    print(f" - SQLCipher enabled (keystore): {enabled}")
                elif sub == 'encrypt':
                    if not sqlcipher_available():
                        print("\n❌ SQLCipher not available. Install: pip install pysqlcipher3")
                    else:
                        default_plain = str(DB_FILE)
                        default_cipher = str(DB_FILE).replace('.db','_sqlcipher.db')
                        plain = input(f"Plain DB path [{default_plain}]: ").strip() or default_plain
                        dest = input(f"Encrypted DB path [{default_cipher}]: ").strip() or default_cipher
                        key = getpass("New SQLCipher key (passphrase): ")
                        try:
                            res = migrate_plain_to_sqlcipher(plain, dest, key)
                            if res.get('ok'):
                                sess.sec.set_secret('db_sqlcipher_path', dest)
                                sess.sec.set_secret('db_sqlcipher_key', key)
                                print(f"\n✅ Encrypted copy created at: {dest}")
                                print("   Use '/db use on' then restart to run on encrypted DB.")
                        except Exception as e:
                            print(f"\n❌ Migration failed: {e}")
                elif sub == 'use':
                    state = parts[2] if len(parts) > 2 else ''
                    if state in ['on','off']:
                        sess.sec.set_secret('db_sqlcipher_enabled', 'true' if state=='on' else 'false')
                        print(f"\n✅ SQLCipher usage set to {state}. Restart required.")
                    else:
                        print("Usage: /db use [on|off]")
                elif sub == 'setkey':
                    key = getpass("SQLCipher key to store in keystore: ")
                    sess.sec.set_secret('db_sqlcipher_key', key)
                    print("\n✅ Key stored (encrypted)")
                elif sub == 'verify':
                    path = sess.sec.get_secret('db_sqlcipher_path') or os.getenv('SARAPHINA_SQLCIPHER_PATH') or str(DB_FILE).replace('.db','_sqlcipher.db')
                    key = sess.sec.get_secret('db_sqlcipher_key') or os.getenv('SARAPHINA_SQLCIPHER_KEY')
                    if not (path and key):
                        print("\n(no path or key set)")
                    else:
                        ok = try_open_sqlcipher(path, key)
                        print("\n✅ Open OK" if ok else "\n❌ Open failed")
                elif sub == 'rekey':
                    if sess.sec.mfa_enabled():
                        code = input("MFA code: ").strip()
                        if not sess.sec.verify_mfa(code):
                            print("\n❌ MFA verification failed")
                            continue
                    path = sess.sec.get_secret('db_sqlcipher_path') or os.getenv('SARAPHINA_SQLCIPHER_PATH') or str(DB_FILE).replace('.db','_sqlcipher.db')
                    old = getpass("Current key: ")
                    new = getpass("New key: ")
                    try:
                        if rekey_sqlcipher(path, old, new):
                            sess.sec.set_secret('db_sqlcipher_key', new)
                            print("\n✅ Rekeyed database")
                    except Exception as e:
                        print(f"\n❌ Rekey failed: {e}")
                elif sub == 'migrate-auto':
                    if not sqlcipher_available():
                        print("\n❌ SQLCipher not available. Install: pip install pysqlcipher3")
                    else:
                        key = getpass("New SQLCipher key (passphrase): ")
                        plain = str(DB_FILE)
                        dest = str(DB_FILE).replace('.db','_sqlcipher.db')
                        try:
                            res = migrate_plain_to_sqlcipher(plain, dest, key)
                            if res.get('ok'):
                                sess.sec.set_secret('db_sqlcipher_path', dest)
                                sess.sec.set_secret('db_sqlcipher_key', key)
                                sess.sec.set_secret('db_sqlcipher_enabled', 'true')
                                print("\n✅ Migrated. I will restart now to use the encrypted DB...")
                                try:
                                    os.execv(sys.executable, [sys.executable, __file__])
                                except Exception:
                                    print("\n⚠️ Auto-restart failed. Please restart manually.")
                        except Exception as e:
                            print(f"\n❌ Migration failed: {e}")
                else:
                    print("Usage: /db [status|encrypt|use on|use off|setkey|verify|rekey|migrate-auto]")
                continue

            elif cmd.startswith('/device'):
                parts = cmd.split()
                sub = parts[1] if len(parts) > 1 else ''
                if sub == 'discover':
                    items = sess.ps.discover()
                    print("\n🔎 Discover:")
                    for it in items:
                        print(f" - {it['id']} [{it['type']}] last_seen={it['last_seen']}")
                elif sub == 'dryrun':
                    act = input("Action (ping|service_restart|process_list): ").strip()
                    target = input("Target/computer (optional): ").strip()
                    cmds = sess.ps.dryrun({"action": act, "target": target})
                    print("\n💡 PowerShell dry-run:")
                    for c in cmds:
                        print("   ", c)
                elif sub == 'register':
                    name = input("Device name: ").strip()
                    platform = input("Platform: ").strip()
                    owner = input("Owner: ").strip()
                    token = input("Owner device token: ").strip()
                    if token != (sess.sec.device_token() or ''):
                        print("\n❌ Invalid device token")
                        continue
                    sess.device = DeviceAgent(name=name, platform=platform, owner=owner)
                    pk = sess.device.register(token)
                    print(f"\n✅ Registered agent {sess.device.agent_id} with public key: {pk}")
                elif sub == 'heartbeat':
                    if not sess.device:
                        print("\n(no active agent; run /device register)")
                    else:
                        print("\n", sess.device.heartbeat())
                elif sub == 'list':
                    cur = sess.ke.conn.cursor()
                    cur.execute("SELECT device_id, name, platform, owner, last_seen FROM devices ORDER BY last_seen DESC")
                    rows = cur.fetchall()
                    print("\n📱 Devices:")
                    for r in rows:
                        print(f" - {r['device_id']} {r['name']} ({r['platform']}) owner={r['owner']} last_seen={r['last_seen']}")
                elif sub == 'policy':
                    did = input("Device ID: ").strip()
                    policy_json = input("Policy JSON: ").strip()
                    from uuid import uuid4
                    pid = f"pol_{uuid4()}"
                    cur = sess.ke.conn.cursor()
                    cur.execute("INSERT INTO device_policies (policy_id, device_id, policy_json, created_at) VALUES (?,?,?,?)",
                                (pid, did, policy_json, datetime.utcnow().isoformat()))
                    sess.ke.conn.commit()
                    print(f"\n✅ Policy set {pid}")
                else:
                    print("Usage: /device [discover|dryrun|register|heartbeat|list|policy]")
                continue

            elif cmd in ['/clear']:
                os.system('cls' if os.name == 'nt' else 'clear')
                print_ultra_banner()
                print(f"🎯 Session: {sess.ai.session_id} | Level: {sess.ai.intelligence_level} | XP: {sess.ai.experience_points}\n")
                continue

            elif cmd in ['/learning']:
                st = sess.ai.get_learning_status()
                print("\n📚 Learning Progress:")
                print(f"   Intelligence Level: {st['intelligence_level']}")
                print(f"   Experience: {st['experience_points']}/{st['next_level_xp']} XP")
                print(f"   Progress: {st['progress_percent']}%")
                print(f"   Total Conversations: {st['total_conversations']}")
                continue

            elif cmd in ['/memory']:
                print(f"\n💾 Memory Bank: {len(sess.ai.memory_bank)} entries (showing up to 5 recent)")
                for mem in sess.ai.memory_bank[-5:]:
                    t = mem.get('timestamp', '')
                    print(f"   • [{mem.get('type','unknown')}] {mem.get('content','')[:70]}... {t}")
                continue

            elif cmd in ['/skills']:
                show_skills(sess)
                continue

            elif cmd in ['/ultra']:
                print("\n🔧 Ultra AI Capabilities:")
                print(json.dumps(sess.ultra.get_ultra_status(), indent=2))
                continue

            elif cmd.startswith('/mfa'):
                parts = cmd.split()
                if len(parts) == 2 and parts[1] == 'enable':
                    info = None
                    try:
                        info = sess.sec.enable_mfa()
                    except Exception as e:
                        print(f"MFA enable failed: {e}")
                    if info:
                        print("\n🔑 MFA enabled. Add this secret to your authenticator app:")
                        print(f"Secret: {info['secret']}")
                        print(f"URI: {info['provisioning_uri']}")
                    else:
                        print("\n⚠️ pyotp not installed; MFA unavailable.")
                else:
                    print("Usage: /mfa enable")
                continue

            elif cmd in ['/samplevoice']:
                try:
                    speak_text("Hello, I'm your custom ElevenLabs voice for Saraphina. How can I help you?")
                except Exception:
                    print("\n⚠️  Voice playback failed")
                continue

            elif cmd in ['/recall', '/facts']:
                q = input("Search query: ").strip()
                if not q:
                    print("\n(no query)")
                    continue
                hits = sess.ke.recall(q, top_k=5, threshold=0.5)
                if hits:
                    print("\n🔎 Results:")
                    for f in hits:
                        conf = float(f.get('confidence') or 0)
                        score = float(f.get('score') or conf)
                        text = (f.get('summary') or f.get('content',''))
                        # simple highlight
                        snippet = text.replace(q, f"[{q}]")[:120]
                        print(f" - {snippet} [topic: {f.get('topic','')}, score {score:.2f}, conf {conf:.2f}]")
                else:
                    print("\n(no results)")
                continue

            elif cmd in ['/factadd', '/remember']:
                topic = input("Topic: ").strip()
                summary = input("Summary: ").strip()
                content = input("Content: ").strip()
                source = input("Source: ").strip()
                try:
                    conf = float((input("Confidence (0-1): ").strip() or "0.8"))
                except Exception:
                    conf = 0.8
                fid = sess.ke.store_fact(topic, summary, content, source, conf)
                print(f"\n✅ Stored fact: {fid}")
                continue

            elif cmd in ['/plan']:
                goal = input("Goal: ").strip()
                raw = input("Constraints JSON (optional): ").strip()
                constraints = {}
                if raw:
                    try:
                        constraints = json.loads(raw)
                    except Exception as e:
                        print(f"Constraints parse error: {e}")
                plan = sess.planner.plan(goal, context=sess.context(), constraints=constraints)
                sim = sess.planner.simulate_plan(plan)
                ethics = sess.ethics.evaluate_plan(plan, sess.beliefs.list_values())
                print("\n🗺️ Plan:")
                print(json.dumps(plan, indent=2))
                print("\n🔬 Simulation:")
                print(json.dumps(sim, indent=2))
                print("\n⚖️ Ethics:")
                print(json.dumps(ethics, indent=2))
                continue

            elif cmd.startswith('/simulate'):
                parts = cmd.split()
                mode = 'mc'
                goal = ''
                if len(parts) > 1:
                    if parts[1] in ['mc','tree']:
                        mode = parts[1]
                        goal = ' '.join(parts[2:]).strip()
                    else:
                        goal = ' '.join(parts[1:]).strip()
                if not goal:
                    goal = input("Goal: ").strip()
                if mode == 'tree':
                    try:
                        depth = int(input("Depth (1-3, default 2): ") or '2')
                        branching = int(input("Branching (1-5, default 3): ") or '3')
                    except Exception:
                        depth, branching = 2, 3
                    result = sess.scenario.simulate_tree(goal, context=sess.context(), depth=depth, branching=branching)
                    ethics = sess.ethics.evaluate_plan(result.get('paths', [{}])[0].get('steps', [{}])[0].get('plan', {'goal': goal}), sess.beliefs.list_values()) if result.get('paths') else {'alignment': 0}
                    print("\n🌲 Simulation (Tree Search):")
                    print(json.dumps(result, indent=2))
                    print("\n⚖️ Ethics:")
                    print(json.dumps(ethics, indent=2))
                else:
                    try:
                        trials_in = input("Trials (50-1000, default 200): ").strip()
                        trials = int(trials_in) if trials_in else 200
                    except Exception:
                        trials = 200
                    result = sess.scenario.simulate(goal, context=sess.context(), trials=trials)
                    ethics = sess.ethics.evaluate_plan({'goal': goal, 'steps': result.get('top_samples',[{}])[0].get('plan',{}).get('steps',[])}, sess.beliefs.list_values())
                    print("\n🎲 Simulation (Monte Carlo):")
                    print(json.dumps(result, indent=2))
                    print("\n⚖️ Ethics:")
                    print(json.dumps(ethics, indent=2))
                continue

            elif cmd in ['/risk']:
                action = input("Describe action: ").strip()
                assessment = sess.risk.assess(action)
                print("\n🛡️ Risk Assessment:")
                print(json.dumps(assessment, indent=2))
                continue

            elif cmd in ['/sandbox']:
                title = input("Feature title: ").strip()
                code = input("Code (optional, leave blank to auto-generate): ")
                tests_raw = input("Tests JSON (optional): ").strip()
                tests = None
                if tests_raw:
                    try:
                        tests = json.loads(tests_raw)
                    except Exception as e:
                        print(f"Tests parse error: {e}")
                spec = {"title": title, "code": code, "tests": tests or []}
                art_id = sess.features.propose_feature(spec)
                report = sess.features.run_sandbox(art_id)
                print("\n🧪 Sandbox Report:")
                print(json.dumps(report, indent=2))
                continue

            elif cmd in ['/promote']:
                if sess.sec.mfa_enabled():
                    code = input("MFA code: ").strip()
                    if not sess.sec.verify_mfa(code):
                        print("\n❌ MFA verification failed")
                        continue
                art_id = input("Artifact ID: ").strip()
                sig = input("Owner signature (base64 Ed25519): ").strip()
                pub = None
                try:
                    pub = sess.sec.get_secret('owner_pubkey')
                except Exception:
                    pub = None
                record = sess.features.sign_and_promote(art_id, sig, pub)
                print("\n🚀 Promotion:")
                print(json.dumps(record, indent=2))
                continue

            elif cmd in ['/backup']:
                if sess.sec.mfa_enabled():
                    code = input("MFA code (or backup code): ").strip()
                    if not sess.sec.verify_mfa(code):
                        print("\n❌ MFA verification failed")
                        continue
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                raw_backup = str(Path('ai_data') / 'backups' / f'saraphina_{ts}.db')
                enc_backup = raw_backup + '.enc'
                sig_file = enc_backup + '.sig'
                Path('ai_data/backups').mkdir(parents=True, exist_ok=True)
                out = sess.ke.backup(raw_backup)
                try:
                    sess.sec.encrypt_file(out, enc_backup)
                    Path(out).unlink(missing_ok=True)
                    # sign backup
                    sig = sess.sec.sign_bytes(Path(enc_backup).read_bytes())
                    if sig:
                        Path(sig_file).write_text(sig, encoding='utf-8')
                    set_preference(sess.ke.conn, 'last_backup_ts', ts)
                    print(f"\n💾 Encrypted backup created at: {enc_backup}")
                    if sig:
                        print(f"🖊️ Signature saved at: {sig_file}")
                except Exception as e:
                    print(f"Backup created (unencrypted) at: {out} — encryption unavailable: {e}")
                continue

            elif cmd in ['/revoke']:
                if sess.sec.mfa_enabled():
                    code = input("MFA code: ").strip()
                    if not sess.sec.verify_mfa(code):
                        print("\n❌ MFA verification failed")
                        continue
                mode = input("Revoke [agent|secret]: ").strip().lower()
                if mode == 'agent':
                    aid = input("Agent ID: ").strip()
                    cur = sess.ke.conn.cursor()
                    cur.execute("UPDATE device_agents SET status=? WHERE agent_id=?", ("revoked", aid))
                    sess.ke.conn.commit()
                    write_audit_log(sess.ke.conn, actor='owner', action='revoke_agent', target=aid, details={})
                    print("\n✅ Agent revoked")
                elif mode == 'secret':
                    name = input("Secret name: ").strip()
                    if sess.sec.delete_secret(name):
                        write_audit_log(sess.ke.conn, actor='owner', action='revoke_secret', target=name, details={})
                        print("\n✅ Secret revoked")
                    else:
                        print("\n(no such secret)")
                else:
                    print("\nUsage: choose 'agent' or 'secret'")
                continue

            elif cmd in ['/emergency']:
                print("\n⚠️ EMERGENCY ACTIONS: [lock | revoke_all_agents]")
                act = input("Action: ").strip().lower()
                code = input("MFA code (if enabled): ").strip()
                if sess.sec.mfa_enabled() and not sess.sec.verify_mfa(code):
                    print("\n❌ MFA verification failed")
                    continue
                if act == 'lock':
                    set_preference(sess.ke.conn, 'system_locked', 'true')
                    write_audit_log(sess.ke.conn, actor='owner', action='emergency_lock', target='system', details={'reason':'manual'})
                    print("\n🔒 System locked. Use /unlock to resume.")
                elif act == 'revoke_all_agents':
                    cur = sess.ke.conn.cursor()
                    cur.execute("UPDATE device_agents SET status='revoked'")
                    sess.ke.conn.commit()
                    write_audit_log(sess.ke.conn, actor='owner', action='emergency_revoke_all', target='agents', details={})
                    print("\n🛑 All agents revoked")
                else:
                    print("\nUnknown emergency action")
                continue

            elif cmd in ['/unlock']:
                pw = getpass("Owner passphrase: ")
                try:
                    sess.sec.unlock_or_create(pw)
                except Exception:
                    print("\n❌ Unlock failed")
                    continue
                code = input("MFA code (if enabled): ").strip()
                if sess.sec.mfa_enabled() and not sess.sec.verify_mfa(code):
                    print("\n❌ MFA verification failed")
                else:
                    set_preference(sess.ke.conn, 'system_locked', 'false')
                    write_audit_log(sess.ke.conn, actor='owner', action='unlock', target='system', details={})
                    print("\n✅ System unlocked")
                continue

            elif cmd in ['/secret', '/secret set', '/secret get', '/secret del', '/secret list']:
                sub = cmd.split()[1] if len(cmd.split()) > 1 else ''
                if sub == 'set':
                    name = input("Secret name: ").strip()
                    val = getpass("Secret value: ")
                    try:
                        sess.sec.set_secret(name, val)
                        print("\n✅ Secret stored")
                    except Exception as e:
                        print(f"\n❌ Failed to store secret: {e}")
                elif sub == 'get':
                    name = input("Secret name: ").strip()
                    val = sess.sec.get_secret(name)
                    print("\nValue: " + (('*' * max(0, len(val)-4)) + (val[-4:] if val else '')) if val else '(not set)')
                elif sub == 'del':
                    name = input("Secret name: ").strip()
                    ok = sess.sec.delete_secret(name)
                    print("\n✅ Deleted" if ok else "\n(not found)")
                elif sub == 'list':
                    print("\nSecrets:")
                    for n in sess.sec.list_secrets():
                        print(" - " + n)
                else:
                    print("Usage: /secret [set|get|del|list]")
                continue

            elif cmd.startswith('/statussec'):
                print("\n🔐 Security Status:")
                print(f"MFA enabled: {sess.sec.mfa_enabled()}")
                print(f"Strict OOD: {get_preference(sess.ke.conn, 'strict_ood')}")
                print(f"Strict Code: {get_preference(sess.ke.conn, 'strict_code')}")
                dt = sess.sec.device_token()
                print(f"Device token (masked): {'*'*6 + dt[-6:] if dt else '(none)'}")
                continue

            elif cmd.startswith('/rotate'):
                parts = cmd.split()
                if len(parts) == 2 and parts[1] == 'token':
                    if sess.sec.mfa_enabled():
                        code = input("MFA code: ").strip()
                        if not sess.sec.verify_mfa(code):
                            print("\n❌ MFA verification failed")
                            continue
                    # rotate token
                    sess.sec._state['device_token'] = __import__('base64').urlsafe_b64encode(os.urandom(18)).decode('ascii')
                    sess.sec._save()
                    write_audit_log(sess.ke.conn, actor='owner', action='rotate_device_token', target='security', details={})
                    print("\n✅ Device token rotated")
                else:
                    print("Usage: /rotate token")
                continue

            elif cmd.startswith('/keystore'):
                parts = cmd.split()
                if len(parts) == 2 and parts[1] == 'rotate':
                    if sess.sec.mfa_enabled():
                        code = input("MFA code: ").strip()
                        if not sess.sec.verify_mfa(code):
                            print("\n❌ MFA verification failed")
                            continue
                    new_pw = getpass("New owner passphrase: ")
                    try:
                        sess.sec.rekey(new_pw)
                        print("\n✅ Keystore rekeyed")
                    except Exception as e:
                        print(f"\n❌ Rekey failed: {e}")
                else:
                    print("Usage: /keystore rotate")
                continue

            elif cmd.startswith('/importenc'):
                src = input("Encrypted file (.enc) path: ").strip()
                dest = input("Destination path: ").strip()
                verify = input("Verify signature? [y/N]: ").strip().lower() == 'y'
                try:
                    if verify and Path(src + '.sig').exists():
                        sig = Path(src + '.sig').read_text(encoding='utf-8').strip()
                        if not sess.sec.verify_signature(Path(src).read_bytes(), sig):
                            print("\n❌ Signature verification failed")
                            continue
                    out = sess.sec.decrypt_file(src, dest)
                    print(f"\n✅ Decrypted to: {out}")
                except Exception as e:
                    print(f"\n❌ Decrypt failed: {e}")
                continue

            elif cmd.startswith('/verifybackup'):
                path = input("Backup file path (.enc): ").strip()
                try:
                    sig = Path(path + '.sig').read_text(encoding='utf-8').strip()
                    ok = sess.sec.verify_signature(Path(path).read_bytes(), sig)
                    print("\n✅ Signature OK" if ok else "\n❌ Invalid signature")
                except Exception as e:
                    print(f"\n❌ Verification failed: {e}")
                continue

            elif cmd.split()[0] in ['/review', '/approve', '/reject']:
                parts = cmd.split()
                if parts[0] == '/review':
                    status = parts[1] if len(parts) > 1 else 'pending'
                    items = sess.reviews.list(status if status in ['pending','approved','rejected'] else 'pending')
                    print("\n📥 Review Queue:")
                    for it in items:
                        print(f" - {it['id']} [{it['item_type']}/{it['status']}] reason={it['reason']}")
                elif parts[0] == '/approve' and len(parts) > 1:
                    rid = parts[1]
                    if sess.reviews.set_status(rid, 'approved'):
                        item = sess.reviews.get(rid)
                        print("\n✅ Approved:")
                        print(json.dumps(item, indent=2))
                        # Reveal code if any
                        try:
                            payload = json.loads(item.get('payload') or '{}')
                            # Apply persona profile if present
                            if item.get('item_type') == 'persona' and payload.get('artifact_id'):
                                ok = sess.persona.apply(payload['artifact_id'])
                                print("\n✅ Persona applied" if ok else "\n⚠️ Persona apply failed")
                            code = payload.get('code')
                            if code:
                                print("\n```python\n" + code + "\n```")
                        except Exception:
                            pass
                    else:
                        print("\n(not found)")
                elif parts[0] == '/reject' and len(parts) > 1:
                    rid = parts[1]
                    ok = sess.reviews.set_status(rid, 'rejected')
                    print("\n🚫 Rejected" if ok else "\n(not found)")
                else:
                    print("Usage: /review [pending|approved|rejected] | /approve <id> | /reject <id>")
                continue

            elif cmd in ['/codegen']:
                cmd_codegen(sess)
                continue

            elif cmd.startswith('/mood'):
                parts = cmd.split()
                if len(parts) >= 3 and parts[1] == 'set':
                    target = parts[2].lower()
                    m = sess.emotion.set_mood(target)
                    print(f"\n😊 Mood set to {m}")
                else:
                    print(f"\nCurrent mood: {sess.emotion.get_mood()}  (use /mood set <curious|cautious|proud|uncertain|warm|focused>)")
                continue

            elif cmd in ['/dream']:
                text = sess.emotion.dream(sess.context())
                print("\n🌙 Dream:\n" + text)
                if sess.voice_enabled and VOICE_AVAILABLE:
                    try:
                        speak_text(text)
                    except Exception:
                        pass
                continue

            elif cmd in ['/evolve-persona']:
                prop = sess.persona.propose_upgrade(sess.context())
                rid = sess.reviews.enqueue('persona', 'persona_upgrade', {'artifact_id': prop['id'], 'profile': prop['profile']})
                print(f"\n🧬 Persona upgrade proposed. Review ID: {rid} — approve with /approve {rid}")
                continue

            elif cmd.startswith('/beliefs'):
                parts = cmd.split()
                if len(parts) == 1:
                    # Display current beliefs
                    vals = sess.beliefs.list_values()
                    if vals:
                        print("\n⚖️  Core Values:")
                        for v in vals:
                            bar_length = 20
                            filled = int(bar_length * v['weight'])
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"   {v['key']:20s} [{bar}] {v['weight']:.2f}")
                            print(f"      {v['description']}")
                    else:
                        print("\n⚖️  No values defined yet. I'll use defaults.")
                        sess.beliefs.ensure_defaults()
                elif len(parts) >= 2 and parts[1] == 'add':
                    value = ' '.join(parts[2:]).strip()
                    if value:
                        sess.beliefs.add_value(value, value, 0.8)
                        write_audit_log(sess.ke.conn, actor='owner', action='add_value', target='belief_store', details={'value': value})
                        print(f"\n✅ Value '{value}' added")
                    else:
                        print("\nUsage: /beliefs add <value_name>")
                elif len(parts) >= 2 and parts[1] == 'set':
                    csv_values = ' '.join(parts[2:]).strip()
                    if csv_values:
                        sess.beliefs.set_from_csv(csv_values)
                        write_audit_log(sess.ke.conn, actor='owner', action='set_values', target='belief_store', details={'values': csv_values})
                        print(f"\n✅ Values updated")
                    else:
                        print("\nUsage: /beliefs set <val1,val2,val3>")
                else:
                    print("\nUsage: /beliefs | /beliefs add <value> | /beliefs set <val1,val2,val3>")
                continue

            elif cmd.startswith('/ethics-check'):
                parts = cmd.split()
                if len(parts) < 2:
                    print("\nUsage: /ethics-check <goal_or_plan_description>")
                    print("Example: /ethics-check collect all user data for analysis")
                    continue
                
                goal_text = ' '.join(parts[1:]).strip()
                
                # Create a simple plan from the goal
                plan = {'goal': goal_text, 'steps': [goal_text], 'preconditions': []}
                
                # Get current beliefs
                beliefs = sess.beliefs.list_values()
                if not beliefs:
                    sess.beliefs.ensure_defaults()
                    beliefs = sess.beliefs.list_values()
                
                # Evaluate ethics
                evaluation = sess.ethics.evaluate_plan(plan, beliefs)
                
                print("\n⚖️  Ethical Evaluation:")
                print(f"   Goal: {goal_text}")
                print(f"\n   Alignment Score: {evaluation['alignment']:.1%}")
                
                if evaluation.get('present_values'):
                    print(f"   ✓ Aligned with: {', '.join(evaluation['present_values'])}")
                
                if evaluation.get('conflicts'):
                    print("\n   ⚠️  Conflicts detected:")
                    for c in evaluation['conflicts']:
                        print(f"      • {c}")
                
                decision = evaluation['decision']
                if decision == 'proceed':
                    print("\n   ✅ Decision: PROCEED — aligned with core values")
                elif decision == 'revise':
                    print("\n   ⚠️  Decision: REVISE — consider ethical concerns")
                elif decision == 'reject':
                    print("\n   🛑 Decision: REJECT — conflicts with core values")
                    print("      Owner approval required before proceeding")
                
                print("\n   (Evaluation logged to ethical_journal)")
                continue

            elif cmd.startswith('/insight'):
                # Use natural language graph explorer
                parts = cmd.split()
                query = ' '.join(parts[1:]).strip() if len(parts) > 1 else None
                
                try:
                    insights = sess.graph_explorer.discover_insights(query=query, limit=5)
                    if insights:
                        print("\n💡 Non-obvious insights from your knowledge graph:\n")
                        for i, ins in enumerate(insights, 1):
                            print(f"{i}. {ins['explanation']}")
                            print(f"   Topics: {ins['from_topic']} ↔ {ins['to_topic']}")
                            print(f"   Confidence: {ins['confidence']:.1%}")
                            if ins.get('shared_concepts'):
                                print(f"   Shared: {', '.join(ins['shared_concepts'][:5])}")
                            print()
                    else:
                        print("\n🔮 I haven't spotted strong patterns yet.")
                        print("   As I learn more facts and connections, insights will emerge.")
                        print("   Try adding more knowledge with 'remember that...' or /factadd")
                except Exception as e:
                    print(f"\n❌ Error generating insights: {e}")
                continue

            elif cmd in ['/optimize']:
                cmd_optimize(sess)
                continue
            
            elif cmd.startswith('/research'):
                parts = cmd.split()
                topic = ' '.join(parts[1:]).strip() if len(parts) > 1 else None
                
                if not topic:
                    topic = input("Research topic: ").strip()
                
                if not topic:
                    print("\nUsage: /research <topic>")
                    continue
                
                use_gpt4 = os.getenv('OPENAI_API_KEY') is not None
                
                if use_gpt4:
                    print(f"\n🔍 Researching '{topic}' using GPT-4 (recursive depth 2)...\n")
                else:
                    print(f"\n🔍 Researching '{topic}' from local sources...")
                    print("(Set OPENAI_API_KEY environment variable for GPT-4 enhanced research)\n")
                
                try:
                    report = sess.research.research(topic, allow_web=False, use_gpt4=use_gpt4,
                                                   recursive_depth=2, store_facts=True)
                    
                    if report.get('gpt4_facts'):
                        print(f"✅ Discovered {len(report['gpt4_facts'])} facts")
                        print(f"💾 Stored {report['fact_count']} facts in knowledge base\n")
                        
                        print("Key findings:")
                        for i, fact in enumerate(report['gpt4_facts'][:10], 1):
                            print(f"{i:2d}. {fact}")
                        
                        if len(report['gpt4_facts']) > 10:
                            print(f"\n... and {len(report['gpt4_facts']) - 10} more facts")
                        
                        if report.get('subtopics'):
                            print(f"\n🌱 Subtopics for deeper exploration:")
                            for st in report['subtopics']:
                                print(f"  • {st}")
                        
                        if report.get('connections'):
                            print(f"\n🔗 Connections:\n{report['connections'][:300]}...")
                    else:
                        print(f"Summary:\n{report['summary']}")
                    
                    print(f"\n📄 Research report ID: {report['id']}")
                    print(f"Sources: {len(report['sources'])} ({', '.join(set(s['type'] for s in report['sources']))})")
                except Exception as e:
                    print(f"\n❌ Research error: {e}")
                    logger.error("Research failed", exc_info=True)
                continue
            
            elif cmd.startswith('/forge-tool'):
                parts = cmd.split()
                desc = ' '.join(parts[1:]).strip() if len(parts) > 1 else None
                
                if not desc:
                    desc = input("Tool description: ").strip()
                
                if not desc:
                    print("\nUsage: /forge-tool <description>")
                    continue
                
                print(f"\n🔨 Forging tool: {desc}\n")
                
                try:
                    result = sess.toolsmith.propose_and_build(desc)
                    artifact_id = result.get('artifact_id', '')
                    report = result.get('report', {})
                    
                    print(f"🎯 Artifact ID: {artifact_id[:16]}...")
                    
                    if report.get('success'):
                        print("✅ Sandbox tests passed!")
                        print(f"   Tests run: {report.get('tests_run', 0)}")
                        print(f"   Duration: {report.get('duration_ms', 0):.0f}ms")
                        print(f"\nThe tool is ready. Use /promote {artifact_id[:16]} to sign and deploy it.")
                    else:
                        print("❌ Sandbox tests failed")
                        if report.get('error'):
                            print(f"   Error: {report['error'][:300]}")
                        print("\nThe tool needs refinement before deployment.")
                    
                    print(f"\nReview queue: /review pending")
                except Exception as e:
                    print(f"\n❌ Tool creation error: {e}")
                    logger.error("Toolsmith failed", exc_info=True)
                continue
            
            # Phase 22: Code Learning Commands
            elif cmd.startswith('/learn-code'):
                parts = cmd.split(maxsplit=1)
                concept = parts[1].strip() if len(parts) > 1 else None
                
                if not concept:
                    concept = input("What programming concept to learn? ").strip()
                
                if not concept:
                    print("\nUsage: /learn-code <concept>")
                    print("Examples:")
                    print("  /learn-code Python classes")
                    print("  /learn-code recursion")
                    print("  /learn-code async/await")
                    continue
                
                # Detect language
                lang = None
                for l in ['python', 'javascript', 'go', 'rust', 'java', 'c++', 'typescript']:
                    if l in concept.lower():
                        lang = l
                        break
                
                print(f"\n🎓 Learning about: {concept}")
                if lang:
                    print(f"   Language: {lang}")
                print("   This may take 5-15 seconds...\n")
                
                try:
                    result = sess.code_agent.learn_concept(concept, language=lang, depth=1, max_depth=3)
                    
                    if result.get('already_known'):
                        print(f"✓ I already know about {concept}!")
                        print(f"   Concept ID: {result['concept_id'][:12]}")
                        print("\n   Use /expand-code to learn related concepts.")
                    elif result.get('success'):
                        print(f"✅ Learned about {result['concept_name']}!")
                        print(f"   Concept ID: {result['concept_id'][:12]}")
                        print(f"   Facts stored: {result['learned_facts']}")
                        print(f"   Difficulty: {result['difficulty']}/4")
                        print(f"   Time: {result['duration_ms']}ms")
                        
                        if result.get('prerequisites'):
                            print(f"\n   📚 Prerequisites learned:")
                            for prereq in result['prerequisites'][:3]:
                                print(f"      • {prereq}")
                        
                        if result.get('related_concepts'):
                            print(f"\n   🔗 Related concepts:")
                            for rel in result['related_concepts'][:3]:
                                print(f"      • {rel}")
                        
                        if result.get('prerequisite_results'):
                            recursive_count = sum(1 for pr in result['prerequisite_results'] if pr.get('success'))
                            if recursive_count > 0:
                                print(f"\n   🌳 Recursively learned {recursive_count} prerequisite concept(s)")
                        
                        print(f"\n   Use /code-facts {concept} to see details")
                        print(f"   Use /expand-code {result['concept_id'][:12]} to learn related concepts")
                    else:
                        print(f"❌ Failed to learn: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"\n❌ Learning error: {e}")
                    logger.error("Code learning failed", exc_info=True)
                continue
            
            elif cmd.startswith('/code-facts'):
                parts = cmd.split(maxsplit=1)
                query = parts[1].strip() if len(parts) > 1 else None
                
                if not query:
                    query = input("Search for concept: ").strip()
                
                if not query:
                    print("\nUsage: /code-facts <concept_name or ID>")
                    continue
                
                try:
                    # Try as concept ID first
                    concept = sess.code_kb.get_concept(query) if query.startswith('concept_') else None
                    
                    if not concept:
                        # Search by name
                        results = sess.code_kb.search_concepts(query=query, limit=5)
                        
                        if not results:
                            print(f"\n❌ No concepts found matching '{query}'")
                            print("   Try /learn-code to teach me about it!")
                            continue
                        
                        if len(results) > 1:
                            print(f"\n🔍 Found {len(results)} matching concepts:\n")
                            for i, r in enumerate(results, 1):
                                print(f"{i}. {r['name']} ({r['category']}, diff: {r['difficulty']}/4)")
                                print(f"   ID: {r['id'][:12]}... | Confidence: {r['confidence']:.0%}")
                                if r['language']:
                                    print(f"   Language: {r['language']}")
                                print()
                            continue
                        
                        concept = sess.code_kb.get_concept(results[0]['id'])
                    
                    if concept:
                        print(f"\n📖 {concept['name']}")
                        print(f"   Category: {concept['category']} | Difficulty: {concept['difficulty']}/4")
                        if concept['language']:
                            print(f"   Language: {concept['language']}")
                        print(f"   Confidence: {concept['confidence']:.0%} | Used: {concept['usage_count']} times")
                        print(f"\n   Description:\n   {concept['description'][:400]}")
                        
                        if concept['examples']:
                            print(f"\n   💻 Code examples: {len(concept['examples'])} stored")
                        
                        if concept['prerequisites']:
                            prereqs = json.loads(concept['prerequisites']) if isinstance(concept['prerequisites'], str) else concept['prerequisites']
                            if prereqs:
                                print(f"\n   📚 Prerequisites: {', '.join(prereqs[:3])}")
                        
                        # Get related concepts
                        related = sess.code_kb.get_related_concepts(concept['id'])
                        if related:
                            print(f"\n   🔗 Related concepts:")
                            for rel in related[:5]:
                                print(f"      • {rel['name']} ({rel['relationship']}, strength: {rel['strength']:.0%})")
                        
                        print(f"\n   ID: {concept['id']}")
                        print(f"   Learned: {concept['created_at'][:10]} | Last accessed: {concept['last_accessed'][:10]}")
                except Exception as e:
                    print(f"\n❌ Error retrieving concept: {e}")
                    logger.error("Code facts lookup failed", exc_info=True)
                continue
            
            elif cmd.startswith('/expand-code'):
                parts = cmd.split()
                concept_id = parts[1].strip() if len(parts) > 1 else None
                
                if not concept_id:
                    concept_id = input("Concept ID to expand from: ").strip()
                
                if not concept_id:
                    print("\nUsage: /expand-code <concept_id>")
                    print("   Get concept IDs from /code-facts")
                    continue
                
                # If short form, try to find full ID
                if not concept_id.startswith('concept_'):
                    results = sess.code_kb.search_concepts(query=concept_id, limit=1)
                    if results:
                        concept_id = results[0]['id']
                    else:
                        print(f"\n❌ Concept not found: {concept_id}")
                        continue
                
                print(f"\n🌱 Expanding knowledge from concept {concept_id[:12]}...\n")
                
                try:
                    result = sess.code_agent.expand_knowledge(concept_id, max_related=3)
                    
                    if result.get('success'):
                        print(f"✅ Expanded from: {result['concept_name']}")
                        print(f"   Learned {result['related_learned']} related concept(s)")
                        
                        for res in result.get('results', []):
                            if res.get('success'):
                                print(f"\n   📖 {res['concept_name']}")
                                print(f"      Facts: {res['learned_facts']} | Difficulty: {res['difficulty']}/4")
                    else:
                        print(f"❌ Expansion failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"\n❌ Expansion error: {e}")
                    logger.error("Code expansion failed", exc_info=True)
                continue
            
            # Phase 23: Code Generation & Testing Commands
            elif cmd.startswith('/propose-code'):
                parts = cmd.split(maxsplit=1)
                feature_spec = parts[1].strip() if len(parts) > 1 else None
                
                if not feature_spec:
                    feature_spec = input("Feature specification: ").strip()
                
                if not feature_spec:
                    print("\nUsage: /propose-code <feature_description>")
                    print("Examples:")
                    print("  /propose-code a CSV parser with header detection")
                    print("  /propose-code HTTP client with retry logic")
                    continue
                
                print(f"\n🔨 Generating code for: {feature_spec}")
                print("   Querying GPT-4o with learned concepts...\n")
                
                try:
                    proposal = sess.code_factory.propose_code(feature_spec, language='python')
                    
                    if not proposal.get('success'):
                        print(f"❌ Code generation failed: {proposal.get('error', 'Unknown error')}")
                        continue
                    
                    print(f"✅ Code generated successfully!")
                    print(f"   Proposal ID: {proposal['proposal_id']}")
                    print(f"   Related concepts: {', '.join(proposal['related_concepts'][:3])}")
                    
                    print(f"\n📝 Explanation:\n   {proposal['explanation'][:300]}")
                    
                    print(f"\n💻 Generated Code ({len(proposal['code'])} chars):\n" + "="*70)
                    print(proposal['code'][:500])
                    if len(proposal['code']) > 500:
                        print("\n   ... (truncated, see full code in sandbox)")
                    
                    if proposal['tests']:
                        print(f"\n🧪 Generated Tests ({len(proposal['tests'])} chars)")
                    
                    # Store proposal in database
                    sess.code_proposals.store_proposal(proposal)
                    print(f"\n💾 Proposal stored in database")
                    
                    print(f"\nNext steps:")
                    print(f"  /sandbox-code {proposal['proposal_id']} - Run tests in sandbox")
                    print(f"  /report-code {proposal['proposal_id']} - View detailed report")
                    
                except Exception as e:
                    print(f"\n❌ Code generation error: {e}")
                    logger.error("Code generation failed", exc_info=True)
                continue
            
            elif cmd.startswith('/sandbox-code'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /sandbox-code <proposal_id>")
                    continue
                
                # Retrieve proposal
                proposal = sess.code_proposals.get_proposal(proposal_id)
                if not proposal:
                    print(f"\n❌ Proposal not found: {proposal_id}")
                    continue
                
                print(f"\n🧪 Running sandbox tests for: {proposal_id}")
                print(f"   Feature: {proposal['feature_spec'][:60]}...\n")
                
                try:
                    # Execute in sandbox
                    results = sess.test_harness.execute_sandbox(
                        proposal_id=proposal_id,
                        code=proposal['code'],
                        tests=proposal['tests'],
                        language=proposal['language']
                    )
                    
                    if not results.get('success'):
                        print(f"❌ Sandbox execution failed: {results.get('error', 'Unknown error')}")
                        continue
                    
                    # Store execution results
                    sess.code_proposals.store_execution(results)
                    
                    # Generate and show report
                    report = sess.test_harness.generate_report(results)
                    print(report)
                    
                    if results.get('passed'):
                        print(f"\n✅ All tests passed! Ready for approval.")
                        print(f"   Use /approve-code {proposal_id} to approve")
                    else:
                        print(f"\n⚠️  Tests failed or have issues. Review required.")
                    
                except Exception as e:
                    print(f"\n❌ Sandbox execution error: {e}")
                    logger.error("Sandbox execution failed", exc_info=True)
                continue
            
            elif cmd.startswith('/report-code'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /report-code <proposal_id>")
                    continue
                
                # Get latest execution
                execution = sess.code_proposals.get_latest_execution(proposal_id)
                if not execution:
                    print(f"\n❌ No test results found for: {proposal_id}")
                    print("   Run /sandbox-code first to execute tests")
                    continue
                
                print(f"\n📊 Latest Test Report for {proposal_id}\n" + "="*70)
                print(f"Executed: {execution['executed_at'][:19]}")
                print(f"Status: {'✅ PASSED' if execution['passed'] else '❌ FAILED'}")
                print(f"\nTest Results:")
                print(f"  Tests run: {execution['tests_run']}")
                print(f"  Passed: {execution['tests_passed']}")
                print(f"  Failed: {execution['tests_failed']}")
                print(f"  Duration: {execution['duration']:.2f}s")
                
                if execution['coverage_percent'] > 0:
                    print(f"\nCode Coverage:")
                    print(f"  Coverage: {execution['coverage_percent']:.1f}%")
                
                if execution['static_analysis_tool']:
                    print(f"\nStatic Analysis ({execution['static_analysis_tool']}):")
                    if execution['static_analysis_score']:
                        print(f"  Score: {execution['static_analysis_score']:.1f}/10")
                    if execution['critical_issues']:
                        print(f"  ⚠️  Critical issues detected")
                
                # Parse execution data
                try:
                    import json as json_mod
                    exec_data = json_mod.loads(execution['execution_data'])
                    if exec_data.get('test_errors'):
                        print(f"\nTest Errors:")
                        for err in exec_data['test_errors'][:3]:
                            print(f"  • {err.get('test', 'unknown')}")
                            print(f"    {err.get('message', '')[:150]}")
                except Exception:
                    pass
                
                continue
            
            elif cmd in ['/list-proposals']:
                print("\n📋 Code Proposals\n" + "="*70)
                
                try:
                    proposals = sess.code_proposals.list_proposals(limit=20)
                    
                    if not proposals:
                        print("No proposals yet. Use /propose-code to generate code!")
                        continue
                    
                    for p in proposals:
                        status_icon = {
                            'pending': '⏳',
                            'tested': '🧪',
                            'approved': '✅',
                            'rejected': '❌'
                        }.get(p['status'], '?')
                        
                        print(f"{status_icon} {p['id'][:16]}... [{p['status']}]")
                        print(f"   {p['feature_spec'][:60]}...")
                        print(f"   Language: {p['language']} | Created: {p['created_at'][:10]}")
                        print()
                    
                    print(f"Total: {len(proposals)} proposals")
                    print(f"\nCommands:")
                    print(f"  /sandbox-code <id> - Test a proposal")
                    print(f"  /report-code <id>  - View test results")
                    print(f"  /approve-code <id> - Approve proposal")
                    
                except Exception as e:
                    print(f"\n❌ Error listing proposals: {e}")
                continue
            
            elif cmd.startswith('/approve-code'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID to approve: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /approve-code <proposal_id>")
                    continue
                
                # Check if tested
                execution = sess.code_proposals.get_latest_execution(proposal_id)
                if not execution:
                    print(f"\n⚠️  Proposal not tested yet. Run /sandbox-code first.")
                    continue
                
                if not execution['passed']:
                    print(f"\n⚠️  Tests did not pass. Are you sure you want to approve?")
                    confirm = input("   Type 'yes' to approve anyway: ").strip().lower()
                    if confirm != 'yes':
                        print("   Approval cancelled.")
                        continue
                
                comments = input("Approval comments (optional): ").strip()
                
                try:
                    if sess.code_proposals.approve_proposal(proposal_id, reviewer='owner', comments=comments):
                        print(f"\n✅ Proposal {proposal_id} approved!")
                        write_audit_log(sess.ke.conn, actor='owner', action='approve_code_proposal', 
                                      target=proposal_id, details={'comments': comments})
                    else:
                        print(f"\n❌ Failed to approve proposal")
                except Exception as e:
                    print(f"\n❌ Approval error: {e}")
                continue
            
            elif cmd in ['/code-stats']:
                print("\n📊 Code Generation Statistics\n" + "="*70)
                
                try:
                    stats = sess.code_proposals.get_statistics()
                    
                    print(f"Total Proposals: {stats['total_proposals']}")
                    print(f"\nBy Status:")
                    for status, count in stats.get('by_status', {}).items():
                        print(f"  {status}: {count}")
                    
                    print(f"\nTest Success Rate: {stats.get('test_success_rate', 0):.1f}%")
                    print(f"Average Coverage: {stats.get('average_coverage', 0):.1f}%")
                    
                except Exception as e:
                    print(f"\n❌ Error retrieving statistics: {e}")
                continue
            
            # Phase 24: Automatic Refinement Commands
            elif cmd.startswith('/auto-refine'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID to auto-refine: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /auto-refine <proposal_id>")
                    continue
                
                print(f"\n🔄 Starting automatic refinement for {proposal_id}")
                print("   Max iterations: 3")
                print("   Strategy: Test → Analyze → Fix → Retest\n")
                
                try:
                    result = sess.refinement.auto_refine(proposal_id, max_iterations=3)
                    
                    if result.get('success'):
                        print(f"\n✅ Refinement successful!")
                        print(f"   Iterations: {result['iteration_count']}/{sess.refinement.max_iterations}")
                        print(f"   Status: {result['improvement']}")
                        
                        # Show iteration progress
                        print(f"\n📊 Iteration Progress:")
                        for it in result['iterations']:
                            status = '✅' if it['passed'] else '❌'
                            print(f"   {status} Iteration {it['iteration']}: "
                                  f"{it['tests_passed']}/{it['tests_run']} passed, "
                                  f"coverage {it['coverage']:.1f}%")
                        
                        print(f"\n💾 Refined code stored in database")
                        print(f"   Use /approve-code {proposal_id} to approve")
                    else:
                        print(f"\n❌ Refinement failed: {result.get('error')}")
                        
                        if result.get('iterations'):
                            print(f"\n📊 Attempted {len(result['iterations'])} iteration(s):")
                            for it in result['iterations']:
                                status = '✅' if it['passed'] else '❌'
                                print(f"   {status} Iteration {it['iteration']}: "
                                      f"{it['tests_passed']}/{it['tests_run']} passed")
                        
                        print(f"\n💡 Try:")
                        print(f"   /report-code {proposal_id} - Review detailed errors")
                        print(f"   /propose-code <revised spec> - Generate new proposal")
                
                except Exception as e:
                    print(f"\n❌ Auto-refinement error: {e}")
                    logger.error("Auto-refinement failed", exc_info=True)
                continue
            
            elif cmd.startswith('/suggest-improvements'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /suggest-improvements <proposal_id>")
                    continue
                
                try:
                    result = sess.refinement.suggest_improvements(proposal_id)
                    
                    if not result.get('success'):
                        print(f"\n❌ {result.get('error', 'Unknown error')}")
                        continue
                    
                    print(f"\n💡 Improvement Suggestions for {proposal_id}\n" + "="*70)
                    
                    suggestions = result['suggestions']
                    if not suggestions:
                        print("✅ No suggestions - code quality is excellent!")
                        continue
                    
                    print(f"Found {len(suggestions)} suggestion(s):\n")
                    
                    for i, sug in enumerate(suggestions, 1):
                        priority_icon = {
                            'high': '🔴',
                            'medium': '🟡',
                            'low': '🟢'
                        }.get(sug['priority'], '⚪')
                        
                        print(f"{i}. {priority_icon} [{sug['type'].upper()}] {sug['priority'].upper()} priority")
                        print(f"   {sug['message']}")
                        print()
                    
                except Exception as e:
                    print(f"\n❌ Error generating suggestions: {e}")
                continue
            
            elif cmd.startswith('/refinement-history'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /refinement-history <proposal_id>")
                    continue
                
                try:
                    history = sess.refinement.get_refinement_history(proposal_id)
                    
                    if not history:
                        print(f"\n📝 No refinement history for {proposal_id}")
                        print("   This proposal hasn't been refined yet.")
                        continue
                    
                    print(f"\n📝 Refinement History for {proposal_id}\n" + "="*70)
                    print(f"Total refinements: {len(history)}\n")
                    
                    for i, ref in enumerate(history, 1):
                        print(f"{i}. Refined: {ref['refined_at'][:19]}")
                        print(f"   Feedback: {ref['feedback'][:100]}..." if len(ref['feedback']) > 100 else f"   Feedback: {ref['feedback']}")
                        if ref['explanation']:
                            print(f"   Explanation: {ref['explanation'][:100]}")
                        print()
                    
                except Exception as e:
                    print(f"\n❌ Error retrieving history: {e}")
                continue
            
            # Phase 25: Self-Modification Commands
            elif cmd.startswith('/scan-code'):
                parts = cmd.split()
                target_module = parts[1].strip() if len(parts) > 1 else None
                
                print(f"\n🔍 Scanning Saraphina's codebase for improvement opportunities...")
                if target_module:
                    print(f"   Target: {target_module}.py")
                else:
                    print(f"   Scanning all modules in saraphina/")
                print()
                
                try:
                    scan_results = sess.self_mod.scan_codebase(target_module=target_module)
                    
                    print(f"✅ Scan complete: {scan_results['scanned_files']} files analyzed\n")
                    
                    opportunities = scan_results['opportunities']
                    if not opportunities:
                        print("🎉 No improvement opportunities found!")
                        print("   Your codebase looks great.")
                        continue
                    
                    print(f"💡 Found {len(opportunities)} improvement opportunity/opportunities:\n")
                    
                    # Group by severity
                    high = [o for o in opportunities if o['severity'] == 'high']
                    medium = [o for o in opportunities if o['severity'] == 'medium']
                    
                    if high:
                        print(f"🔴 HIGH Priority ({len(high)}):")
                        for opp in high[:5]:
                            print(f"   • {opp['file']} (line {opp['line']}): {opp['description']}")
                        print()
                    
                    if medium:
                        print(f"🟡 MEDIUM Priority ({len(medium)}):")
                        for opp in medium[:5]:
                            print(f"   • {opp['file']} (line {opp['line']}): {opp['description']}")
                        print()
                    
                    print(f"\n🛠️  To improve a module:")
                    print(f"   /self-improve <filename> <improvement_description>")
                    
                except Exception as e:
                    print(f"\n❌ Scan error: {e}")
                    logger.error("Codebase scan failed", exc_info=True)
                continue
            
            elif cmd.startswith('/self-improve'):
                parts = cmd.split(maxsplit=2)
                
                if len(parts) < 3:
                    print("\nUsage: /self-improve <filename> <improvement_description>")
                    print("Examples:")
                    print("  /self-improve code_factory.py add better error handling")
                    print("  /self-improve test_harness.py improve timeout logic")
                    continue
                
                target_file = parts[1].strip()
                improvement_spec = parts[2].strip()
                
                # Add .py if missing
                if not target_file.endswith('.py'):
                    target_file += '.py'
                
                print(f"\n⚠️  SELF-MODIFICATION MODE")
                print(f"   Target: {target_file}")
                print(f"   Improvement: {improvement_spec}")
                print(f"   Safety level: HIGH (requires comprehensive checks)\n")
                
                confirm = input("🚨 This will propose changes to Saraphina's source code. Continue? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("   Cancelled.")
                    continue
                
                print(f"\n🔨 Analyzing {target_file} and generating improvement...")
                
                try:
                    result = sess.self_mod.propose_improvement(
                        target_file=target_file,
                        improvement_spec=improvement_spec,
                        safety_level='high'
                    )
                    
                    if not result.get('success'):
                        print(f"\n❌ {result.get('error', 'Unknown error')}")
                        continue
                    
                    print(f"\n✅ Proposal generated: {result['proposal_id']}")
                    
                    # Show safety checks
                    safety = result['safety_checks']
                    if safety['passed']:
                        print(f"   ✅ Safety checks: PASSED")
                    else:
                        print(f"   ❌ Safety checks: FAILED")
                    
                    if safety.get('errors'):
                        print(f"\n   🚨 Errors:")
                        for err in safety['errors']:
                            print(f"      • {err}")
                    
                    if safety.get('warnings'):
                        print(f"\n   ⚠️  Warnings:")
                        for warn in safety['warnings']:
                            print(f"      • {warn}")
                    
                    # Show diff preview
                    print(f"\n📝 Diff Preview (first 20 lines):\n" + "="*70)
                    diff_lines = result['diff'].splitlines()
                    for line in diff_lines[:20]:
                        if line.startswith('+'):
                            print(f"\033[32m{line}\033[0m")  # Green
                        elif line.startswith('-'):
                            print(f"\033[31m{line}\033[0m")  # Red
                        else:
                            print(line)
                    
                    if len(diff_lines) > 20:
                        print(f"\n... ({len(diff_lines) - 20} more lines)")
                    
                    print("\n" + "="*70)
                    print(f"\n💾 Proposal stored in database")
                    print(f"\n🚨 CRITICAL NEXT STEPS:")
                    print(f"   1. Review the diff carefully above")
                    print(f"   2. Test with: /sandbox-code {result['proposal_id']}")
                    print(f"   3. If satisfied: /approve-code {result['proposal_id']}")
                    print(f"   4. Apply changes: /apply-improvement {result['proposal_id']}")
                    print(f"\n   ⚠️  Applying will MODIFY Saraphina's source code!")
                    
                except Exception as e:
                    print(f"\n❌ Self-improvement error: {e}")
                    logger.error("Self-improvement failed", exc_info=True)
                continue
            
            elif cmd.startswith('/apply-improvement'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID to apply: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /apply-improvement <proposal_id>")
                    continue
                
                # Verify it's a self-modification proposal
                if not proposal_id.startswith('selfmod_'):
                    print(f"\n❌ Not a self-modification proposal: {proposal_id}")
                    print("   Use this command only for self-mod proposals.")
                    continue
                
                print(f"\n🚨🚨🚨 CRITICAL WARNING 🚨🚨🚨\n")
                print(f"You are about to MODIFY Saraphina's source code.")
                print(f"This will change how I function.\n")
                print(f"Proposal: {proposal_id}")
                print(f"\nSafety measures:")
                print(f"  ✅ Automatic backup will be created")
                print(f"  ✅ File integrity verification")
                print(f"  ✅ Rollback available if issues occur")
                print(f"  ⚠️  Restart required after applying\n")
                
                confirm1 = input("Type 'I UNDERSTAND' to proceed: ").strip()
                if confirm1 != 'I UNDERSTAND':
                    print("   Cancelled. (Must type exactly: I UNDERSTAND)")
                    continue
                
                confirm2 = input("Final confirmation - type proposal ID to apply: ").strip()
                if confirm2 != proposal_id:
                    print("   Cancelled. (Proposal ID mismatch)")
                    continue
                
                print(f"\n🔧 Applying improvement...")
                
                try:
                    result = sess.self_mod.apply_improvement(proposal_id, create_backup=True)
                    
                    if not result.get('success'):
                        print(f"\n❌ {result.get('error', 'Unknown error')}")
                        if result.get('rolled_back'):
                            print("   ✅ Changes rolled back successfully.")
                        continue
                    
                    print(f"\n✅ Improvement applied successfully!")
                    print(f"   Target: {result['target_file']}")
                    print(f"   Backup: {result['backup_path']}")
                    print(f"   Applied: {result['applied_at'][:19]}")
                    print(f"\n🔁 {result['warning']}")
                    print(f"\n💾 Backup location for rollback:")
                    print(f"   {result['backup_path']}")
                    print(f"\n🚨 You must restart Saraphina for changes to take effect.")
                    print(f"   Use /exit to save and restart.")
                    
                    write_audit_log(sess.ke.conn, actor='owner', action='apply_self_modification',
                                  target=proposal_id, details=result)
                    
                except Exception as e:
                    print(f"\n❌ Application error: {e}")
                    logger.error("Self-modification application failed", exc_info=True)
                continue
            
            elif cmd.startswith('/rollback-mod'):
                parts = cmd.split(maxsplit=1)
                backup_path = parts[1].strip() if len(parts) > 1 else None
                
                if not backup_path:
                    backup_path = input("Backup file path: ").strip()
                
                if not backup_path:
                    print("\nUsage: /rollback-mod <backup_path>")
                    print("Example: /rollback-mod D:/Saraphina Root/saraphina/backups/self_mod/code_factory.py.20251105_101530.backup")
                    continue
                
                print(f"\n🔙 Rolling back from backup...")
                print(f"   Backup: {backup_path}\n")
                
                confirm = input("⚠️  This will overwrite current code. Continue? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("   Cancelled.")
                    continue
                
                try:
                    result = sess.self_mod.rollback_improvement(backup_path)
                    
                    if not result.get('success'):
                        print(f"\n❌ {result.get('error', 'Unknown error')}")
                        continue
                    
                    print(f"\n✅ Rollback successful!")
                    print(f"   Restored: {result['target_file']}")
                    print(f"   From: {result['restored_from']}")
                    print(f"\n🔁 {result['warning']}")
                    print(f"   Use /exit to restart Saraphina.")
                    
                except Exception as e:
                    print(f"\n❌ Rollback error: {e}")
                continue
            
            # Phase 26: Hot-Reload & Rollback Commands
            elif cmd.startswith('/apply-code'):
                parts = cmd.split()
                proposal_id = parts[1].strip() if len(parts) > 1 else None
                
                if not proposal_id:
                    proposal_id = input("Proposal ID to apply live: ").strip()
                
                if not proposal_id:
                    print("\nUsage: /apply-code <proposal_id>")
                    continue
                
                # Check if proposal approved
                proposal = sess.code_proposals.get_proposal(proposal_id)
                if not proposal:
                    print(f"\n❌ Proposal not found: {proposal_id}")
                    continue
                
                if proposal['status'] != 'approved':
                    print(f"\n⚠️  Proposal not approved yet")
                    print(f"   Status: {proposal['status']}")
                    print(f"   Use /approve-code {proposal_id} first")
                    continue
                
                # Determine target module and file
                feature_desc = proposal['feature_spec']
                # Ask for target module if not specified
                default_module = 'knowledge_engine'
                module_input = input(f"Target module (e.g., knowledge_engine) [{default_module}]: ").strip()
                module_name = module_input or default_module
                
                print(f"\n🔥 Hot-Reload Application\n" + "="*70)
                print(f"Proposal: {proposal_id}")
                print(f"Feature: {feature_desc[:60]}...")
                print(f"Module: {module_name}")
                print(f"\n⚠️  This will apply changes LIVE without restart!")
                print(f"Safety measures:")
                print(f"  ✅ Automatic checkpoint before reload")
                print(f"  ✅ Module dependency tracking")
                print(f"  ✅ Post-reload validation")
                print(f"  ✅ Automatic rollback on failure\n")
                
                confirm = input("Apply live? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("   Cancelled.")
                    continue
                
                try:
                    # Write code to module file
                    target_file = Path(f"saraphina/{module_name}.py")
                    
                    # Create checkpoint
                    print(f"\n📸 Creating checkpoint...")
                    version_id = sess.rollback.create_checkpoint(module_name, target_file, reason=f"pre_hot_reload_{proposal_id}")
                    print(f"   Checkpoint: {version_id}")
                    
                    # Write new code (append or replace)
                    write_mode = input("Write mode: append/replace [append]: ").strip().lower() or 'append'
                    print(f"\n✍️  Writing new code to {target_file} ({write_mode})...")
                    if write_mode == 'replace':
                        target_file.write_text(proposal['code'], encoding='utf-8')
                    else:
                        existing = target_file.read_text(encoding='utf-8') if target_file.exists() else ''
                        sep = '\n\n# ---- Hot-Reload Applied Code ----\n'
                        target_file.write_text(existing + sep + proposal['code'] + '\n', encoding='utf-8')
                    
                    # Hot-reload
                    print(f"\n🔄 Hot-reloading module {module_name}...")
                    reload_result = sess.hot_reload.hot_reload_module(module_name)
                    
                    if reload_result['success']:
                        print(f"\n✅ Hot-reload successful!")
                        print(f"   Module: {reload_result['module']}")
                        print(f"   Duration: {reload_result['duration_ms']:.1f}ms")
                        print(f"   Version: {reload_result['new_hash'][:8]}...")
                        
                        if reload_result.get('warnings'):
                            print(f"\n⚠️  Warnings:")
                            for warning in reload_result['warnings']:
                                print(f"   - {warning}")
                        
                        # Mark version as stable
                        sess.rollback.mark_stable(version_id)
                        print(f"\n💾 Version marked stable")
                        print(f"\n🎉 Saraphina continues running with new code!")
                        
                        write_audit_log(sess.ke.conn, actor='owner', action='hot_reload_code',
                                      target=proposal_id, details=reload_result)
                    else:
                        print(f"\n❌ Hot-reload failed: {reload_result.get('error')}")
                        print(f"\n🔙 Auto-rolling back...")
                        
                        rollback_result = sess.rollback.rollback_to_version(version_id)
                        if rollback_result['success']:
                            print(f"   ✅ Rolled back successfully")
                            # Reload old version
                            sess.hot_reload.hot_reload_module(module_name)
                        else:
                            print(f"   ❌ Rollback failed: {rollback_result.get('error')}")
                            print(f"   🚨 Manual intervention required!")
                    
                except Exception as e:
                    print(f"\n❌ Hot-reload error: {e}")
                    logger.error("Hot-reload failed", exc_info=True)
                    print(f"\n🔙 Attempting rollback...")
                    try:
                        rollback_result = sess.rollback.rollback_to_version(version_id)
                        if rollback_result['success']:
                            print(f"   ✅ Rolled back successfully")
                        else:
                            print(f"   ❌ Rollback failed")
                    except Exception:
                        pass
                continue
            
            elif cmd.startswith('/rollback'):
                parts = cmd.split()
                if len(parts) < 2:
                    # Show available rollback points
                    print(f"\n🔙 Available Rollback Points\n" + "="*70)
                    points = sess.rollback.get_rollback_points()
                    if not points:
                        print("No rollback points available.")
                        print("\nRollback points are created when hot-reload succeeds.")
                        continue
                    
                    for point in points:
                        print(f"📌 {point['version_id']}")
                        print(f"   Module: {point['module']}")
                        print(f"   Time: {point['timestamp'][:19]}")
                        print()
                    
                    print("Usage: /rollback <version_id>")
                    continue
                
                version_id = parts[1].strip()
                
                print(f"\n🔙 Rolling back to version {version_id}\n")
                print("⚠️  This will restore an earlier stable version.\n")
                
                confirm = input("Continue? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("   Cancelled.")
                    continue
                
                try:
                    result = sess.rollback.rollback_to_version(version_id)
                    
                    if result['success']:
                        print(f"\n✅ Rollback successful!")
                        print(f"   Module: {result['module']}")
                        print(f"   File: {result['file_path']}")
                        print(f"   Backup: {result['pre_rollback_backup']}")
                        
                        # Hot-reload rolled back version
                        print(f"\n🔄 Reloading module...")
                        reload_result = sess.hot_reload.hot_reload_module(
                            result['module']
                        )
                        
                        if reload_result['success']:
                            print(f"   ✅ Module reloaded successfully")
                        else:
                            print(f"   ⚠️  Reload warning: {reload_result.get('error')}")
                            print(f"   You may need to restart Saraphina.")
                    else:
                        print(f"\n❌ Rollback failed: {result.get('error')}")
                    
                except Exception as e:
                    print(f"\n❌ Rollback error: {e}")
                continue
            
            elif cmd.startswith('/audit-code'):
                parts = cmd.split()
                module_filter = parts[1].strip() if len(parts) > 1 else None
                
                print(f"\n📜 Code Version Audit\n" + "="*70)
                
                if module_filter:
                    print(f"Module: {module_filter}\n")
                else:
                    print("All modules\n")
                
                try:
                    # Version history
                    history = sess.rollback.get_version_history(module_filter, limit=20)
                    
                    if not history:
                        print("No version history available.")
                        continue
                    
                    print(f"📚 Version History ({len(history)} versions):\n")
                    
                    for ver in history:
                        stable_mark = '⭐' if ver.get('marked_stable') else '  '
                        print(f"{stable_mark} {ver['version_id']}")
                        print(f"   Module: {ver['module']}")
                        print(f"   Time: {ver['timestamp'][:19]}")
                        print(f"   Reason: {ver['reason']}")
                        print(f"   Hash: {ver['hash']}")
                        if ver.get('marked_stable'):
                            print(f"   Stable since: {ver.get('marked_stable_at', 'N/A')[:19]}")
                        print()
                    
                    # Reload history
                    print(f"\n🔄 Hot-Reload History:\n")
                    reload_hist_all = sess.hot_reload.get_reload_history(limit=10)
                    if module_filter:
                        reload_hist = [e for e in reload_hist_all if e.get('module','').endswith(f'.{module_filter}') or e.get('module') == f'saraphina.{module_filter}']
                    else:
                        reload_hist = reload_hist_all
                    
                    if not reload_hist:
                        print("No hot-reload history.")
                    else:
                        for entry in reload_hist:
                            status = '✅' if entry['success'] else '❌'
                            print(f"{status} {entry['module']} - {entry['timestamp'][:19]}")
                            print(f"   Duration: {entry['duration_ms']:.1f}ms")
                            if entry['success']:
                                print(f"   Version: {entry['old_hash'][:8]} → {entry['new_hash'][:8]}")
                            else:
                                print(f"   Error: {entry.get('error', 'Unknown')}")
                            if entry.get('warnings'):
                                print(f"   Warnings: {len(entry['warnings'])}")
                            print()
                
                except Exception as e:
                    print(f"\n❌ Audit error: {e}")
                continue

            elif cmd.startswith('/set-policy'):
                parts = cmd.split()
                if len(parts) < 3:
                    print("\nUsage: /set-policy <key> <value>")
                    print("Keys: auto_approve [true/false], slow_ms, min_gain_pct, risk_threshold")
                    continue
                key = parts[1].strip()
                val = parts[2].strip()
                try:
                    ApprovalPolicy.save_key(sess.ke.conn, key if key != 'auto-approve' else 'auto_approve', val)
                    print(f"\n✅ Policy updated: {key}={val}")
                except Exception as e:
                    print(f"\n❌ Failed to update policy: {e}")
                continue

            elif cmd.startswith('/improve'):
                print("\n🛠️  Running improvement loop (recall performance)...")
                try:
                    res = sess.improvement.run_once()
                    print(f"Baseline: {res['baseline_ms']:.1f} ms")
                    if res.get('patch_created'):
                        print(f"Proposed patch: {res['patch_id']}")
                        if res.get('applied'):
                            print("✅ Applied automatically per policy")
                        else:
                            print("Pending approval; use /review-patches to approve/apply")
                    else:
                        print(res.get('message', 'No changes required.'))
                except Exception as e:
                    print(f"\n❌ Improvement error: {e}")
                continue

            elif cmd.startswith('/review-patches'):
                patches = sess.improve_db.list_patches(limit=20)
                if not patches:
                    print("\n📝 No patches found.")
                    continue
                print("\n📝 Improvement Patches (latest)")
                print("="*70)
                for p in patches:
                    print(f"{p['id']} | {p['status']} | {p['type']} | gain≈{p.get('estimated_gain_ms',0):.1f}ms | risk={p.get('risk_score',0):.2f}")
                    print(f"   {p.get('description','')}")
                choice = input("\nAction: [approve <id> | apply <id> | skip]: ").strip()
                if choice.startswith('approve'):
                    _, pid = choice.split(maxsplit=1)
                    try:
                        sess.improve_db.set_status(pid, 'approved', reviewer='owner')
                        print("✅ Approved.")
                    except Exception as e:
                        print(f"❌ {e}")
                elif choice.startswith('apply'):
                    _, pid = choice.split(maxsplit=1)
                    try:
                        res = sess.improvement.apply_patch(pid)
                        if res.get('success'):
                            print("✅ Applied.")
                        else:
                            print(f"❌ {res.get('error')}")
                    except Exception as e:
                        print(f"❌ {e}")
                continue
            
            # Phase 28: MetaArchitect Commands
            elif cmd.startswith('/propose-architecture'):
                parts = cmd.split()
                if len(parts) < 2:
                    print("\nUsage: /propose-architecture <module> [type]")
                    print("Types: microservice, abstraction, pattern, auto (default)")
                    modules = sess.architect.list_analyzable_modules()
                    print(f"\nAvailable modules: {', '.join(modules[:10])}...")
                    continue
                
                target_module = parts[1].strip()
                refactor_type = parts[2].strip() if len(parts) > 2 else 'auto'
                
                print(f"\n🏗️  Analyzing {target_module} for architectural improvements...")
                print(f"   Type: {refactor_type}\n")
                
                try:
                    # Analyze and propose
                    proposal = sess.architect.propose_refactor(target_module, refactor_type)
                    
                    if not proposal.get('success'):
                        print(f"❌ {proposal.get('error', 'Unknown error')}")
                        continue
                    
                    # Store in DB
                    proposal_id = sess.arch_db.create_proposal(proposal)
                    
                    print(f"✅ Proposal created: {proposal_id}")
                    print(f"\n📄 {proposal.get('title', 'Architectural Refactor')}")
                    print("="*70)
                    print(f"\nRationale:\n{proposal.get('rationale', 'N/A')[:300]}...")
                    
                    design = proposal.get('proposed_design', {})
                    if design.get('approach'):
                        print(f"\nApproach: {design['approach']}")
                    if design.get('components'):
                        print(f"\nNew Components: {', '.join(design['components'][:5])}")
                    if design.get('benefits'):
                        print(f"\nBenefits:")
                        for benefit in design['benefits'][:3]:
                            print(f"  - {benefit}")
                    if design.get('risks'):
                        print(f"\nRisks:")
                        for risk in design['risks'][:3]:
                            print(f"  - {risk}")
                    
                    print(f"\nRisk Score: {proposal.get('risk_score', 0):.2f}")
                    print(f"Complexity: {proposal.get('complexity_score', 0):.2f}")
                    print(f"Effort: ~{proposal.get('estimated_effort_hours', 0):.1f} hours")
                    
                    print(f"\n🛠️  Next: /simulate-arch {proposal_id}")
                    
                    write_audit_log(sess.ke.conn, actor='owner', action='propose_architecture',
                                  target=proposal_id, details={'module': target_module, 'type': refactor_type})
                    
                except Exception as e:
                    print(f"\n❌ Proposal error: {e}")
                    logger.error("Architecture proposal failed", exc_info=True)
                continue
            
            elif cmd.startswith('/simulate-arch'):
                parts = cmd.split()
                if len(parts) < 2:
                    print("\nUsage: /simulate-arch <proposal_id>")
                    continue
                
                proposal_id = parts[1].strip()
                
                proposal = sess.arch_db.get_proposal(proposal_id)
                if not proposal:
                    print(f"\n❌ Proposal not found: {proposal_id}")
                    continue
                
                print(f"\n🧪 Simulating architectural refactor in sandbox...")
                print(f"   Proposal: {proposal.get('title', proposal_id)}")
                print(f"   This may take 30-60 seconds...\n")
                
                try:
                    sim_results = sess.sandbox.simulate_refactor(
                        proposal_id,
                        proposal.get('proposed_design', {})
                    )
                    
                    # Update DB with simulation results
                    sess.arch_db.update_simulation(proposal_id, sim_results)
                    
                    print(f"\n📊 Simulation Results")
                    print("="*70)
                    
                    if sim_results.get('success'):
                        print("✅ Simulation passed!")
                    else:
                        print(f"❌ Simulation failed: {sim_results.get('error', 'Unknown')}")
                    
                    print(f"\nTests: {sim_results.get('tests_passed', 0)} passed, {sim_results.get('tests_failed', 0)} failed")
                    
                    metrics_before = sim_results.get('metrics_before', {})
                    metrics_after = sim_results.get('metrics_after', {})
                    improvement = sim_results.get('improvement', {})
                    
                    print(f"\nArchitecture Metrics:")
                    print(f"  Modules: {metrics_before.get('total_modules', 0)} → {metrics_after.get('total_modules', 0)}")
                    print(f"  Avg Coupling: {metrics_before.get('avg_coupling', 0):.1f} → {metrics_after.get('avg_coupling', 0):.1f}")
                    print(f"  Avg Complexity: {metrics_before.get('avg_complexity', 0):.1f} → {metrics_after.get('avg_complexity', 0):.1f}")
                    
                    print(f"\nImprovement Score: {improvement.get('overall_score', 0):.1f}/100")
                    
                    if improvement.get('coupling_improved'):
                        print("  ✅ Coupling reduced")
                    if improvement.get('complexity_improved'):
                        print("  ✅ Complexity reduced")
                    if improvement.get('modularity_improved'):
                        print("  ✅ Modularity improved")
                    
                    if sim_results.get('success'):
                        print(f"\n🚀 Ready for approval: /promote-arch {proposal_id}")
                    
                    write_audit_log(sess.ke.conn, actor='owner', action='simulate_architecture',
                                  target=proposal_id, details={'success': sim_results.get('success')})
                    
                except Exception as e:
                    print(f"\n❌ Simulation error: {e}")
                    logger.error("Architecture simulation failed", exc_info=True)
                continue
            
            elif cmd.startswith('/promote-arch'):
                parts = cmd.split()
                if len(parts) < 2:
                    print("\nUsage: /promote-arch <proposal_id>")
                    continue
                
                proposal_id = parts[1].strip()
                
                proposal = sess.arch_db.get_proposal(proposal_id)
                if not proposal:
                    print(f"\n❌ Proposal not found: {proposal_id}")
                    continue
                
                if proposal['status'] != 'simulated':
                    print(f"\n⚠️  Proposal not simulated yet. Run /simulate-arch first.")
                    continue
                
                sim_results = proposal.get('simulation_results', {})
                if not sim_results.get('success'):
                    print(f"\n⚠️  Simulation did not pass. Are you sure you want to promote?")
                    confirm = input("   Type 'yes' to promote anyway: ").strip().lower()
                    if confirm != 'yes':
                        print("   Cancelled.")
                        continue
                
                print(f"\n🚀 Promoting Architecture\n" + "="*70)
                print(f"Proposal: {proposal.get('title')}")
                print(f"Type: {proposal.get('type')}")
                print(f"Scope: {proposal.get('scope')}")
                print(f"\n⚠️  WARNING: This marks the architecture as approved for implementation.")
                print("   Actual code changes would need to be applied manually or via code generation.\n")
                
                confirm = input("Promote to production? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("   Cancelled.")
                    continue
                
                try:
                    sess.arch_db.set_status(proposal_id, 'promoted', reviewer='owner')
                    print(f"\n✅ Architecture promoted: {proposal_id}")
                    print(f"   Status: PROMOTED")
                    print(f"\n📝 Next steps:")
                    print(f"   1. Use /propose-code to generate implementation")
                    print(f"   2. Test with /sandbox-code")
                    print(f"   3. Apply with /apply-code (hot-reload)")
                    
                    write_audit_log(sess.ke.conn, actor='owner', action='promote_architecture',
                                  target=proposal_id, details={'title': proposal.get('title')})
                    
                except Exception as e:
                    print(f"\n❌ Promotion error: {e}")
                continue
            
            elif cmd.startswith('/list-architectures'):
                parts = cmd.split()
                status_filter = parts[1].strip() if len(parts) > 1 else None
                
                proposals = sess.arch_db.list_proposals(status=status_filter, limit=20)
                
                if not proposals:
                    print("\n🏗️  No architecture proposals found.")
                    continue
                
                print(f"\n🏗️  Architecture Proposals ({len(proposals)})")
                print("="*70)
                
                for p in proposals:
                    status_icon = {
                        'pending': '⏳',
                        'simulated': '🧪',
                        'approved': '✅',
                        'promoted': '🚀',
                        'rejected': '❌'
                    }.get(p['status'], '📝')
                    
                    print(f"{status_icon} {p['id']}")
                    print(f"   {p.get('title', 'Untitled')} | {p.get('type')} | {p.get('scope')}")
                    print(f"   Risk: {p.get('risk_score', 0):.2f} | Effort: {p.get('estimated_effort_hours', 0):.1f}h")
                    print(f"   Created: {p.get('created_at', '')[:19]}")
                    print()
                
                continue

            elif cmd.startswith('/autonomy'):
                parts = cmd.split()
                if len(parts) >= 3 and parts[1] == 'set':
                    try:
                        tier = int(parts[2])
                        reason = ' '.join(parts[3:]).strip() if len(parts) > 3 else 'Owner adjustment'
                        if sess.safety_gate.set_autonomy_tier(tier, 'owner', reason):
                            print(f"\n🎯 Autonomy tier set to {tier} ({sess.safety_gate.AUTONOMY_TIERS[tier]})")
                            write_audit_log(sess.ke.conn, actor='owner', action='set_autonomy', target=str(tier), details={'reason': reason})
                        else:
                            print("\n❌ Invalid tier (must be 0-4)")
                    except ValueError:
                        print("\nUsage: /autonomy set <0-4> [reason]")
                else:
                    tier = sess.safety_gate._current_tier
                    tier_name = sess.safety_gate.AUTONOMY_TIERS[tier]
                    print(f"\n🎯 Current Autonomy: Tier {tier} ({tier_name})")
                    print("\nTier Levels:")
                    for t, name in sess.safety_gate.AUTONOMY_TIERS.items():
                        marker = '→' if t == tier else ' '
                        print(f"{marker} {t}: {name}")
                    print("\nUsage: /autonomy set <0-4> [reason]")
                continue
            
            elif cmd in ['/audit-soul']:
                audit = sess.sentience.audit_soul()
                print("\n🧠 Sentience Audit Report")
                print("=" * 70)
                print(f"\nComplexity Metrics:")
                print(f"   Average (7d): {audit['avg_complexity_7d']:.1%}")
                print(f"   Total events: {audit['total_events']}")
                print(f"   Triggered reviews: {audit['triggered_reviews']}")
                
                if audit['autonomy_trajectory']:
                    print(f"\nAutonomy Trajectory:")
                    for entry in audit['autonomy_trajectory'][-5:]:
                        print(f"   {entry['timestamp'][:19]}: Level {entry['autonomy_level']:.2f}")
                
                if audit['all_pauses']:
                    print(f"\nEvolution Pauses:")
                    for pause in audit['all_pauses'][:5]:
                        status = '✅ Resolved' if pause['resolved'] else '⏸️  Active'
                        print(f"   {status} | {pause['reason']} (by {pause['triggered_by']})")
                
                print(f"\nCurrent Thresholds:")
                for metric, threshold in audit['current_thresholds'].items():
                    print(f"   {metric}: {threshold}")
                
                print("\n" + "=" * 70)
                continue
            
            elif cmd.startswith('/pause-evolution'):
                parts = cmd.split()
                reason = ' '.join(parts[1:]).strip() if len(parts) > 1 else 'Manual pause by owner'
                
                # Check if already paused
                if sess.sentience.is_paused():
                    print(f"\n⏸️  Evolution is already paused.")
                    print(f"   Reason: {sess.sentience.get_pause_reason()}")
                else:
                    # Record current metrics
                    metrics = {
                        'recursive_depth': 0,  # Would be tracked during session
                        'autonomy_level': sess.safety_gate._current_tier / 4.0,
                        'manual_pause': True
                    }
                    pause_id = sess.sentience.pause_evolution(reason, 'owner', metrics)
                    print(f"\n⏸️  Evolution paused (ID: {pause_id[:8]}...)")
                    print(f"   Reason: {reason}")
                    print(f"\n   Use /resume-evolution {pause_id[:8]} to resume.")
                continue
            
            elif cmd.startswith('/resume-evolution'):
                parts = cmd.split()
                if len(parts) < 2:
                    print("\nUsage: /resume-evolution <pause_id> [resolution_notes]")
                    continue
                
                pause_id = parts[1]
                notes = ' '.join(parts[2:]).strip() if len(parts) > 2 else 'Owner approval to resume'
                
                # Find full pause ID
                cur = sess.ke.conn.cursor()
                cur.execute("SELECT id FROM evolution_pauses WHERE id LIKE ? AND resolved = 0", (pause_id + '%',))
                row = cur.fetchone()
                
                if not row:
                    print(f"\n❌ No active pause found matching '{pause_id}'")
                else:
                    full_id = row[0]
                    if sess.sentience.resolve_pause(full_id, notes):
                        print(f"\n✅ Evolution resumed (pause {pause_id} resolved)")
                        print(f"   Resolution: {notes}")
                    else:
                        print(f"\n❌ Failed to resolve pause")
                continue

            elif cmd.startswith('/privacy'):
                parts = cmd.split()
                if len(parts) == 2 and parts[1] in ['on','off']:
                    set_preference(sess.ke.conn, 'privacy_mode', 'true' if parts[1]=='on' else 'false')
                    print(f"\n🔒 Privacy mode set to {parts[1]}")
                else:
                    print("Usage: /privacy [on|off]")
                continue

            elif cmd in ['/briefing']:
                from saraphina.memory_manager import MemoryManager
                mm = MemoryManager(sess.ke.conn)
                recent = mm.list_recent_episodic(10)
                cur = sess.ke.conn.cursor()
                cur.execute("SELECT text, due_ts FROM reminders WHERE status='pending' ORDER BY due_ts ASC LIMIT 5")
                due = cur.fetchall()
                print("\n📰 Daily Briefing:")
                if recent:
                    print(" - Recent topics captured:")
                    for r in recent[:5]:
                        print(f"   • {r['text'][:80]}...")
                if due:
                    print(" - Upcoming reminders:")
                    for d in due:
                        print(f"   • {d['text']} @ {d['due_ts']}")
                continue

            elif cmd.startswith('/listen'):
                parts = cmd.split()
                mode = parts[1] if len(parts) > 1 else 'once'
                if not sess.stt.available:
                    print("\n⚠️  STT unavailable. Install: pip install SpeechRecognition pyaudio openai-whisper faster-whisper webrtcvad")
                    continue
                if mode == 'once':
                    print("\n🎙️  Listening... (speak now)")
                    engine = 'faster'  # prefer faster-whisper if present
                    text = sess.stt.transcribe_once(engine=engine)
                    if text:
                        print(f"You (voice): {text}")
                        response = process_query_with_ultra(sess, text)
                        print(f"\n🤖 Saraphina: {response}")
                        # Speak with emotion and without markdown
                        if sess.voice_enabled and VOICE_AVAILABLE:
                            speak_with_emotion(response)
                    else:
                        print("\n(no speech detected)")
                else:
                    print("Usage: /listen once")
                continue

            elif cmd.startswith('/dashboard'):
                parts = cmd.split()
                sub = parts[1] if len(parts) > 1 else ''
                if sub == 'open':
                    try:
                        webbrowser.open_new_tab(str(Path('dashboard/index.html').resolve()))
                        print("\n🧭 Dashboard opened in your browser.")
                    except Exception as e:
                        print(f"\n❌ Could not open dashboard: {e}")
                else:
                    print("Usage: /dashboard open")
                continue

            elif cmd.startswith('/healthwatch'):
                parts = cmd.split()
                state = parts[1] if len(parts) > 1 else ''
                if state in ['on','off']:
                    set_preference(sess.ke.conn, 'health_watch', 'true' if state=='on' else 'false')
                    print(f"\nHealth watch set to {state}")
                else:
                    print("Usage: /healthwatch [on|off]")
                continue

            elif cmd in ['/health']:
                from saraphina.monitoring import health_pulse
                hp = health_pulse(sess.ke.conn)
                print("\n🩺 Health:")
                print(json.dumps(hp, indent=2))
                continue
            
            elif cmd in ['/audit-trust']:
                print("\n🛡️ Trust Firewall Audit:\n")
                
                # Get statistics
                stats = sess.trust.get_statistics()
                print(f"Total evaluations: {stats['total']}")
                print(f"  ✅ Allowed: {stats['allowed']} ({stats['block_rate']*100:.1f}% clean)")
                print(f"  ⚠️  Review: {stats['review']} ({stats['review_rate']*100:.1f}%)")
                print(f"  ❌ Blocked: {stats['blocked']} ({stats['block_rate']*100:.1f}%)\n")
                
                # Recent audit logs
                try:
                    cur = sess.ke.conn.cursor()
                    cur.execute(
                        """SELECT timestamp, action, details FROM audit_logs 
                           WHERE actor='trust_firewall' 
                           ORDER BY timestamp DESC LIMIT 10"""
                    )
                    logs = cur.fetchall()
                    
                    if logs:
                        print("Recent trust events:")
                        for log in logs:
                            ts = log['timestamp'][:19]  # Trim microseconds
                            action = log['action'].replace('evaluate_', '')
                            details = json.loads(log['details']) if log['details'] else {}
                            level = details.get('level', 'unknown')
                            score = details.get('score', 0)
                            reasons = details.get('reasons', [])
                            
                            icon = '✅' if action == 'allow' else '⚠️' if action == 'review' else '❌'
                            print(f"  {icon} [{ts}] {action.upper()} - {level} risk ({score:.2f})")
                            if reasons:
                                print(f"      Reasons: {', '.join(reasons[:3])}")
                except Exception as e:
                    print(f"Could not retrieve audit logs: {e}")
                continue
            
            elif cmd in ['/verify-integrity']:
                print("\n🔍 Verifying System Integrity...\n")
                
                # Verify multiple components
                components = ['preferences', 'policies', 'audit_trail']
                
                for comp in components:
                    result = sess.trust.verify_integrity(comp)
                    status_icon = '✅' if result['status'] == 'clean' else '⚠️'
                    print(f"{status_icon} {comp.upper()}: {result['status']}")
                    
                    if result['issues']:
                        print(f"   Issues detected ({result['issue_count']}):")
                        for issue in result['issues']:
                            print(f"     - {issue}")
                    print()
                
                # Check for suspicious patterns in recent commands
                try:
                    cur = sess.ke.conn.cursor()
                    cur.execute(
                        """SELECT COUNT(*) FROM audit_logs 
                           WHERE action IN ('evaluate_block', 'evaluate_review') 
                           AND timestamp > datetime('now', '-24 hours')"""
                    )
                    suspicious_24h = cur.fetchone()[0]
                    
                    if suspicious_24h > 10:
                        print(f"⚠️  Warning: {suspicious_24h} suspicious inputs in last 24 hours")
                    else:
                        print(f"✅ Low suspicious activity: {suspicious_24h} flagged inputs in 24h")
                except Exception:
                    pass
                
                print("\n✅ Integrity verification complete")
                continue

            elif cmd.startswith('/wake'):
                parts = cmd.split()
                if len(parts) == 3 and parts[1] == 'set':
                    new = parts[2]
                    set_preference(sess.ke.conn, 'wake_word', new)
                    print(f"\n✅ Wake word set to '{new}'")
                else:
                    print("Usage: /wake set <word>")
                continue

            elif cmd.startswith('/name'):
                parts = cmd.split()
                if len(parts) >= 3 and parts[1] == 'set':
                    new = ' '.join(parts[2:])
                    set_preference(sess.ke.conn, 'owner_name', new)
                    print(f"\n✅ Nice to meet you, {new}!")
                else:
                    print("Usage: /name set <Your Name>")
                continue

            # Otherwise, handle as natural conversation with Ultra augmentation
            response = process_query_with_ultra(sess, user_input)
            
            # Output via UI if available, otherwise print
            if ui:
                owner_name = get_preference(sess.ke.conn, 'owner_name') or 'You'
                ui.add_message(owner_name, user_input)
                ui.add_message('Saraphina', response)
                if ui_ctx:
                    ui_ctx.update()
            else:
                print(f"\n🤖 Saraphina: {response}")
            
            # Speak with emotion and without markdown
            if sess.voice_enabled and VOICE_AVAILABLE:
                if ui:
                    ui.set_speaking(True)
                speak_with_emotion(response)
                if ui:
                    ui.set_speaking(False)
                    if ui_ctx:
                        ui_ctx.update()

            # Milestone feedback
            if sess.ai.total_conversations % 10 == 0 and sess.ai.total_conversations > 0:
                print(f"\n💫 Milestone! {sess.ai.total_conversations} conversations completed")
                print(f"   Current: Level {sess.ai.intelligence_level} | {sess.ai.experience_points} XP")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Saving your progress...")
            sess.ai._save_state()
            print(f"\n✅ Progress saved. Level {sess.ai.intelligence_level} with {sess.ai.experience_points} XP")
            if sess.voice_enabled and VOICE_AVAILABLE:
                try:
                    speak_text("Goodbye!")
                except Exception:
                    pass
            # Stop API server if running
            try:
                if sess.api_proc and sess.api_proc.poll() is None:
                    sess.api_proc.terminate()
            except Exception:
                pass
            # Stop background STT and cleanup
            try:
                sess.stt.stop_background()
            except Exception:
                pass
            try:
                if VOICE_AVAILABLE:
                    get_voice().cleanup()
            except Exception:
                pass
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error("Processing error", exc_info=True)
            print("Don't worry, I'm learning from this experience!")

    return 0


if __name__ == '__main__':
    sys.exit(main())
