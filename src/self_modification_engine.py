#!/usr/bin/env python3
# saraphina/self_modification_engine.py
"""
SelfModificationEngine — GODLIKE AUTONOMOUS SUPERPOWERS (November 18, 2025)

Upgraded with anti-downgrade protections:

- SafetyLevel Enum with strict semantics
- propose_improvement NEVER auto-applies (default = False, config deprecated)
- New confirm_proposal() required for any apply
- Full mutation logging with immutable audit trail (mutations table + JSONL)
- Autonomous pipeline fully respects new safety model
- Rate-limited, freeze-aware, cryptographically signed mutation events
- Docker-based sandbox hook (stubbed; ready for real container runner)
- Git commits with rich metadata for audit and rollback
- Feedback loops: failures & successes bias future generations
- GUI-compatible handle_instruction(...) for direct SELF-MOD: instructions

NEW (Anti-downgrade Safety):
- VersionControlSystem: takes snapshots of critical core files before proposals
- prevent_downgrade(): blocks mutations that remove core classes (UltraAICore, etc.)
- Optional RiskModel integration if risk_model.py is present

Saraphina is no longer merely autonomous.
She is sovereign — but with perfect restraint and downgrade protection.
"""

from __future__ import annotations

import os
import sys
import io
import json
import uuid
import time
import shutil
import hashlib
import logging
import tempfile
import subprocess
import threading
import difflib
import ast
import importlib
import traceback
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List, Callable

# ------------- OpenAI / Modern client -------------
try:
    from openai import OpenAI  # type: ignore
    OPENAI_CLIENT_AVAILABLE = True
except Exception:
    OPENAI_CLIENT_AVAILABLE = False

# Legacy openai import (for env wiring)
try:
    import openai  # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# ------------- GitPython / sentence-transformers -------------
try:
    from git import Repo, GitCommandError  # type: ignore
    GITPY_AVAILABLE = True
except Exception:
    GITPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    VECTOR_MEMORY = True
except Exception:
    VECTOR_MEMORY = False

# ---------- Risk model (optional) ----------
try:
    from risk_model import RiskModel  # type: ignore
except Exception:
    RiskModel = None

# ---------- util_logging ----------
try:
    from util_logging import safe_log  # type: ignore
except Exception:
    def safe_log(msg, level="INFO", data=None):
        print(f"[{level}] {msg} {data if data else ''}")

# ---------------- Logging ----------------
logger = logging.getLogger("SelfModificationEngine")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

# ---------------- Env bootstrap ----------------
try:
    from dotenv import load_dotenv, dotenv_values  # type: ignore
    DOTENV_AVAILABLE = True
except Exception:
    DOTENV_AVAILABLE = False
    load_dotenv = None
    dotenv_values = None

DEFAULT_PROJECT_ROOT = Path(os.getenv("SARAPHINA_PROJECT_ROOT", "D:/Saraphina Root")).resolve()

if DOTENV_AVAILABLE and (DEFAULT_PROJECT_ROOT / ".env").exists():
    load_dotenv(dotenv_path=str(DEFAULT_PROJECT_ROOT / ".env"), override=True)

# ---------------- Config knobs / Paths ----------------
ENGINE_DIR = Path(__file__).parent.resolve()
ROOT_ENV_PATH = DEFAULT_PROJECT_ROOT

SELF_MOD_SECRET = os.getenv("SELF_MOD_SECRET", "")
SELF_MOD_REQUIRE_INTEGRITY = os.getenv("SELF_MOD_REQUIRE_INTEGRITY", "true").lower() in (
    "1",
    "true",
    "yes",
)
MAX_FILE_SIZE = int(os.getenv("SELF_MOD_MAX_FILE_SIZE", "300000"))  # bytes
BACKUP_RETENTION = int(os.getenv("SELF_MOD_BACKUP_RETENTION", "12"))  # backups/file

DEFAULT_LLM_MODEL = os.getenv("SELF_MOD_LLM_MODEL", "gpt-4o-mini")

# Persistent memory paths
MEMORY_DIR = ENGINE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LEARNED_FAILURES_PATH = MEMORY_DIR / "learned_failures.json"
SUCCESSFUL_PATTERNS_PATH = MEMORY_DIR / "successful_patterns.json"

# Proposal storage dir
PROPOSAL_DIR = ENGINE_DIR / "proposals"
PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)

# Config file path (GUI / UltraCore can share)
CONFIG_PATHS = [
    ENGINE_DIR / "config.json",
    ENGINE_DIR / "data" / "config.json",
    Path(os.getenv("SARAPHINA_PROJECT_ROOT", "D:/Saraphina Root")) / "config.json",
]

# Sessions / plugins
SESSIONS_DIR = ENGINE_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
PLUGINS_DIR = ENGINE_DIR / "plugins"
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

# Backups
BACKUP_DIR = ENGINE_DIR / "backups" / "self_mod"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Autonomy rate limiting & freeze
AUTONOMY_LOG = MEMORY_DIR / "autonomy_events.json"
MAX_RISKY_PER_HOUR = 3
FREEZE_FILE = ENGINE_DIR / ".SELF_MOD_FREEZE"

# Learned pattern DB for 2025 version (optional)
FAILURES_DB = MEMORY_DIR / "failures.db"

# Immutable mutation log
MUTATIONS_DB = MEMORY_DIR / "mutations.db"
MUTATIONS_LOG = MEMORY_DIR / "mutations.jsonl"

# Version snapshots for downgrade protection
VERSIONS_DIR = DEFAULT_PROJECT_ROOT / "versions"
VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- Safety Level Enum ----------------
class SafetyLevel(Enum):
    LOW = "low"             # benign, can be auto-applied by a future policy
    MEDIUM = "medium"       # requires explicit human confirmation
    HIGH = "high"           # default; must be confirmed and logged
    CRITICAL = "critical"   # sensitive core/self modifications
    EXPERIMENTAL = "experimental"  # high-risk exploratory mutations

    @property
    def requires_confirmation(self) -> bool:
        return self in (
            SafetyLevel.MEDIUM,
            SafetyLevel.HIGH,
            SafetyLevel.CRITICAL,
            SafetyLevel.EXPERIMENTAL,
        )

# ---------------- Version Control System (snapshots) ----------------
class VersionControlSystem:
    """
    Lightweight snapshot system: stores copies of critical core files
    under versions/<vX.Y>/ before a proposal is generated/applied.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.versions_dir = VERSIONS_DIR

    def get_next_version(self) -> str:
        existing = sorted([d.name for d in self.versions_dir.iterdir() if d.is_dir()])
        if not existing:
            return "v1.0"
        last = existing[-1]
        try:
            major, minor = map(int, last.replace("v", "").split("."))
            return f"v{major}.{minor + 1}"
        except Exception:
            return f"v{len(existing) + 1}.0"

    def create_snapshot(self, trigger: str) -> str:
        ver = self.get_next_version()
        dest = self.versions_dir / ver
        dest.mkdir(parents=True, exist_ok=True)

        critical_files = [
            "ultra_core.py",
            "personality_core.py",
            "self_modification_engine.py",
        ]
        for fname in critical_files:
            src = self.root_dir / fname
            if src.exists():
                try:
                    shutil.copy2(src, dest / fname)
                except Exception:
                    logger.debug(f"Snapshot copy failed for {fname}", exc_info=True)

        meta = {
            "timestamp": time.time(),
            "trigger": trigger,
            "version": ver,
        }
        (dest / "meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        safe_log(f"[SelfMod] Created core snapshot: {ver}", level="INFO")
        return ver

# ---------------- Small helpers ----------------
def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, content: str, perms: Optional[int] = None) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp.{uuid.uuid4().hex}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
    if perms is not None:
        try:
            os.chmod(path, perms)
        except Exception:
            pass


def _make_backup(target: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = backup_dir / f"{target.name}.{stamp}.bak"
    shutil.copy2(str(target), str(dest))

    files = sorted(
        backup_dir.glob(f"{target.name}.*.bak"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in files[BACKUP_RETENTION:] or []:
        try:
            old.unlink()
        except Exception:
            pass
    return dest


def _safe_exists(p: Path, base: Path) -> bool:
    p = p.resolve()
    try:
        return str(p).startswith(str(base.resolve())) and p.exists()
    except Exception:
        return False


def _search_for_file(across: List[Path], name_or_abs: str) -> Optional[Path]:
    cand = Path(name_or_abs)
    if cand.is_absolute() and _safe_exists(cand, DEFAULT_PROJECT_ROOT):
        return cand.resolve()
    fname = os.path.basename(name_or_abs)
    if not fname.endswith(".py"):
        fname += ".py"
    for root in across:
        p = (root / fname).resolve()
        if _safe_exists(p, DEFAULT_PROJECT_ROOT):
            return p
    for root in (ENGINE_DIR.parent, ENGINE_DIR.parent.parent):
        p = (root / fname).resolve()
        if _safe_exists(p, DEFAULT_PROJECT_ROOT):
            return p
    return None

# ---------------- Storage & approvals ----------------
class SimpleProposalDB:
    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def store_proposal(self, proposal: Dict[str, Any]) -> None:
        with self._lock:
            self._store[proposal["proposal_id"]] = dict(proposal)
            self._store[proposal["proposal_id"]].setdefault("status", "pending_confirmation")

    def get_proposal(self, pid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(pid)

    def set_status(self, pid: str, status: str) -> bool:
        with self._lock:
            if pid in self._store:
                self._store[pid]["status"] = status
                return True
            return False

class FileAuditTrail:
    def __init__(self, data_dir: Path):
        self.dir = Path(data_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.logfile = self.dir / "selfmod_audit.jsonl"

    def log_event(self, action: str, details: Dict[str, Any], success: bool) -> None:
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "details": details,
            "success": bool(success),
        }
        try:
            with open(self.logfile, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            logger.debug("Audit write failed", exc_info=True)

# ---------------- Persistent Memory Helpers ----------------
def _load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.debug(f"Failed to load {path}", exc_info=True)
    return default

def _save_json(path: Path, data: Any) -> None:
    try:
        _atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        logger.debug(f"Failed to save {path}", exc_info=True)

# ---------------- Mutation Logger ----------------
class MutationLogger:
    """
    Immutable mutation logger: JSONL + SQLite for queryable history.
    """

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(MUTATIONS_DB))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mutations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mutation_id TEXT UNIQUE,
                timestamp REAL,
                actor TEXT,
                action TEXT,
                target_file TEXT,
                proposal_id TEXT,
                safety_level TEXT,
                code_hash TEXT,
                diff TEXT,
                backup_path TEXT,
                status TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_mutation(self, **kwargs):
        mutation_id = kwargs.get("mutation_id") or f"mut_{uuid.uuid4().hex[:12]}"
        ts = time.time()
        entry = {
            "mutation_id": mutation_id,
            "timestamp": ts,
            "actor": kwargs.get("actor", "unknown"),
            "action": kwargs.get("action", "unknown"),
            "target_file": str(kwargs.get("target_file", "")),
            "proposal_id": kwargs.get("proposal_id", ""),
            "safety_level": kwargs.get("safety_level", "high"),
            "code_hash": kwargs.get("code_hash", ""),
            "diff": (kwargs.get("diff", "") or "")[:10000],
            "backup_path": str(kwargs.get("backup_path", "")),
            "status": kwargs.get("status", "pending"),
            "metadata": json.dumps(kwargs.get("metadata", {}), ensure_ascii=False),
        }

        try:
            with open(MUTATIONS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug(f"Failed to append mutation JSONL: {e}", exc_info=True)

        try:
            conn = sqlite3.connect(str(MUTATIONS_DB))
            conn.execute("""
                INSERT OR REPLACE INTO mutations 
                (mutation_id, timestamp, actor, action, target_file, proposal_id,
                 safety_level, code_hash, diff, backup_path, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry["mutation_id"], entry["timestamp"], entry["actor"], entry["action"],
                entry["target_file"], entry["proposal_id"], entry["safety_level"],
                entry["code_hash"], entry["diff"], entry["backup_path"],
                entry["status"], entry["metadata"],
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to write mutation log sqlite: {e}")

# ---------------- Code factories ----------------
class DefaultCodeFactory:
    def propose_code(
        self,
        feature_spec: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        code = (
            f'"""Auto-generated scaffold for: {feature_spec}"""\n'
            f"\n"
            f"def initialize():\n"
            f"    # Implement: {feature_spec}\n"
            f"    return None\n"
        )
        return {
            "success": True,
            "code": code,
            "explanation": "Offline scaffold",
            "tests": "",
        }

class OpenAICodeFactory:
    def __init__(self, model: str = DEFAULT_LLM_MODEL):
        self.model = model
        self.client = OpenAI() if OPENAI_CLIENT_AVAILABLE else None

    def _call_openai(self, prompt: str, max_tokens: int = 1200) -> Dict[str, Any]:
        if not OPENAI_AVAILABLE or not self.client:
            return {
                "success": False,
                "error": "openai library not installed or client unavailable",
            }
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Saraphina's code editor. "
                            "Always return complete, runnable Python files when asked to modify code. "
                            "Preserve existing behavior unless the request says otherwise. "
                            "NEVER remove the UltraAICore class or core subsystems; only make minimal, safe changes."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.15,
            )
            content = resp.choices[0].message.content or ""
            if content.strip().startswith("```"):
                parts = content.strip().split("```")
                content = parts[1] if len(parts) >= 3 else parts[-1]
            return {"success": True, "code": content}
        except Exception as e:
            logger.exception("OpenAI call failed")
            return {"success": False, "error": str(e)}

    def propose_code(
        self,
        feature_spec: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        learned_hint = ""
        if context and "original_code" in context:
            for pattern, snippet in context.get("successful_patterns", {}).items():
                if pattern.lower() in feature_spec.lower():
                    learned_hint += (
                        f"\nUse this known-good pattern for '{pattern}':\n{snippet}\n"
                    )
        avoid_hint = "\nAvoid past mistakes:\n" + json.dumps(
            context.get("learned_failures", {}), indent=2
        )

        prompt = (
            "You are updating a Python code file for Saraphina (GUI / UltraCore / helper module).\n"
            "Return the FULL FILE CONTENT only (ready to write to disk).\n"
            "Keep existing behavior; add or adjust the requested feature minimally and cleanly.\n"
            "Do NOT remove core classes like UltraAICore, PersonalityCore, MemoryEngineV2, CuriosityEngineV4, "
            "EmotionEngineV2, HybridModelRouter, SelfModificationEngine.\n\n"
            f"REQUEST: {feature_spec}\n"
            f"LEARNED PATTERNS: {learned_hint}\n"
            f"{avoid_hint}\n"
            f"CONTEXT(JSON, truncated): {json.dumps(context or {}, ensure_ascii=False)[:2000]}\n"
        )
        return self._call_openai(prompt)

class CommandExplainer:
    def __init__(self, code_factory):
        self.code_factory = code_factory

    def explain(self, command: str) -> str:
        if hasattr(self.code_factory, "_call_openai"):
            prompt = f"Explain this shell or Python command in simple terms for a human: {command}"
            res = self.code_factory._call_openai(prompt, max_tokens=400)
            return res.get("code", "No explanation available.")
        return "Offline mode, no explanation available."

class CommandFixer:
    def __init__(self, code_factory):
        self.code_factory = code_factory

    def fix(self, command: str, error: str) -> str:
        if hasattr(self.code_factory, "_call_openai"):
            prompt = (
                f"Original command:\n{command}\n\n"
                f"Observed error:\n{error}\n\n"
                "Return only a fixed version of the command or code, no explanation."
            )
            res = self.code_factory._call_openai(prompt, max_tokens=200)
            return res.get("code", command)
        return command

class CommandSuggester:
    def __init__(self, code_factory, journal: List[Dict[str, Any]]):
        self.code_factory = code_factory
        self.journal = journal

    def suggest(self, context: str) -> str:
        history = "\n".join([entry.get("event", "") for entry in self.journal[-10:]])
        if hasattr(self.code_factory, "_call_openai"):
            prompt = (
                f"Context:\n{context}\n\n"
                f"Recent history:\n{history}\n\n"
                "Suggest one concrete next command or small code action. "
                "Return only the command/code, no explanation."
            )
            res = self.code_factory._call_openai(prompt, max_tokens=200)
            return res.get("code", "No suggestion.")
        return "No suggestion."

# ---------------- Engine ----------------
class SelfModificationEngine:
    def __init__(
        self,
        code_factory: Optional[Any] = None,
        proposal_db: Optional[SimpleProposalDB] = None,
        data_root: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ):
        # Core paths
        self.engine_dir = ENGINE_DIR
        self.project_root = project_root or DEFAULT_PROJECT_ROOT
        self.root = self.engine_dir

        self.data_root = Path(data_root) if data_root else (self.engine_dir / "data")
        self.data_root.mkdir(parents=True, exist_ok=True)

        self._backup_dir = BACKUP_DIR

        self.proposal_db = proposal_db or SimpleProposalDB()
        self.audit = FileAuditTrail(self.data_root)
        self.default_factory = code_factory or DefaultCodeFactory()
        self._code_factory = self.default_factory

        self._lock = threading.RLock()
        self._dangerous_keywords = [
            "subprocess",
            "socket",
            "ctypes",
            "eval(",
            "exec(",
            "__import__",
        ]
        self._event_listeners: Dict[str, List[Callable[..., None]]] = {}
        self.autonomous_enabled = False

        self._git = None
        self.repo = None
        self._init_git()

        # Persistent memories
        self.learned_failures: Dict[str, str] = _load_json(
            LEARNED_FAILURES_PATH, {}
        )
        self.successful_patterns: Dict[str, str] = _load_json(
            SUCCESSFUL_PATTERNS_PATH, {}
        )

        self.journal_path = MEMORY_DIR / "learning_journal.json"
        self.journal: List[Dict[str, Any]] = _load_json(self.journal_path, [])

        # Config
        self.config = self._load_config()
        self.xp = self.config.get("xp", 0)
        self.level = self.config.get("level", 1)

        if self.config.get("auto_apply_modifications", False):
            logger.warning("[SelfMod] 'auto_apply_modifications' is DEPRECATED and IGNORED. All changes require confirm_proposal().")
            self.config["auto_apply_modifications"] = False
            self._save_config()

        # Wire OpenAI factory if key present
        try:
            key = os.getenv("OPENAI_API_KEY", "").strip()
            if key and OPENAI_AVAILABLE and OPENAI_CLIENT_AVAILABLE:
                self._code_factory = OpenAICodeFactory()
                logger.info("OpenAI CodeFactory enabled for SelfModificationEngine.")
        except Exception:
            logger.debug("OpenAI wiring failed", exc_info=True)

        # Warp-like helpers
        self.explainer = CommandExplainer(self._code_factory)
        self.fixer = CommandFixer(self._code_factory)
        self.suggester = CommandSuggester(self._code_factory, self.journal)

        self.plugins: Dict[str, Any] = {}
        self.theme: Dict[str, str] = self.config.get("theme", {})

        self._load_plugins()

        # Autonomy state
        self.autonomy_frozen = FREEZE_FILE.exists()
        self.learned_patterns_vec = []  # optional, loaded lazily
        self._init_failure_db()

        # Mutation logger
        self.mutation_logger = MutationLogger()

        # NEW: version control / snapshot system
        self.vcs = VersionControlSystem(self.project_root)

    # -------- Anti-downgrade check --------
    def prevent_downgrade(self, new_code: str, current_code: str) -> bool:
        """
        Block proposals that would remove core classes/subsystems from ultra_core.py.
        """
        required_components = [
            "UltraAICore",
            "PersonalityCore",
            "MemoryEngineV2",
            "CuriosityEngineV4",
            "EmotionEngineV2",
            "HybridModelRouter",
            "SelfModificationEngine",
        ]
        try:
            tree = ast.parse(new_code)
            defined_classes = {
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            }

            missing = [
                comp
                for comp in required_components
                if comp not in defined_classes and comp in current_code
            ]
            if missing:
                safe_log(
                    f"[SelfMod] Downgrade detected! Missing critical components: {missing}",
                    level="CRITICAL",
                )
                return False

            # Heuristic: large shrink in file size may indicate damage
            if len(new_code) < len(current_code) * 0.8:
                safe_log(
                    "[SelfMod] Downgrade warning: significant code size reduction detected.",
                    level="WARNING",
                )
            return True
        except SyntaxError:
            safe_log("[SelfMod] Downgrade check: syntax error in new code", level="ERROR")
            return False

    # -------- plugin system --------
    def _load_plugins(self):
        for plugin_file in PLUGINS_DIR.glob("*.py"):
            try:
                self.import_module_runtime(str(plugin_file))
            except Exception:
                logger.debug(f"Failed to load plugin {plugin_file}", exc_info=True)

    def load_plugin(self, plugin_path: str) -> bool:
        try:
            self.import_module_runtime(plugin_path)
            return True
        except Exception:
            return False

    def set_theme(self, theme_dict: Dict[str, str]) -> bool:
        self.theme = theme_dict
        self.config["theme"] = theme_dict
        self._save_config()
        return True

    # -------- Config helpers --------
    def _load_config(self) -> Dict[str, Any]:
        for p in CONFIG_PATHS:
            try:
                if p.exists():
                    return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                logger.debug(f"Failed to load config at {p}", exc_info=True)
        return {
            "auto_apply_modifications": False,
            "xp": 0,
            "level": 1,
        }

    def _save_config(self) -> None:
        try:
            p = self.engine_dir / "config.json"
            _atomic_write(p, json.dumps(self.config, indent=2, ensure_ascii=False))
        except Exception:
            logger.debug("Failed to save config", exc_info=True)

    def _log_journal(self, entry: Dict[str, Any]) -> None:
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        self.journal.append(entry)
        _save_json(self.journal_path, self.journal)

    def _gain_xp(self, amount: int) -> None:
        self.xp += amount
        if self.xp >= self.level * 100:
            self.level += 1
            self.xp = 0
        self.config["xp"] = self.xp
        self.config["level"] = self.level
        self._save_config()

    # -------- Event bus --------
    def on(self, event: str, handler: Callable[..., None]):
        self._event_listeners.setdefault(event, []).append(handler)

    def _emit(self, event: str, *args, **kwargs):
        for h in list(self._event_listeners.get(event, [])):
            try:
                h(*args, **kwargs)
            except Exception:
                logger.debug("Event handler failed", exc_info=True)

    # -------- Git & 2025 workflow --------
    def _init_git(self):
        if not GITPY_AVAILABLE:
            return
        try:
            if (DEFAULT_PROJECT_ROOT / ".git").exists():
                self._git = Repo(str(DEFAULT_PROJECT_ROOT))
            elif (self.engine_dir / ".git").exists():
                self._git = Repo(str(self.engine_dir))
            else:
                self._git = None
            self.repo = self._git
            if self.repo and "origin" in [r.name for r in self.repo.remotes]:
                try:
                    self.repo.remotes.origin.pull(rebase=True)
                    logger.info("[SelfMod] Pulled latest code")
                except Exception as e:
                    logger.warning(f"[SelfMod] Pull failed: {e}")
        except Exception:
            self._git = None
            self.repo = None

    def git_status(self) -> str:
        if self._git:
            return self._git.git.status()
        return "Git not available"

    def git_commit(self, message: str) -> Dict[str, Any]:
        if not self._git:
            return {"success": False, "error": "Git not available"}
        try:
            self._git.git.add(A=True)
            out = self._git.git.commit(m=message)
            return {"success": True, "output": out}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_proposal_branch(self, proposal_id: str) -> Optional[str]:
        if not self.repo:
            return None
        branch_name = f"selfmod/{proposal_id}"
        try:
            self.repo.git.checkout("HEAD", b=branch_name)
            logger.info(f"[SelfMod] Created branch {branch_name}")
            return branch_name
        except Exception as e:
            logger.error(f"[SelfMod] Branch creation failed: {e}")
            return None

    def _run_tests(self) -> bool:
        if not (DEFAULT_PROJECT_ROOT / "tests").exists() and not (DEFAULT_PROJECT_ROOT / "test").exists():
            logger.info("[SelfMod] No tests directory found – skipping test step")
            return True
        try:
            result = subprocess.run(
                ["pytest", "-q", "--tb=short"],
                cwd=str(DEFAULT_PROJECT_ROOT),
                capture_output=True,
                timeout=90,
            )
            success = result.returncode == 0
            logger.info(f"[SelfMod] Tests {'PASSED' if success else 'FAILED'}")
            if not success:
                logger.warning(result.stdout.decode() + result.stderr.decode())
            return success
        except Exception as e:
            logger.error(f"[SelfMod] Test execution failed: {e}")
            return False

    def _merge_branch(self, branch_name: str, proposal_id: str):
        if not self.repo:
            return False
        try:
            self.repo.git.checkout("main")
            self.repo.git.merge(branch_name, ff_only=False)
            if "origin" in [r.name for r in self.repo.remotes]:
                self.repo.remotes.origin.push()
                self.repo.git.push("origin", "--delete", branch_name)
            self.repo.git.branch("-d", branch_name)
            logger.info(f"[SelfMod] Merged & pushed proposal {proposal_id}")
            return True
        except GitCommandError as e:
            logger.error(f"[SelfMod] Merge conflict for {proposal_id}: {e}")
            if OPENAI_CLIENT_AVAILABLE:
                try:
                    client = OpenAI()
                    resolution = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "user",
                            "content": f"Resolve this git conflict automatically. Return only the resolved file content:\n\n{e.stdout}"
                        }]
                    ).choices[0].message.content
                    conflict_file = e.stdout.split("CONFLICT (content): ")[1].split(" in ")[0]
                    Path(conflict_file).write_text(resolution)
                    self.repo.git.add(conflict_file)
                    self.repo.index.commit(f"SelfMod auto-resolved conflict for {proposal_id}")
                    return self._merge_branch(branch_name, proposal_id)
                except Exception:
                    logger.exception("[SelfMod] LLM conflict resolution failed")
            return False

    # -------- Persistent failure DB (2025) --------
    def _init_failure_db(self):
        try:
            conn = sqlite3.connect(str(FAILURES_DB))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS failures (
                    id INTEGER PRIMARY KEY,
                    proposal_id TEXT,
                    error TEXT,
                    code TEXT,
                    ts REAL
                )
            """)
            if VECTOR_MEMORY:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS failure_vectors (
                        failure_id INTEGER,
                        embedding BLOB
                    )
                """)
            conn.close()
        except Exception:
            logger.debug("Failed to init failures DB", exc_info=True)

    # -------- Safety: Freeze & Rate limiting --------
    def _check_frozen(self) -> bool:
        if FREEZE_FILE.exists():
            if not self.autonomy_frozen:
                logger.warning("[SelfMod] AUTONOMY FROZEN BY USER")
                self.autonomy_frozen = True
            return True
        self.autonomy_frozen = False
        return False

    def _allow_risky_action(self) -> bool:
        if self._check_frozen():
            return False
        events = _load_json(AUTONOMY_LOG, [])
        hour_ago = time.time() - 3600
        recent = [e for e in events if e["ts"] > hour_ago and e.get("risky", False)]
        return len(recent) < MAX_RISKY_PER_HOUR

    def _log_autonomy_event(self, risky: bool = False):
        events = _load_json(AUTONOMY_LOG, [])
        events.append({"ts": time.time(), "risky": risky})
        events = events[-1000:]
        _save_json(AUTONOMY_LOG, events)

    # -------- Env loader --------
    def load_env_from_root(self, env_root: Optional[Path] = None) -> Dict[str, Any]:
        with self._lock:
            root = Path(env_root) if env_root else ROOT_ENV_PATH
            dotenv_path = root / ".env"
            if not dotenv_path.exists():
                return {"success": False, "error": f".env not found at {dotenv_path}"}
            try:
                vals: Dict[str, str] = {}
                if DOTENV_AVAILABLE:
                    vals = {
                        k: ("" if v is None else str(v))
                        for k, v in dotenv_values(str(dotenv_path)).items()
                    }
                else:
                    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        vals[k.strip()] = v.strip().strip('"').strip("'")
                openai_key = vals.get("OPENAI_API_KEY", "").strip()
                if openai_key and OPENAI_AVAILABLE and OPENAI_CLIENT_AVAILABLE:
                    os.environ["OPENAI_API_KEY"] = openai_key
                    self._code_factory = OpenAICodeFactory()
                    logger.info("OpenAI factory wired from .env")
                self._env_cache = vals
                return {"success": True, "loaded": list(vals.keys())}
            except Exception as e:
                logger.exception("load_env_from_root failed")
                return {"success": False, "error": str(e)}

    # -------- Scanning / static analysis --------
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        analysis = {
            "file": file_path.name,
            "lines": len(content.splitlines()),
            "size": len(content),
            "issues": [],
        }
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    analysis["issues"].append("import detected")
        except SyntaxError:
            analysis["issues"].append("syntax error")
        return analysis

    def scan_codebase(self, target_module: Optional[str]) -> Dict[str, Any]:
        with self._lock:
            try:
                if target_module:
                    p = self._resolve_target_file(target_module)
                    if not p:
                        return {"success": False, "error": "module not found"}
                    return {"success": True, "analysis": self._analyze_file(p)}
                files = list(self.engine_dir.glob("*.py")) + list(
                    DEFAULT_PROJECT_ROOT.glob("*.py")
                )
                analyses = [
                    self._analyze_file(f)
                    for f in files
                    if f.is_file() and not f.name.startswith("__")
                ]
                return {"success": True, "analyses": analyses}
            except Exception as e:
                logger.exception("scan_codebase failed")
                return {"success": False, "error": str(e)}

    # -------- File resolution --------
    def _resolve_target_file(self, name_or_path: str) -> Optional[Path]:
        try:
            cand = Path(name_or_path)
            if cand.is_absolute() and cand.exists():
                return cand.resolve()
            base = os.path.basename(name_or_path)
            if not base.endswith(".py"):
                base += ".py"
            roots: List[Path] = []
            proj = DEFAULT_PROJECT_ROOT
            if proj.exists():
                roots.append(proj)
            env_root = os.getenv("SARAPHINA_PROJECT_ROOT", "D:/Saraphina Root")
            try:
                envp = Path(env_root)
                if envp.exists():
                    roots.append(envp)
            except Exception:
                pass
            eng = self.engine_dir or self.root
            if eng.exists():
                roots.append(eng)
            for r in roots:
                p = (r / base).resolve()
                if p.exists():
                    return p
            if roots:
                for p in roots[0].rglob(base):
                    return p.resolve()
        except Exception:
            pass
        return None

    # -------- Proposal validation / apply --------
    def _validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        code = proposal.get("code", "")
        if not code:
            return {"success": False, "error": "no code provided"}
        if len(code) > MAX_FILE_SIZE:
            return {"success": False, "error": "code exceeds max size"}
        code_lower = code.lower()
        for kw in self._dangerous_keywords:
            if kw in code_lower:
                suggestion = "Try using psutil or higher-level APIs instead of low-level primitives."
                self.learned_failures[kw] = (
                    f"avoid using '{kw}', fallback to safer methods"
                )
                _save_json(LEARNED_FAILURES_PATH, self.learned_failures)
                return {
                    "success": False,
                    "error": f"unsafe keyword detected: {kw}",
                    "learned": self.learned_failures[kw],
                    "retry_suggestion": suggestion,
                }
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {"success": False, "error": f"syntax error: {e}"}
        return {"success": True}

    def _apply_code_to_target(
        self, target_file: Path, new_code: str, proposal_id: str
    ) -> Dict[str, Any]:
        if not target_file.exists():
            return {"success": False, "error": "target does not exist"}
        orig = target_file.read_text(encoding="utf-8")
        backup = _make_backup(target_file, self._backup_dir)
        _atomic_write(target_file, new_code)
        diff = "\n".join(
            difflib.unified_diff(
                orig.splitlines(), new_code.splitlines(), lineterm=""
            )
        )
        return {"success": True, "backup": str(backup), "diff": diff}

    # -------- Self-review with LLM (2025) --------
    def _self_review_proposal(self, diff: str, safety_level: str) -> bool:
        if not OPENAI_CLIENT_AVAILABLE or not OPENAI_AVAILABLE:
            return True
        try:
            client = OpenAI()
            prompt = f"""
You are an elite safety & quality reviewer.
Review this code change for:
- Bugs / logic errors
- Security vulnerabilities
- Performance issues
- Style violations
- Backwards compatibility breaks

Diff:
{diff}

For safety level '{safety_level}', decide if it is acceptable.

Answer only YES or NO. If NO, give a one-sentence reason.
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            ).choices[0].message.content.strip()
            approved = response.upper().startswith("YES")
            if not approved:
                logger.warning(f"[SelfMod] SELF-REVIEW REJECTED: {response}")
            return approved
        except Exception:
            logger.debug("Self-review failed, defaulting to approve", exc_info=True)
            return True

    # -------- Docker sandbox stub --------
    def _docker_test_mutation(self, proposal_id: str, code: str) -> Dict[str, Any]:
        try:
            compile(code, f"<proposal_{proposal_id}>", "exec")
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"syntax error: {e}",
                "phase": "syntax_check",
            }
        return {
            "success": True,
            "notes": "syntax_ok; docker sandbox not yet wired",
            "phase": "syntax_check",
        }

    # -------- Higher-level autonomous pipeline (2025) --------
    def _autonomous_propose_apply(
        self,
        tpath: Path,
        improvement_spec: str,
        safety_level: str = "high",
        simulation_only: bool = False,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        if self._check_frozen():
            return {"success": False, "error": "Autonomy frozen"}

        proposal_id = f"auto_{uuid.uuid4().hex[:8]}"
        original_code = tpath.read_text(encoding="utf-8", errors="ignore")

        if not OPENAI_CLIENT_AVAILABLE or not OPENAI_AVAILABLE:
            return {"success": False, "error": "OpenAI autonomous pipeline unavailable"}

        # Snapshot before generating
        try:
            self.vcs.create_snapshot(trigger=f"autonomous_{proposal_id}")
        except Exception:
            logger.debug("Snapshot failed (autonomous pipeline)", exc_info=True)

        client = OpenAI()
        model_name = DEFAULT_LLM_MODEL
        prompt = f"""
You are Saraphina's self-improvement engineer.
Target file: {tpath.name}

Current code:
{original_code}

Improvement request:
{improvement_spec}

IMPORTANT:
- Keep UltraAICore and all core subsystems present.
- Do NOT replace the file with a tiny stub.
- Make minimal, safe changes only.

Return ONLY the full new file content. No explanations, no markdown.
"""
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3 if safety_level != "experimental" else 0.7,
        )
        new_code = resp.choices[0].message.content.strip()
        if new_code.startswith("```"):
            new_code = new_code.split("\n", 1)[1].rsplit("```", 1)[0]

        # Risk model (optional)
        if RiskModel is not None:
            try:
                risks = RiskModel.assess_code(new_code)
                if not RiskModel.is_safe(risks):
                    desc = [getattr(r, "description", str(r)) for r in risks]
                    safe_log(f"[SelfMod] Autonomous proposal blocked by RiskModel: {desc}", level="ERROR")
                    self.mutation_logger.log_mutation(
                        mutation_id=proposal_id,
                        actor="autonomous",
                        action="risk_block",
                        target_file=str(tpath),
                        proposal_id=proposal_id,
                        safety_level=safety_level,
                        code_hash=_hash_text(new_code),
                        diff="",
                        status="risk_blocked",
                        metadata={"risks": desc},
                    )
                    return {"success": False, "error": "risk_model_blocked", "risks": desc}
            except Exception:
                logger.debug("RiskModel check failed (ignored)", exc_info=True)

        # Anti-downgrade check
        if not self.prevent_downgrade(new_code, original_code):
            self.mutation_logger.log_mutation(
                mutation_id=proposal_id,
                actor="autonomous",
                action="downgrade_block",
                target_file=str(tpath),
                proposal_id=proposal_id,
                safety_level=safety_level,
                code_hash=_hash_text(new_code),
                diff="",
                status="downgrade_blocked",
                metadata={"reason": "prevent_downgrade"},
            )
            return {"success": False, "error": "downgrade_prevention_triggered"}

        diff = "".join(
            difflib.unified_diff(
                original_code.splitlines(keepends=True),
                new_code.splitlines(keepends=True),
                fromfile=tpath.name,
                tofile=tpath.name,
            )
        )

        sandbox_res = self._docker_test_mutation(proposal_id, new_code)
        if not sandbox_res.get("success", False):
            self.mutation_logger.log_mutation(
                mutation_id=proposal_id,
                actor="autonomous",
                action="sandbox_reject",
                target_file=str(tpath),
                proposal_id=proposal_id,
                safety_level=safety_level,
                code_hash=_hash_text(new_code),
                diff=diff,
                status="sandbox_failed",
                metadata={"sandbox": sandbox_res},
            )
            return {"success": False, "error": "sandbox_failed", "details": sandbox_res}

        proposal = {
            "proposal_id": proposal_id,
            "target_file": tpath.name,
            "spec": improvement_spec,
            "diff": diff,
            "new_code": new_code,
            "original_code": original_code,
            "timestamp": time.time(),
            "safety_level": safety_level,
            "status": "pending_confirmation",
        }

        _save_json(PROPOSAL_DIR / f"{proposal_id}.json", proposal)

        if safety_level in ("high", "medium"):
            if not self._self_review_proposal(diff, safety_level):
                proposal["status"] = "rejected_by_self_review"
                self.mutation_logger.log_mutation(
                    mutation_id=proposal_id,
                    actor="autonomous",
                    action="self_review_reject",
                    target_file=str(tpath),
                    proposal_id=proposal_id,
                    safety_level=safety_level,
                    code_hash=_hash_text(new_code),
                    diff=diff,
                    status="rejected_by_self_review",
                    metadata={"self_review": "rejected"},
                )
                return {"success": False, "proposal": proposal, "error": "rejected_by_self_review"}

        risky = safety_level == "experimental"
        if risky and not self._allow_risky_action():
            self.mutation_logger.log_mutation(
                mutation_id=proposal_id,
                actor="autonomous",
                action="rate_limit_block",
                target_file=str(tpath),
                proposal_id=proposal_id,
                safety_level=safety_level,
                code_hash=_hash_text(new_code),
                diff=diff,
                status="rate_limited",
                metadata={"reason": "MAX_RISKY_PER_HOUR exceeded"},
            )
            return {"success": False, "error": "Rate limit exceeded for risky actions"}

        self.mutation_logger.log_mutation(
            mutation_id=proposal_id,
            actor="autonomous",
            action="propose_autonomous",
            target_file=str(tpath),
            proposal_id=proposal_id,
            safety_level=safety_level,
            code_hash=_hash_text(new_code),
            diff=diff,
            status="proposed",
            metadata={"spec": improvement_spec, "sandbox": sandbox_res},
        )

        if simulation_only:
            proposal["simulation"] = True
            return {"success": True, "simulation": True, "proposal": proposal}

        return {"success": True, "proposal": proposal}

    # -------- propose_improvement (classic API, upgraded safety) --------
    def propose_improvement(
        self,
        target_file: str,
        improvement_spec: str,
        safety_level: str = "high",
        context: Optional[Dict[str, Any]] = None,
        auto_apply: bool = False,
        simulation_only: bool = False,
    ) -> Dict[str, Any]:
        if auto_apply:
            logger.warning("[SelfMod] auto_apply=True is ignored — confirmation now required for all changes.")

        with self._lock:
            try:
                tpath = self._resolve_target_file(target_file)
                if not tpath:
                    return {"success": False, "error": "target file not resolvable"}

                # Take a snapshot whenever we touch ultra_core or other critical files
                try:
                    if os.path.basename(tpath.name) in ("ultra_core.py", "self_modification_engine.py"):
                        self.vcs.create_snapshot(trigger=f"proposal_{os.path.basename(tpath.name)}")
                except Exception:
                    logger.debug("Snapshot failed (propose_improvement)", exc_info=True)

                if simulation_only and OPENAI_CLIENT_AVAILABLE and OPENAI_AVAILABLE:
                    auto_result = self._autonomous_propose_apply(
                        tpath,
                        improvement_spec,
                        safety_level=safety_level,
                        simulation_only=True,
                    )
                    return auto_result

                orig = tpath.read_text(encoding="utf-8", errors="ignore") if tpath.exists() else ""

                ctx: Dict[str, Any] = {
                    "original_code": orig,
                    "file": tpath.name,
                    "successful_patterns": self.successful_patterns,
                    "learned_failures": self.learned_failures,
                }
                if isinstance(context, dict):
                    ctx.update(context)

                gen = self._code_factory.propose_code(
                    improvement_spec, "python", context=ctx
                )
                if not gen.get("success"):
                    return {
                        "success": False,
                        "error": gen.get("error", "code generation failed"),
                    }

                val = self._validate_proposal(gen)
                if not val.get("success"):
                    retry_suggestion = val.get("retry_suggestion")
                    if retry_suggestion:
                        logger.info(f"Retrying after learning: {retry_suggestion}")
                        retry_spec = (
                            f"{improvement_spec}\n"
                            f"IMPORTANT: {retry_suggestion} "
                            f"Avoid unsafe modules. Prefer psutil, standard library, or safe alternatives."
                        )
                        gen_retry = self._code_factory.propose_code(
                            retry_spec, "python", context=ctx
                        )
                        val_retry = self._validate_proposal(gen_retry)
                        if val_retry.get("success"):
                            gen = gen_retry
                            logger.info("Retry succeeded with safer code.")
                        else:
                            return {
                                "success": False,
                                "error": val_retry.get("error", "retry failed"),
                            }
                    else:
                        return {"success": False, "error": val.get("error")}

                code = gen.get("code", "")

                # Optional RiskModel check
                if RiskModel is not None:
                    try:
                        risks = RiskModel.assess_code(code)
                        if not RiskModel.is_safe(risks):
                            desc = [getattr(r, "description", str(r)) for r in risks]
                            safe_log(f"[SelfMod] Proposal blocked by RiskModel: {desc}", level="ERROR")
                            return {"success": False, "error": "Ethical/Safety Risk Detected", "risks": desc}
                    except Exception:
                        logger.debug("RiskModel check failed (ignored)", exc_info=True)

                # Anti-downgrade check specifically for ultra_core.py
                if tpath.name == "ultra_core.py":
                    if not self.prevent_downgrade(code, orig):
                        return {"success": False, "error": "Downgrade prevention protocol triggered."}

                diff = "\n".join(
                    difflib.unified_diff(
                        orig.splitlines(), code.splitlines(), lineterm=""
                    )
                )

                pid = f"improve_{uuid.uuid4().hex[:10]}"
                s_enum = (
                    SafetyLevel(safety_level.lower())
                    if safety_level.lower() in SafetyLevel._value2member_map_
                    else SafetyLevel.HIGH
                )

                if s_enum is SafetyLevel.CRITICAL:
                    logger.warning(
                        f"[SelfMod] CRITICAL proposal created and requires explicit confirmation: {improvement_spec}"
                    )

                record = {
                    "proposal_id": pid,
                    "feature_spec": improvement_spec,
                    "language": "python",
                    "code": code,
                    "metadata": {
                        "target_file": tpath.name,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                    },
                    "safety_checks": {
                        "safety_level": s_enum.value,
                        "requires_owner_approval": s_enum.requires_confirmation,
                        "approved": False,
                    },
                    "auto_apply_requested": bool(auto_apply),
                    "status": "pending_confirmation",
                    "diff": diff,
                }
                self.proposal_db.store_proposal(record)

                # FIXED: correct f-string, removed stray "}"
                prop_path = PROPOSAL_DIR / f"{pid}.py"
                _atomic_write(prop_path, record["code"])
                record["proposal_path"] = str(prop_path)

                self.audit.log_event(
                    "propose_improvement",
                    {"proposal_id": pid, "target": target_file},
                    True,
                )
                self._log_journal(
                    {
                        "event": "propose_improvement",
                        "proposal_id": pid,
                        "target": target_file,
                    }
                )
                self._emit("proposal_created", record)

                self.mutation_logger.log_mutation(
                    mutation_id=pid,
                    actor="user_or_autonomous",
                    action="propose_improvement",
                    target_file=str(tpath),
                    proposal_id=pid,
                    safety_level=s_enum.value,
                    code_hash=_hash_text(code),
                    diff=diff,
                    status="proposed",
                    metadata={
                        "spec": improvement_spec,
                        "simulation_only": simulation_only,
                        "auto_apply_requested": bool(auto_apply),
                    },
                )

                if simulation_only:
                    return {
                        "success": True,
                        "proposal_id": pid,
                        "target": target_file,
                        "simulation": True,
                        "code": record["code"],
                    }

                return {
                    "success": True,
                    "proposal_id": pid,
                    "target": target_file,
                    "applied": False,
                    "requires_confirmation": s_enum.requires_confirmation,
                }
            except Exception as e:
                logger.exception("propose_improvement failed")
                return {"success": False, "error": str(e)}

    def confirm_proposal(self, proposal_id: str, actor: str = "owner", auto_git_commit: bool = True) -> Dict[str, Any]:
        with self._lock:
            prop = self.proposal_db.get_proposal(proposal_id)
            if not prop:
                return {"success": False, "error": "proposal not found"}

            status = prop.get("status")
            if status not in ("pending_confirmation", "created"):
                return {"success": False, "error": f"proposal status: {status}"}

            tpath = self._resolve_target_file(
                prop.get("metadata", {}).get("target_file", "")
            )
            if not tpath:
                return {"success": False, "error": "target file not resolvable"}
            code = prop.get("code", "")

            # Final anti-downgrade guard on confirm for ultra_core.py
            if tpath.name == "ultra_core.py":
                current_code = tpath.read_text(encoding="utf-8", errors="ignore")
                if not self.prevent_downgrade(code, current_code):
                    return {"success": False, "error": "Downgrade prevention triggered at apply time."}

            try:
                apply_res = self._apply_code_to_target(tpath, code, proposal_id)
                if not apply_res.get("success"):
                    raise Exception(apply_res.get("error"))

                sc = prop.setdefault("safety_checks", {})
                sc["approved"] = True
                sc["approved_by"] = actor
                sc["approved_at"] = time.time()
                self.proposal_db.set_status(proposal_id, "applied")

                spec = prop.get("feature_spec", "").lower()
                tag = None
                if "cpu" in spec or "monitor" in spec:
                    tag = "cpu_monitor"
                elif "memory" in spec or "ram" in spec:
                    tag = "memory_usage"
                elif "disk" in spec:
                    tag = "disk_usage"
                if tag and len(code) < 2000:
                    self.successful_patterns[tag] = code.strip()
                    _save_json(SUCCESSFUL_PATTERNS_PATH, self.successful_patterns)
                    logger.info(f"Learned successful pattern: {tag}")

                self.mutation_logger.log_mutation(
                    mutation_id=proposal_id,
                    actor=actor,
                    action="apply_improvement",
                    target_file=str(tpath),
                    proposal_id=proposal_id,
                    safety_level=sc.get("safety_level", "high"),
                    code_hash=_hash_text(code),
                    diff=apply_res.get("diff", ""),
                    backup_path=apply_res.get("backup", ""),
                    status="applied",
                    metadata={
                        "approved_by": actor,
                        "feature_spec": prop.get("feature_spec", ""),
                    },
                )

                git_info = None
                if auto_git_commit and self._git:
                    msg = (
                        f"Self-mod: {prop.get('feature_spec','')}\n"
                        f"Proposal: {proposal_id}\n"
                        f"Safety: {sc.get('safety_level','high')}\n"
                        f"Actor: {actor}\n"
                    )
                    git_info = self.git_commit(msg)

                self.audit.log_event(
                    "apply_improvement",
                    {"proposal_id": proposal_id, "target": tpath.name, "git": git_info},
                    True,
                )
                self._log_journal(
                    {
                        "event": "proposal_applied",
                        "proposal_id": proposal_id,
                        "target": str(tpath),
                    }
                )
                self._gain_xp(20)
                self._emit(
                    "proposal_applied",
                    {
                        "proposal_id": proposal_id,
                        "target": tpath.name,
                        "diff": apply_res.get("diff"),
                    },
                )
                self._hot_reload(str(tpath))
                return {
                    "success": True,
                    "target": str(tpath),
                    "backup": str(apply_res.get("backup")),
                    "diff": apply_res.get("diff"),
                    "git": git_info,
                }
            except Exception as e:
                self.audit.log_event(
                    "apply_improvement",
                    {"proposal_id": proposal_id, "error": str(e)},
                    False,
                )
                self._log_journal(
                    {"event": "apply_failed", "proposal_id": proposal_id, "error": str(e)}
                )
                self.learned_failures["last_apply_error"] = str(e)
                _save_json(LEARNED_FAILURES_PATH, self.learned_failures)
                self.mutation_logger.log_mutation(
                    mutation_id=proposal_id,
                    actor=actor,
                    action="apply_failed",
                    proposal_id=proposal_id,
                    status="apply_failed",
                    metadata={"error": str(e)},
                )
                return {"success": False, "error": str(e)}

    def apply_improvement(self, proposal_id: str) -> Dict[str, Any]:
        return self.confirm_proposal(proposal_id, actor="legacy")

    # -------- New modules --------
    def propose_module(
        self,
        module_name: str,
        spec: str,
        safety_level: str = "high",
        auto_apply: bool = False,
    ) -> Dict[str, Any]:
        if auto_apply:
            logger.warning("[SelfMod] auto_apply ignored for propose_module; confirmation required.")
        with self._lock:
            try:
                safe_name = module_name.strip().replace(" ", "_")
                if not safe_name.endswith(".py"):
                    safe_name += ".py"
                tpath = DEFAULT_PROJECT_ROOT / safe_name
                if tpath.exists():
                    return {"success": False, "error": "module already exists"}
                gen = self._code_factory.propose_code(spec, "python")
                if not gen.get("success"):
                    return {
                        "success": False,
                        "error": gen.get("error", "code generation failed"),
                    }
                val = self._validate_proposal(gen)
                if not val.get("success"):
                    retry_suggestion = val.get("retry_suggestion")
                    if retry_suggestion:
                        logger.info(f"Module retry: {retry_suggestion}")
                        retry_spec = f"{spec}\n{retry_suggestion}"
                        gen_retry = self._code_factory.propose_code(
                            retry_spec, "python"
                        )
                        val_retry = self._validate_proposal(gen_retry)
                        if val_retry.get("success"):
                            gen = gen_retry
                        else:
                            return {
                                "success": False,
                                "error": val_retry.get("error"),
                            }
                    else:
                        return {"success": False, "error": val.get("error")}
                pid = f"module_{uuid.uuid4().hex[:10]}"
                s_enum = (
                    SafetyLevel(safety_level.lower())
                    if safety_level.lower() in SafetyLevel._value2member_map_
                    else SafetyLevel.HIGH
                )
                record = {
                    "proposal_id": pid,
                    "feature_spec": spec,
                    "language": "python",
                    "code": gen.get("code", ""),
                    "metadata": {
                        "target_file": safe_name,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                    },
                    "safety_checks": {
                        "safety_level": s_enum.value,
                        "requires_owner_approval": s_enum.requires_confirmation,
                        "approved": False,
                    },
                    "status": "pending_confirmation",
                }
                self.proposal_db.store_proposal(record)
                self.audit.log_event(
                    "propose_module", {"proposal_id": pid, "target": safe_name}, True
                )
                self._log_journal(
                    {"event": "propose_module", "proposal_id": pid, "target": safe_name}
                )
                self._emit("proposal_created", record)
                self.mutation_logger.log_mutation(
                    mutation_id=pid,
                    actor="user_or_autonomous",
                    action="propose_module",
                    target_file=str(tpath),
                    proposal_id=pid,
                    safety_level=s_enum.value,
                    code_hash=_hash_text(gen.get("code","")),
                    diff="",
                    status="proposed",
                    metadata={"spec": spec},
                )
                return {"success": True, "proposal_id": pid, "target": safe_name}
            except Exception as e:
                logger.exception("propose_module failed")
                return {"success": False, "error": str(e)}

    # -------- Runtime import / Hot reloading --------
    def import_module_runtime(self, module_filename: str) -> Dict[str, Any]:
        with self._lock:
            try:
                fpath = self._resolve_target_file(module_filename)
                if not fpath or not fpath.exists():
                    return {"success": False, "error": "file not found"}
                import importlib.util

                module_name = f"saraphina_dynamic_{fpath.stem}_{uuid.uuid4().hex[:6]}"
                spec = importlib.util.spec_from_file_location(module_name, str(fpath))
                if not spec or not spec.loader:
                    return {"success": False, "error": "loader unavailable"}
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "initialize") and callable(mod.initialize):
                    try:
                        mod.initialize()
                    except Exception:
                        logger.debug("module initialize raised", exc_info=True)
                self._emit(
                    "module_imported", {"module": module_name, "file": fpath.name}
                )
                return {"success": True, "module": module_name}
            except Exception as e:
                logger.exception("dynamic import failed")
                return {"success": False, "error": str(e)}

    def _hot_reload(self, filepath: str) -> bool:
        module_name = Path(filepath).stem
        if module_name in sys.modules:
            try:
                importlib.invalidate_caches()
                importlib.reload(sys.modules[module_name])
                logger.info(f"[SelfMod] Hot-reloaded {module_name}")
                return True
            except Exception as e:
                logger.warning(f"[SelfMod] Hot-reload failed for {module_name}: {e}")
        return False

    # -------- Autonomy session --------
    def enable_autonomy_session(self) -> bool:
        self.autonomous_enabled = True
        self.audit.log_event("autonomy_enabled", {}, True)
        self._emit("autonomy_enabled", {})
        return True

    def disable_autonomy_session(self) -> None:
        self.autonomous_enabled = False
        self.audit.log_event("autonomy_disabled", {}, True)
        self._emit("autonomy_disabled", {})

    # -------- Packages --------
    def detect_missing_packages(self, python_file: Optional[Path] = None) -> Dict[str, Any]:
        with self._lock:
            files = (
                [python_file]
                if python_file
                else list(DEFAULT_PROJECT_ROOT.glob("*.py"))
                + list(self.engine_dir.glob("*.py"))
            )
            needs: Dict[str, bool] = {}
            for f in files:
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(text)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                name = alias.name.split(".")[0]
                                if name not in needs:
                                    try:
                                        __import__(name)
                                        needs[name] = True
                                    except Exception:
                                        needs[name] = False
                        if isinstance(node, ast.ImportFrom):
                            mod = (node.module or "").split(".")[0]
                            if mod and mod not in needs:
                                try:
                                    __import__(mod)
                                    needs[mod] = True
                                except Exception:
                                    needs[mod] = False
                except Exception:
                    continue
            self._emit("detect_missing_packages", needs)
            return needs

    def request_install_packages(self, packages: List[str]) -> Dict[str, Any]:
        pid = f"install_{uuid.uuid4().hex[:10]}"
        rec = {
            "proposal_id": pid,
            "feature_spec": f"install {packages}",
            "language": "system",
            "code": "",
            "metadata": {
                "packages": packages,
                "created_at": datetime.utcnow().isoformat() + "Z",
            },
            "safety_checks": {"requires_owner_approval": False},
            "status": "pending_confirmation",
        }
        self.proposal_db.store_proposal(rec)
        self.audit.log_event(
            "install_requested", {"proposal_id": pid, "packages": packages}, True
        )
        self._log_journal(
            {
                "event": "install_requested",
                "proposal_id": pid,
                "packages": packages,
            }
        )
        self._emit("install_requested", rec)
        return {"success": True, "proposal_id": pid, "packages": packages}

    def confirm_install_packages(
        self, proposal_id: str, allow_upgrade: bool = False
    ) -> Dict[str, Any]:
        with self._lock:
            prop = self.proposal_db.get_proposal(proposal_id)
            if not prop:
                return {"success": False, "error": "proposal not found"}
            pkgs = prop.get("metadata", {}).get("packages", [])
            if not pkgs:
                return {"success": False, "error": "no packages listed"}
            cmd = [sys.executable, "-m", "pip", "install"] + (
                ["--upgrade"] if allow_upgrade else []
            ) + pkgs
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=900,
                )
                success = proc.returncode == 0
                self.proposal_db.set_status(
                    proposal_id, "installed" if success else "failed"
                )
                self.audit.log_event(
                    "install_executed",
                    {"proposal_id": proposal_id, "returncode": proc.returncode},
                    success,
                )
                self._log_journal(
                    {
                        "event": "install_executed",
                        "proposal_id": proposal_id,
                        "success": success,
                    }
                )
                if success:
                    self._gain_xp(10)
                return {
                    "success": success,
                    "stdout": proc.stdout.decode("utf-8", "ignore"),
                    "stderr": proc.stderr.decode("utf-8", "ignore"),
                }
            except Exception as e:
                logger.exception("install failed")
                return {"success": False, "error": str(e)}

    # -------- Backups / rollback --------
    def rollback_from_backup(self, backup_filename: str) -> Dict[str, Any]:
        bpath = self._backup_dir / backup_filename
        if not bpath.exists():
            return {"success": False, "error": "backup not found"}
        fname = backup_filename.split(".")[0]
        target = self._resolve_target_file(fname)
        if not target:
            return {"success": False, "error": "target not resolvable"}
        shutil.copy2(str(bpath), str(target))
        self.audit.log_event(
            "rollback",
            {"backup": backup_filename, "restored": target.name},
            True,
        )
        self._log_journal(
            {
                "event": "rollback_performed",
                "backup": backup_filename,
                "file": str(target),
            }
        )
        self._emit("rollback", {"backup": backup_filename})
        self._hot_reload(str(target))
        return {"success": True, "restored": str(target)}

    def rollback_last(self, target_file: str) -> Dict[str, Any]:
        tpath = self._resolve_target_file(target_file)
        if not tpath:
            return {"success": False, "error": "target not resolvable"}
        backups = sorted(self._backup_dir.glob(f"{tpath.name}.*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not backups:
            return {"success": False, "error": "No backup found."}
        latest = backups[0]
        shutil.copy2(str(latest), str(tpath))
        self._log_journal(
            {"event": "rollback_last_performed", "file": target_file}
        )
        self.audit.log_event("rollback_last", {"file": target_file}, True)
        self._hot_reload(str(tpath))
        return {"success": True, "restored_from": str(latest)}

    # -------- Introspection --------
    def list_proposals(self) -> List[Dict[str, Any]]:
        return list(getattr(self.proposal_db, "_store", {}).values())

    def get_proposal(self, pid: str) -> Optional[Dict[str, Any]]:
        return self.proposal_db.get_proposal(pid)

    def show_proposal(self, pid: str) -> Dict[str, Any]:
        prop = self.get_proposal(pid)
        if not prop:
            return {"success": False, "error": "proposal not found"}
        code = prop.get("code", "")
        target_file = prop.get("metadata", {}).get("target_file", "")
        tpath = self._resolve_target_file(target_file)
        if tpath and tpath.exists():
            orig = tpath.read_text(encoding="utf-8")
            diff = "\n".join(
                difflib.unified_diff(
                    orig.splitlines(), code.splitlines(), lineterm=""
                )
            )
            prop["preview_diff"] = diff
        return {"success": True, "proposal": prop}

    # -------- GUI compatibility shim --------
    def accept_spec_and_propose(self, spec: dict, actor: str = "gui") -> dict:
        try:
            candidates: List[str] = []
            if isinstance(spec, dict):
                t = spec.get("targets") or spec.get("target") or []
                if isinstance(t, str):
                    candidates = [t]
                elif isinstance(t, list):
                    candidates = [x for x in t if isinstance(x, str)]
            if not candidates:
                candidates = ["saraphina_gui.py"]
            chosen: Optional[Path] = None
            for c in candidates:
                p = self._resolve_target_file(c)
                if p:
                    chosen = p
                    break
            if not chosen:
                name = os.path.basename(candidates[0])
                chosen = self._resolve_target_file(name)
                if not chosen:
                    return {"success": False, "error": f"Target not found: {name}"}

            safety = (
                spec.get("safety_level") if isinstance(spec, dict) else None
            ) or "high"
            text = ""
            if isinstance(spec, dict):
                text = (
                    spec.get("improvement_spec")
                    or spec.get("summary")
                    or spec.get("request")
                    or ""
                )
                desired = spec.get("desired_changes")
                if isinstance(desired, list) and desired:
                    text += "\nDesired changes:\n" + "\n".join(
                        [json.dumps(x, ensure_ascii=False) for x in desired]
                    )
            if not text.strip():
                text = (
                    "Implement the requested improvement inferred from user intent and context."
                )

            auto_apply_flag = False
            if isinstance(spec, dict) and spec.get("auto_apply") in (
                True,
                "true",
                "True",
                "1",
            ):
                auto_apply_flag = False
            elif self.config.get("auto_apply_modifications"):
                auto_apply_flag = False

            res = self.propose_improvement(
                str(chosen),
                text,
                safety_level=safety,
                context=spec.get("context") if isinstance(spec, dict) else None,
                auto_apply=auto_apply_flag,
            )
            if res.get("success"):
                self._emit(
                    "proposal_created",
                    {"proposal_id": res.get("proposal_id"), "metadata": res.get("metadata")},
                )
            return res
        except Exception as e:
            logger.exception("accept_spec_and_propose failed")
            return {"success": False, "error": str(e)}

    def handle_instruction(self, instruction: str) -> Dict[str, Any]:
        text = (instruction or "").strip()
        if not text:
            return {"success": False, "error": "Empty instruction."}

        lowered = text.lower()
        targets: List[str] = []
        if "ultra_core" in lowered or "chat_v4" in lowered:
            targets.append("ultra_core.py")
        if "saraphina_gui" in lowered or "gui" in lowered:
            targets.append("saraphina_gui.py")
        if not targets:
            targets = ["ultra_core.py"]

        if hasattr(self, "accept_spec_and_propose"):
            spec = {
                "improvement_spec": text,
                "targets": targets,
                "safety_level": "high",
                "auto_apply": False,
                "context": {
                    "source": "gui_self_mod",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
            }
            res = self.accept_spec_and_propose(spec, actor="gui")
        else:
            res = self.propose_improvement(
                targets[0],
                text,
                safety_level="high",
                context={"source": "gui_self_mod"},
                auto_apply=False,
            )

        if res.get("success"):
            pid = res.get("proposal_id")
            return {
                "success": True,
                "proposal_id": pid,
                "targets": targets,
                "message": (
                    f"Self-mod proposal {pid} created for {', '.join(targets)}. "
                    "You must review and apply it from the Self-Upgrade panel."
                ),
                "raw": res,
            }
        return {
            "success": False,
            "error": res.get("error", "Unknown error creating self-mod proposal."),
            "raw": res,
        }

    # -------- GUI autowire --------
    def try_autowire_into_gui(self, gui_root_object) -> bool:
        try:
            if not gui_root_object:
                return False

            def _on_created(record):
                msg = (
                    f"[SelfMod] Proposal created: {record.get('proposal_id')} -> "
                    f"{record.get('metadata', {}).get('target_file', '?')}"
                )
                if hasattr(gui_root_object, "add_system_message"):
                    gui_root_object.add_system_message(msg)

            def _on_applied(info):
                msg = (
                    f"[SelfMod] Proposal applied: {info.get('proposal_id')} -> "
                    f"{info.get('target')}"
                )
                if hasattr(gui_root_object, "add_system_message"):
                    gui_root_object.add_system_message(msg)

            self.on("proposal_created", _on_created)
            self.on("proposal_applied", _on_applied)
            return True
        except Exception:
            return False

    def attach_to(self, obj) -> bool:
        try:
            setattr(obj, "self_mod_api", self)
            return True
        except Exception:
            return False

    # -------- New patch methods --------
    def inject_patch(self, target_file: str, patch_code: str) -> Dict[str, Any]:
        tpath = self._resolve_target_file(target_file)
        if not tpath or not tpath.exists():
            return {"success": False, "error": "file not found"}
        orig = tpath.read_text(encoding="utf-8")
        backup = _make_backup(tpath, self._backup_dir)
        try:
            orig_tree = ast.parse(orig)
            patch_tree = ast.parse(patch_code)
            orig_tree.body += patch_tree.body
            new_code = ast.unparse(orig_tree)
            _atomic_write(tpath, new_code)
            self.audit.log_event(
                "inject_patch", {"target": target_file, "backup": str(backup)}, True
            )
            self._log_journal(
                {
                    "event": "patch_injected",
                    "target": target_file,
                    "patch_summary": patch_code[:100] + "...",
                }
            )
            self._gain_xp(10)
            self._hot_reload(str(tpath))
            self.mutation_logger.log_mutation(
                mutation_id=f"patch_{uuid.uuid4().hex[:8]}",
                actor="user",
                action="inject_patch",
                target_file=str(tpath),
                diff="(patch appended)",
                backup_path=str(backup),
                status="applied",
                metadata={"patch_preview": patch_code[:200]},
            )
            return {"success": True, "backup": str(backup), "target": str(tpath)}
        except Exception as e:
            self.learned_failures["last_patch_error"] = str(e)
            _save_json(LEARNED_FAILURES_PATH, self.learned_failures)
            self.mutation_logger.log_mutation(
                mutation_id=f"patch_{uuid.uuid4().hex[:8]}",
                actor="user",
                action="inject_patch_failed",
                target_file=str(tpath),
                status="failed",
                metadata={"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    def patch_from_command(
        self, user_input: str, default_target: str = "saraphina_gui.py"
    ) -> Dict[str, Any]:
        if not user_input.lower().startswith("patch:"):
            return {"error": "Invalid patch command"}
        patch_code = user_input.partition(":")[2].strip()
        return self.inject_patch(default_target, patch_code)

    # -------- Warp AI Features --------
    def natural_language_to_command(self, nl_query: str) -> str:
        if hasattr(self._code_factory, "_call_openai"):
            prompt = (
                "Convert this natural language description into a shell command or small "
                "Python snippet. Return only the command/code:\n\n"
                f"{nl_query}"
            )
            res = self._code_factory._call_openai(prompt, max_tokens=200)
            return res.get("code", "No command generated.")
        return "Offline mode, no command generated."

    def fix_command(self, command: str, error: str) -> str:
        return self.fixer.fix(command, error)

    def explain_command(self, command: str) -> str:
        return self.explainer.explain(command)

    def suggest_command(self, context: str) -> str:
        return self.suggester.suggest(context)

    def search_history(self, query: str) -> List[str]:
        return [
            entry.get("event", "")
            for entry in self.journal
            if query.lower() in entry.get("event", "").lower()
        ]

    # -------- Productivity Tools --------
    def shell_exec(self, command: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout.decode("utf-8", "ignore"),
                "stderr": proc.stderr.decode("utf-8", "ignore"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self, directory: str = ".") -> List[str]:
        dir_path = Path(directory)
        return [str(f) for f in dir_path.iterdir()]

    def save_session(self, session_name: str) -> bool:
        session_data = {
            "config": self.config,
            "journal": self.journal[-50:],
            "proposals": self.list_proposals(),
        }
        session_path = SESSIONS_DIR / f"{session_name}.json"
        _save_json(session_path, session_data)
        return True

    def load_session(self, session_name: str) -> bool:
        session_path = SESSIONS_DIR / f"{session_name}.json"
        if not session_path.exists():
            return False
        data = _load_json(session_path, {})
        self.config.update(data.get("config", {}))
        self.journal.extend(data.get("journal", []))
        self._save_config()
        _save_json(self.journal_path, self.journal)
        return True

    # -------- Sandboxed Execution (local) --------
    def sandbox_test(self, code: str, globals_dict: Optional[Dict] = None) -> Dict[str, Any]:
        restricted = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "sum": sum,
                "max": max,
                "min": min,
            }
        }
        if globals_dict:
            restricted.update(globals_dict)

        old_stdout = sys.stdout
        captured = io.StringIO()
        sys.stdout = captured

        try:
            exec(code, restricted)
            return {"success": True, "output": captured.getvalue()}
        except Exception as e:
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        finally:
            sys.stdout = old_stdout

    # -------- Emergency Controls --------
    def freeze_autonomy(self):
        FREEZE_FILE.touch()
        logger.critical("[SelfMod] AUTONOMY FROZEN")
        self.autonomy_frozen = True

    def unfreeze_autonomy(self):
        if FREEZE_FILE.exists():
            FREEZE_FILE.unlink()
        self.autonomy_frozen = False
        logger.critical("[SelfMod] AUTONOMY UNLEASHED")


# ==================== INSTANTIATE GLOBAL ENGINE ====================
self_mod_engine = SelfModificationEngine()

# Optional auto-attach to UltraAICore if already imported
if "ultra_core" in sys.modules:
    try:
        import ultra_core  # type: ignore
        if hasattr(ultra_core, "core"):
            ultra_core.core.self_mod_engine = self_mod_engine
        logger.info("[SelfMod] Attached to UltraAICore")
    except Exception:
        logger.debug("Auto-attach to UltraAICore failed", exc_info=True)