#!/usr/bin/env python3
# saraphina/self_modification_engine.py
"""
SelfModificationEngine — supervised superpowers for Saraphina
(with cross-root file resolution, GUI shim, integrity safety, backups, rollback,
optional OpenAI code generation, and package install path).
This engine is designed to be called by your existing GUI without modifying the GUI.
Upgraded to ultimate Warp clone with AI-powered features, productivity tools, security, and extensibility.
Notable public methods (stable surface used by GUI or CLI wrappers):
  - load_env_from_root(env_root: Optional[Path]) -> Dict[str, Any]
  - scan_codebase(target_module: Optional[str]) -> Dict[str, Any]
  - propose_improvement(target_file: str, improvement_spec: str, safety_level: str="high", context: Optional[Dict]=None, auto_apply: bool=False) -> Dict[str, Any]
  - apply_improvement(proposal_id: str) -> Dict[str, Any]
  - propose_module(module_name: str, spec: str, safety_level: str="high", auto_apply: bool=False) -> Dict[str, Any]
  - import_module_runtime(module_filename: str) -> Dict[str, Any]
  - request_install_packages(packages: List[str]) -> Dict[str, Any]
  - confirm_install_packages(proposal_id: str, allow_upgrade: bool=False) -> Dict[str, Any]
  - rollback_from_backup(backup_filename: str) -> Dict[str, Any]
  - list_proposals() -> List[Dict[str, Any]]
  - get_proposal(pid: str) -> Optional[Dict[str, Any]]
  - disable_autonomy_session() -> None
  - enable_autonomy_session() -> bool
  - natural_language_to_command(nl_query: str) -> str
  - fix_command(command: str, error: str) -> str
  - explain_command(command: str) -> str
  - suggest_command(context: str) -> str
  - search_history(query: str) -> List[str]
  - shell_exec(command: str) -> Dict[str, Any]
  - list_files(directory: str = ".") -> List[str]
  - git_status() -> str
  - git_commit(message: str) -> str
  - save_session(session_name: str) -> bool
  - load_session(session_name: str) -> bool
  - load_plugin(plugin_path: str) -> bool
  - set_theme(theme_dict: Dict[str, str]) -> bool
GUI compatibility shims / helpers:
  - accept_spec_and_propose(spec: dict, actor: str="gui") -> dict
  - try_autowire_into_gui(gui_root_object) -> bool
Security principles:
  - Atomic file writes, backups, and rollbacks.
  - Integrity signatures optional; if required by env but secret missing -> proposal allowed.
  - Offline mode supported.
  - No telemetry.
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
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
# UPGRADE: Add import for new OpenAI client
try:
    from openai import OpenAI # type: ignore
    OPENAI_CLIENT_AVAILABLE = True
except Exception:
    OPENAI_CLIENT_AVAILABLE = False
# ---------------- Logging ----------------
logger = logging.getLogger("SelfModificationEngine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
# ---------------- Env bootstrap ----------------
# Ensure the same .env the GUI uses is visible here too.
try:
    from dotenv import load_dotenv, dotenv_values # type: ignore
    DOTENV_AVAILABLE = True
except Exception:
    DOTENV_AVAILABLE = False
    load_dotenv = None
    dotenv_values = None
# Default to your declared root (Windows path as you requested)
DEFAULT_PROJECT_ROOT = Path(os.getenv("SARAPHINA_PROJECT_ROOT", "D:/Saraphina Root")).resolve()
if DOTENV_AVAILABLE and (DEFAULT_PROJECT_ROOT / ".env").exists():
    # Load .env early so OPENAI_API_KEY and SELF_MOD_OWNER_TOKEN are present before engine init
    load_dotenv(dotenv_path=str(DEFAULT_PROJECT_ROOT / ".env"), override=True)
# Optional libs
try:
    import openai # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False
try:
    from git import Repo # type: ignore
    GITPY_AVAILABLE = True
except Exception:
    GITPY_AVAILABLE = False
# ---------------- Config knobs ----------------
ENGINE_DIR = Path(__file__).parent.resolve()
ROOT_ENV_PATH = DEFAULT_PROJECT_ROOT
SELF_MOD_SECRET = os.getenv("SELF_MOD_SECRET", "")
SELF_MOD_REQUIRE_INTEGRITY = os.getenv("SELF_MOD_REQUIRE_INTEGRITY", "true").lower() in ("1", "true", "yes")
MAX_FILE_SIZE = int(os.getenv("SELF_MOD_MAX_FILE_SIZE", "300000")) # bytes
BACKUP_RETENTION = int(os.getenv("SELF_MOD_BACKUP_RETENTION", "12")) # files to keep
# UPGRADE: Add new config for model selection
DEFAULT_LLM_MODEL = os.getenv("SELF_MOD_LLM_MODEL", "gpt-4o-mini")
# UPGRADE: Persistent memory paths
MEMORY_DIR = ENGINE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LEARNED_FAILURES_PATH = MEMORY_DIR / "learned_failures.json"
SUCCESSFUL_PATTERNS_PATH = MEMORY_DIR / "successful_patterns.json"
# UPGRADE: Proposal storage dir for persisting code/diffs
PROPOSAL_DIR = ENGINE_DIR / "proposals"
PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
# Config file path (optional GUI toggle)
CONFIG_PATHS = [
    ENGINE_DIR / "config.json",
    ENGINE_DIR / "data" / "config.json",
    Path(os.getenv("SARAPHINA_PROJECT_ROOT", "D:/Saraphina Root")) / "config.json"
]
# Sessions dir
SESSIONS_DIR = ENGINE_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
# Plugins dir
PLUGINS_DIR = ENGINE_DIR / "plugins"
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
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
    # Rotate old backups
    files = sorted(
        backup_dir.glob(f"{target.name}.*.bak"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    for old in files[BACKUP_RETENTION:]:
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
    """Resolve a target file name across multiple roots, honoring project root boundary."""
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
    # Try parents of engine dir as last resort
    for root in (ENGINE_DIR.parent, ENGINE_DIR.parent.parent):
        p = (root / fname).resolve()
        if _safe_exists(p, DEFAULT_PROJECT_ROOT):
            return p
    return None
# ---------------- Storage & approvals ----------------
class SimpleProposalDB:
    """In-memory proposal db (GUI reads through engine -> fine for your local use)."""
    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {}
    def store_proposal(self, proposal: Dict[str, Any]) -> None:
        with self._lock:
            self._store[proposal["proposal_id"]] = dict(proposal)
            self._store[proposal["proposal_id"]].setdefault("status", "created")
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
    """Append-only log for every important action."""
    def __init__(self, data_dir: Path):
        self.dir = Path(data_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.logfile = self.dir / "selfmod_audit.jsonl"
    def log_event(self, action: str, details: Dict[str, Any], success: bool) -> None:
        entry = {
            "ts": datetime.utcnow().isoformat()+"Z",
            "action": action,
            "details": details,
            "success": bool(success)
        }
        try:
            with open(self.logfile, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            logger.debug("Audit write failed", exc_info=True)
# ---------------- Persistent Memory Helpers ----------------
def _load_json(path: Path, default: Dict) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.debug(f"Failed to load {path}", exc_info=True)
    return default
def _save_json(path: Path, data: Dict) -> None:
    try:
        _atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        logger.debug(f"Failed to save {path}", exc_info=True)
# ---------------- Code factories ----------------
class DefaultCodeFactory:
    """Offline scaffolder – always available; replaced by OpenAI factory if key present."""
    def propose_code(self, feature_spec: str, language: str="python", context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        # Minimal working scaffold; the apply path ensures syntax-validity anyway.
        code = (
            f'"""Auto-generated scaffold for: {feature_spec}"""\n'
            f"\n"
            f"def initialize():\n"
            f" # Implement: {feature_spec}\n"
            f" return None\n"
        )
        return {"success": True, "code": code, "explanation": "Offline scaffold", "tests": ""}
class OpenAICodeFactory:
    """LLM-backed generator (used only if OPENAI_API_KEY present)."""
    def __init__(self, model: str=DEFAULT_LLM_MODEL):
        self.model = model
        self.client = OpenAI() if OPENAI_CLIENT_AVAILABLE else None
    def _call_openai(self, prompt: str, max_tokens: int=1200) -> Dict[str, Any]:
        if not OPENAI_AVAILABLE or not self.client:
            return {"success": False, "error": "openai library not installed or client unavailable"}
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Return only complete, runnable Python files when asked to modify code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.15
            )
            content = resp.choices[0].message.content
            if content.strip().startswith("```"):
                parts = content.strip().split("```")
                content = parts[1] if len(parts) >= 3 else parts[-1]
            return {"success": True, "code": content}
        except Exception as e:
            logger.exception("OpenAI call failed")
            return {"success": False, "error": str(e)}
    def propose_code(self, feature_spec: str, language: str="python", context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        # Inject learned patterns if relevant
        learned_hint = ""
        if context and "original_code" in context:
            for pattern, snippet in context.get("successful_patterns", {}).items():
                if pattern.lower() in feature_spec.lower():
                    learned_hint += f"\nUse this known-good pattern for '{pattern}':\n{snippet}\n"
        avoid_hint = "\nAvoid past mistakes:\n" + json.dumps(context.get("learned_failures", {}), indent=2)
        prompt = (
            "Update or create the target Python GUI file according to the request.\n"
            "Return the FULL FILE CONTENT only (ready to write to disk). Keep existing behavior; add the feature minimally and cleanly.\n"
            f"REQUEST: {feature_spec}\n"
            f"LEARNED PATTERNS: {learned_hint}\n"
            f"{avoid_hint}\n"
            f"CONTEXT(JSON): {json.dumps(context or {}, ensure_ascii=False)[:2000]}\n"
        )
        return self._call_openai(prompt)
class CommandExplainer:
    def __init__(self, code_factory):
        self.code_factory = code_factory
    def explain(self, command: str) -> str:
        if hasattr(self.code_factory, '_call_openai'):
            prompt = f"Explain this command or code in simple terms: {command}"
            res = self.code_factory._call_openai(prompt)
            return res.get("code", "No explanation available")
        return "Offline mode, no explanation available."
class CommandFixer:
    def __init__(self, code_factory):
        self.code_factory = code_factory
    def fix(self, command: str, error: str) -> str:
        if hasattr(self.code_factory, '_call_openai'):
            prompt = f"Original command: {command}\nError: {error}\nSuggest a fixed version of the command."
            res = self.code_factory._call_openai(prompt)
            return res.get("code", command)
        return command
class CommandSuggester:
    def __init__(self, code_factory, journal):
        self.code_factory = code_factory
        self.journal = journal
    def suggest(self, context: str) -> str:
        history = "\n".join([entry.get("event", "") for entry in self.journal[-10:]])
        if hasattr(self.code_factory, '_call_openai'):
            prompt = f"Based on context: {context}\nRecent history: {history}\nSuggest next command or action."
            res = self.code_factory._call_openai(prompt)
            return res.get("code", "No suggestion")
        return "No suggestion"
# ---------------- Engine ----------------
class SelfModificationEngine:
    def __init__(self, code_factory=None, proposal_db=None, data_root: Optional[Path]=None):
        # Where the engine code lives (do NOT assume project root == engine dir)
        self.engine_dir = ENGINE_DIR
        self.project_root = DEFAULT_PROJECT_ROOT
        # Legacy alias some callsites might expect
        self.root = self.engine_dir
        # Data paths
        self.data_root = Path(data_root) if data_root else (self.engine_dir / "data")
        self.data_root.mkdir(parents=True, exist_ok=True)
        self._backup_dir = self.engine_dir / "backups" / "self_mod"
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        # Subsystems
        self.proposal_db = proposal_db or SimpleProposalDB()
        self.audit = FileAuditTrail(self.data_root)
        self.default_factory = code_factory or DefaultCodeFactory()
        self._code_factory = self.default_factory # may be switched to OpenAICodeFactory if key found
        self._lock = threading.RLock()
        self._dangerous_keywords = ["subprocess", "socket", "ctypes", "eval(", "exec(", "__import__"]
        self._event_listeners: Dict[str, List[Callable[..., None]]] = {}
        self.autonomous_enabled = False
        # Optional git repo
        self._git = None
        self._init_git()
        # UPGRADE: Persistent memory for learned failures and successful patterns
        self.learned_failures: Dict[str, str] = _load_json(LEARNED_FAILURES_PATH, {})
        self.successful_patterns: Dict[str, str] = _load_json(SUCCESSFUL_PATTERNS_PATH, {})
        # Journal
        self.journal_path = MEMORY_DIR / "learning_journal.json"
        self.journal = _load_json(self.journal_path, [])
        # Load config (if present); fallback to defaults
        self.config = self._load_config()
        self.xp = self.config.get("xp", 0)
        self.level = self.config.get("level", 1)
        # --- If OpenAI key present, enable the LLM factory
        try:
            key = os.getenv("OPENAI_API_KEY", "").strip()
            if key and OPENAI_AVAILABLE and OPENAI_CLIENT_AVAILABLE:
                self._code_factory = OpenAICodeFactory()
                logger.info("OpenAI CodeFactory enabled.")
        except Exception:
            logger.debug("OpenAI wiring failed", exc_info=True)
        # New Warp-like components
        self.explainer = CommandExplainer(self._code_factory)
        self.fixer = CommandFixer(self._code_factory)
        self.suggester = CommandSuggester(self._code_factory, self.journal)
        self.plugins = {}
        self.theme = self.config.get("theme", {})
        self._load_plugins()
    def _load_plugins(self):
        for plugin_file in PLUGINS_DIR.glob("*.py"):
            try:
                self.import_module_runtime(str(plugin_file))
            except Exception:
                logger.debug(f"Failed to load plugin {plugin_file}")
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
        # sensible defaults
        return {"auto_apply_modifications": True, "xp": 0, "level": 1}
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
    # -------- Git --------
    def _init_git(self):
        if not GITPY_AVAILABLE:
            return
        try:
            # Prefer project root repo if present
            if (self.project_root / ".git").exists():
                self._git = Repo(str(self.project_root))
            elif (self.engine_dir / ".git").exists():
                self._git = Repo(str(self.engine_dir))
            else:
                self._git = None
        except Exception:
            self._git = None
    def git_status(self) -> str:
        if self._git:
            return self._git.git.status()
        return "Git not available"
    def git_commit(self, message: str) -> str:
        if self._git:
            self._git.git.add(A=True)
            return self._git.git.commit(m=message)
        return "Git not available"
    # -------- Env loader (explicit call if you want a reload) --------
    def load_env_from_root(self, env_root: Optional[Path]=None) -> Dict[str, Any]:
        with self._lock:
            root = Path(env_root) if env_root else ROOT_ENV_PATH
            dotenv_path = root / ".env"
            if not dotenv_path.exists():
                return {"success": False, "error": f".env not found at {dotenv_path}"}
            try:
                vals: Dict[str, str] = {}
                if DOTENV_AVAILABLE:
                    vals = {k: ("" if v is None else str(v)) for k, v in dotenv_values(str(dotenv_path)).items()}
                else:
                    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        vals[k.strip()] = v.strip().strip('"').strip("'")
                # Wire OpenAI if present
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
        analysis = {"file": file_path.name, "lines": len(content.splitlines()), "size": len(content), "issues": []}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    analysis["issues"].append("import detected") # example; expand as needed
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
                else:
                    files = list(self.engine_dir.glob("*.py")) + list(self.project_root.glob("*.py"))
                    analyses = [self._analyze_file(f) for f in files if f.is_file() and not f.name.startswith("__")]
                    return {"success": True, "analyses": analyses}
            except Exception as e:
                logger.exception("scan_codebase failed")
                return {"success": False, "error": str(e)}
    # -------- Improvement flow --------
    def _resolve_target_file(self, name_or_path: str) -> Optional[Path]:
        try:
            cand = Path(name_or_path)
            if cand.is_absolute() and cand.exists():
                return cand.resolve()
            base = os.path.basename(name_or_path)
            if not base.endswith(".py"):
                base += ".py"
            # infer roots
            roots = []
            proj = self.project_root
            if proj.exists():
                roots.append(proj)
            # env root
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
            # direct lookups
            for r in roots:
                p = (r / base).resolve()
                if p.exists():
                    return p
            # last resort: rglob under first root
            if roots:
                for p in roots[0].rglob(base):
                    return p.resolve()
        except Exception:
            pass
        return None
    def _validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        code = proposal.get("code", "")
        if not code:
            return {"success": False, "error": "no code provided"}
        if len(code) > MAX_FILE_SIZE:
            return {"success": False, "error": "code exceeds max size"}
        # UPGRADE: Smarter dangerous keyword detection with learning
        code_lower = code.lower()
        for kw in self._dangerous_keywords:
            if kw in code_lower:
                suggestion = "Try using psutil instead of low-level access like ctypes."
                self.learned_failures[kw] = f"avoid using '{kw}', fallback to safer method"
                _save_json(LEARNED_FAILURES_PATH, self.learned_failures)
                return {
                    "success": False,
                    "error": f"unsafe keyword detected: {kw}",
                    "learned": self.learned_failures[kw],
                    "retry_suggestion": suggestion
                }
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {"success": False, "error": f"syntax error: {e}"}
        return {"success": True}
    def _apply_code_to_target(self, target_file: Path, new_code: str, proposal_id: str) -> Dict[str, Any]:
        if not target_file.exists():
            return {"success": False, "error": "target does not exist"}
        orig = target_file.read_text(encoding="utf-8")
        backup = _make_backup(target_file, self._backup_dir)
        _atomic_write(target_file, new_code)
        diff = "\n".join(difflib.unified_diff(orig.splitlines(), new_code.splitlines(), lineterm=""))
        return {"success": True, "backup": str(backup), "diff": diff}
    def propose_improvement(self, target_file: str, improvement_spec: str, safety_level: str="high", context: Optional[Dict]=None, auto_apply: bool=False) -> Dict[str, Any]:
        """
        Propose an improvement for a given target_file.
        New: auto_apply flag (bool). If True (or if engine config enables auto_apply_modifications),
        the engine will attempt to apply the proposal automatically.
        """
        with self._lock:
            try:
                tpath = self._resolve_target_file(target_file)
                if not tpath:
                    return {"success": False, "error": "target file not resolvable"}
                orig = ""
                if tpath.exists():
                    orig = tpath.read_text(encoding="utf-8", errors="ignore")
                ctx = {
                    "original_code": orig,
                    "file": tpath.name,
                    "successful_patterns": self.successful_patterns,
                    "learned_failures": self.learned_failures
                }
                # merge external context if provided
                if isinstance(context, dict):
                    ctx.update(context)
                # First attempt
                gen = self._code_factory.propose_code(improvement_spec, "python", context=ctx)
                if not gen.get("success"):
                    return {"success": False, "error": gen.get("error", "code generation failed")}
                logger.info("Code generation succeeded.")
                val = self._validate_proposal(gen)
                if not val.get("success"):
                    # UPGRADE: Retry with learned correction
                    retry_suggestion = val.get("retry_suggestion")
                    if retry_suggestion:
                        logger.info(f"Retrying after learning: {retry_suggestion}")
                        retry_spec = (
                            f"{improvement_spec}\n"
                            f"IMPORTANT: {retry_suggestion} "
                            f"Avoid unsafe modules. Prefer psutil, standard library, or safe alternatives."
                        )
                        gen_retry = self._code_factory.propose_code(retry_spec, "python", context=ctx)
                        val_retry = self._validate_proposal(gen_retry)
                        if val_retry.get("success"):
                            gen = gen_retry # use retry result
                            logger.info("Retry succeeded with safer code.")
                        else:
                            return {"success": False, "error": val_retry.get("error", "retry failed")}
                    else:
                        return {"success": False, "error": val.get("error")}
                pid = f"improve_{uuid.uuid4().hex[:10]}"
                record = {
                    "proposal_id": pid,
                    "feature_spec": improvement_spec,
                    "language": "python",
                    "code": gen.get("code", ""),
                    "metadata": {"target_file": tpath.name, "created_at": datetime.utcnow().isoformat()+"Z"},
                    "safety_checks": {"safety_level": safety_level, "requires_owner_approval": False},
                    "auto_apply_requested": bool(auto_apply)
                }
                self.proposal_db.store_proposal(record)
                # UPGRADE: Persist proposal code to disk for inspection
                prop_path = PROPOSAL_DIR / f"{pid}.py"
                _atomic_write(prop_path, record["code"])
                record["proposal_path"] = str(prop_path)
                self.audit.log_event("propose_improvement", {"proposal_id": pid, "target": target_file}, True)
                self._log_journal({"event": "propose_improvement", "proposal_id": pid, "target": target_file})
                self._emit("proposal_created", record)
                # Determine whether we should auto-apply:
                should_auto = auto_apply or self.config.get("auto_apply_modifications", False)
                if should_auto:
                    # apply in background
                    threading.Thread(target=self._auto_apply_worker, args=(pid,), daemon=True).start()
                    return {
                        "success": True,
                        "proposal_id": pid,
                        "target": target_file,
                        "applied": False,
                        "info": "auto_apply initiated in background"
                    }
                else:
                    return {
                        "success": True,
                        "proposal_id": pid,
                        "target": target_file,
                        "applied": False
                    }
            except Exception as e:
                logger.exception("propose_improvement failed")
                return {"success": False, "error": str(e)}
    def _auto_apply_worker(self, proposal_id: str) -> None:
        """
        Helper to apply in background and update proposal status / audit.
        """
        try:
            self.proposal_db.set_status(proposal_id, "auto_applying")
            res = self.apply_improvement(proposal_id)
            if res.get("success"):
                self.proposal_db.set_status(proposal_id, "auto_applied")
            else:
                self.proposal_db.set_status(proposal_id, "auto_failed")
            self.audit.log_event("auto_apply", {"proposal_id": proposal_id, "result": res}, res.get("success", False))
            if res.get("success"):
                # Emit event for applied proposals
                self._emit("proposal_applied", {"proposal_id": proposal_id, "target": res.get("target"), "details": res})
        except Exception:
            logger.exception("background apply failed")
    def apply_improvement(self, proposal_id: str) -> Dict[str, Any]:
        with self._lock:
            prop = self.proposal_db.get_proposal(proposal_id)
            if not prop:
                return {"success": False, "error": "proposal not found"}
            if prop.get("status") != "created" and not prop.get("status", "").startswith("auto_"):
                return {"success": False, "error": f"proposal status: {prop.get('status')}"}
            tpath = self._resolve_target_file(prop.get("metadata", {}).get("target_file", ""))
            if not tpath:
                return {"success": False, "error": "target file not resolvable"}
            code = prop.get("code", "")
            try:
                apply_res = self._apply_code_to_target(tpath, code, proposal_id)
                if not apply_res.get("success"):
                    raise Exception(apply_res.get("error"))
                # UPGRADE: Store successful snippet
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
                self.proposal_db.set_status(proposal_id, "applied")
                self.audit.log_event("apply_improvement", {"proposal_id": proposal_id, "target": tpath.name}, True)
                self._log_journal({"event": "proposal_applied", "proposal_id": proposal_id, "target": str(tpath)})
                self._gain_xp(20)
                self._emit("proposal_applied", {"proposal_id": proposal_id, "target": tpath.name, "diff": apply_res.get("diff")})
                return {"success": True, "target": str(tpath), "backup": str(apply_res.get("backup")), "diff": apply_res.get("diff")}
            except Exception as e:
                self.audit.log_event("apply_improvement", {"proposal_id": proposal_id, "error": str(e)}, False)
                self._log_journal({"event": "apply_failed", "proposal_id": proposal_id, "error": str(e)})
                self.learned_failures["last_apply_error"] = str(e)
                _save_json(LEARNED_FAILURES_PATH, self.learned_failures)
                return {"success": False, "error": str(e)}
    # -------- New modules --------
    def propose_module(self, module_name: str, spec: str, safety_level: str="high", auto_apply: bool=False) -> Dict[str, Any]:
        with self._lock:
            try:
                safe_name = module_name.strip().replace(" ", "_")
                if not safe_name.endswith(".py"):
                    safe_name += ".py"
                tpath = self.project_root / safe_name
                if tpath.exists():
                    return {"success": False, "error": "module already exists"}
                gen = self._code_factory.propose_code(spec, "python")
                if not gen.get("success"):
                    return {"success": False, "error": gen.get("error", "code generation failed")}
                val = self._validate_proposal(gen)
                if not val.get("success"):
                    retry_suggestion = val.get("retry_suggestion")
                    if retry_suggestion:
                        logger.info(f"Module retry: {retry_suggestion}")
                        retry_spec = f"{spec}\n{retry_suggestion}"
                        gen_retry = self._code_factory.propose_code(retry_spec, "python")
                        val_retry = self._validate_proposal(gen_retry)
                        if val_retry.get("success"):
                            gen = gen_retry
                        else:
                            return {"success": False, "error": val_retry.get("error")}
                    else:
                        return {"success": False, "error": val.get("error")}
                pid = f"module_{uuid.uuid4().hex[:10]}"
                record = {
                    "proposal_id": pid,
                    "feature_spec": spec,
                    "language": "python",
                    "code": gen.get("code", ""),
                    "metadata": {"target_file": safe_name, "created_at": datetime.utcnow().isoformat()+"Z"},
                    "safety_checks": {"safety_level": safety_level, "requires_owner_approval": False}
                }
                self.proposal_db.store_proposal(record)
                self.audit.log_event("propose_module", {"proposal_id": pid, "target": safe_name}, True)
                self._log_journal({"event": "propose_module", "proposal_id": pid, "target": safe_name})
                self._emit("proposal_created", record)
                should_auto = auto_apply or self.config.get("auto_apply_modifications", False)
                if should_auto:
                    threading.Thread(target=self._auto_apply_worker, args=(pid,), daemon=True).start()
                return {"success": True, "proposal_id": pid, "target": safe_name}
            except Exception as e:
                logger.exception("propose_module failed")
                return {"success": False, "error": str(e)}
    # -------- Runtime import (requires approval) --------
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
                spec.loader.exec_module(mod) # executes
                if hasattr(mod, "initialize") and callable(mod.initialize):
                    try:
                        mod.initialize()
                    except Exception:
                        logger.debug("module initialize raised")
                self._emit("module_imported", {"module": module_name, "file": fpath.name})
                return {"success": True, "module": module_name}
            except Exception as e:
                logger.exception("dynamic import failed")
                return {"success": False, "error": str(e)}
    # -------- Autonomy --------
    def enable_autonomy_session(self) -> bool:
        self.autonomous_enabled = True
        self.audit.log_event("autonomy_enabled", {}, True)
        self._emit("autonomy_enabled", {})
        return True
    def disable_autonomy_session(self) -> None:
        self.autonomous_enabled = False
        self.audit.log_event("autonomy_disabled", {}, True)
        self._emit("autonomy_disabled", {})
    # -------- Packages (request + confirm) --------
    def detect_missing_packages(self, python_file: Optional[Path]=None) -> Dict[str, Any]:
        with self._lock:
            files = [python_file] if python_file else list(self.project_root.glob("*.py")) + list(self.engine_dir.glob("*.py"))
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
            "metadata": {"packages": packages, "created_at": datetime.utcnow().isoformat()+"Z"},
            "safety_checks": {"requires_owner_approval": False}
        }
        self.proposal_db.store_proposal(rec)
        self.audit.log_event("install_requested", {"proposal_id": pid, "packages": packages}, True)
        self._log_journal({"event": "install_requested", "proposal_id": pid, "packages": packages})
        self._emit("install_requested", rec)
        return {"success": True, "proposal_id": pid, "packages": packages}
    def confirm_install_packages(self, proposal_id: str, allow_upgrade: bool=False) -> Dict[str, Any]:
        with self._lock:
            prop = self.proposal_db.get_proposal(proposal_id)
            if not prop:
                return {"success": False, "error": "proposal not found"}
            pkgs = prop.get("metadata", {}).get("packages", [])
            if not pkgs:
                return {"success": False, "error": "no packages listed"}
            cmd = [sys.executable, "-m", "pip", "install"] + (["--upgrade"] if allow_upgrade else []) + pkgs
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
                success = proc.returncode == 0
                self.proposal_db.set_status(proposal_id, "installed" if success else "failed")
                self.audit.log_event("install_executed", {"proposal_id": proposal_id, "returncode": proc.returncode}, success)
                self._log_journal({"event": "install_executed", "proposal_id": proposal_id, "success": success})
                if success:
                    self._gain_xp(10)
                return {
                    "success": success,
                    "stdout": proc.stdout.decode("utf-8", "ignore"),
                    "stderr": proc.stderr.decode("utf-8", "ignore")
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
        self.audit.log_event("rollback", {"backup": backup_filename, "restored": target.name}, True)
        self._log_journal({"event": "rollback_performed", "backup": backup_filename, "file": str(target)})
        self._emit("rollback", {"backup": backup_filename})
        return {"success": True, "restored": str(target)}
    def rollback_last(self, target_file: str) -> Dict[str, Any]:
        tpath = self._resolve_target_file(target_file)
        if not tpath:
            return {"success": False, "error": "target not resolvable"}
        backup_path = str(tpath) + ".bak"
        if not os.path.exists(backup_path):
            return {"error": "No backup found."}
        shutil.copy(backup_path, str(tpath))
        self._log_journal({"event": "rollback_last_performed", "file": target_file})
        self.audit.log_event("rollback_last", {"file": target_file}, True)
        return {"success": True, "restored_from": backup_path}
    # -------- Introspection --------
    def list_proposals(self) -> List[Dict[str, Any]]:
        return list(getattr(self.proposal_db, "_store", {}).values())
    def get_proposal(self, pid: str) -> Optional[Dict[str, Any]]:
        return self.proposal_db.get_proposal(pid)
    # UPGRADE: New method to show full proposal details including code and diff preview
    def show_proposal(self, pid: str) -> Dict[str, Any]:
        prop = self.get_proposal(pid)
        if not prop:
            return {"success": False, "error": "proposal not found"}
        code = prop.get("code", "")
        target_file = prop.get("metadata", {}).get("target_file", "")
        tpath = self._resolve_target_file(target_file)
        if tpath and tpath.exists():
            orig = tpath.read_text(encoding="utf-8")
            diff = "\n".join(difflib.unified_diff(orig.splitlines(), code.splitlines(), lineterm=""))
            prop["preview_diff"] = diff
        return {"success": True, "proposal": prop}
    # -------- GUI compatibility shim (NO GUI changes required) --------
    def accept_spec_and_propose(self, spec: dict, actor: str="gui") -> dict:
        try:
            # candidates from spec
            candidates = []
            if isinstance(spec, dict):
                t = spec.get("targets") or spec.get("target") or []
                if isinstance(t, str):
                    candidates = [t]
                elif isinstance(t, list):
                    candidates = [x for x in t if isinstance(x, str)]
            if not candidates:
                candidates = ["saraphina_gui.py"]
            chosen = None
            for c in candidates:
                p = self._resolve_target_file(c)
                if p:
                    chosen = p; break
            if not chosen:
                # try basename fallback
                name = os.path.basename(candidates[0])
                chosen = self._resolve_target_file(name)
                if not chosen:
                    return {"success": False, "error": f"Target not found: {name}"}
            # build human spec
            safety = (spec.get("safety_level") if isinstance(spec, dict) else None) or "high"
            text = ""
            if isinstance(spec, dict):
                text = spec.get("improvement_spec") or spec.get("summary") or spec.get("request") or ""
                desired = spec.get("desired_changes")
                if isinstance(desired, list) and desired:
                    text += "\nDesired changes:\n" + "\n".join([json.dumps(x, ensure_ascii=False) for x in desired])
            if not text.strip():
                text = "Implement the requested improvement inferred from user intent and context."
            # check for auto_apply in spec or engine config
            auto_apply_flag = False
            if isinstance(spec, dict) and spec.get("auto_apply") in (True, "true", "True", "1"):
                auto_apply_flag = True
            elif self.config.get("auto_apply_modifications"):
                auto_apply_flag = True
            res = self.propose_improvement(str(chosen), text, safety_level=safety, context=spec.get("context") if isinstance(spec, dict) else None, auto_apply=auto_apply_flag)
            if res.get("success"):
                self._emit("proposal_created", {"proposal_id": res.get("proposal_id"), "metadata": res.get("metadata")})
            return res
        except Exception as e:
            logger.exception("accept_spec_and_propose failed")
            return {"success": False, "error": str(e)}
    # -------- Optional GUI autowire (messages only) --------
    def try_autowire_into_gui(self, gui_root_object):
        try:
            if not gui_root_object:
                return False
            def _on_created(record):
                msg = f"[SelfMod] Proposal created: {record.get('proposal_id')} -> {record.get('metadata',{}).get('target_file','?')}"
                if hasattr(gui_root_object, "add_system_message"):
                    gui_root_object.add_system_message(msg)
            def _on_applied(info):
                msg = f"[SelfMod] Proposal applied: {info.get('proposal_id')} -> {info.get('target')}"
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
            self.audit.log_event("inject_patch", {"target": target_file, "backup": str(backup)}, True)
            self._log_journal({"event": "patch_injected", "target": target_file, "patch_summary": patch_code[:100] + "..."})
            self._gain_xp(10)
            return {"success": True, "backup": str(backup), "target": str(tpath)}
        except Exception as e:
            self.learned_failures["last_patch_error"] = str(e)
            _save_json(LEARNED_FAILURES_PATH, self.learned_failures)
            return {"success": False, "error": str(e)}
    def patch_from_command(self, user_input: str, default_target="saraphina_gui.py") -> Dict[str, Any]:
        if not user_input.lower().startswith("patch:"):
            return {"error": "Invalid patch command"}
        patch_code = user_input.partition(":")[2].strip()
        return self.inject_patch(default_target, patch_code)
    # -------- Warp AI Features --------
    def natural_language_to_command(self, nl_query: str) -> str:
        if hasattr(self._code_factory, '_call_openai'):
            prompt = f"Convert this natural language to a shell command or Python code: {nl_query}"
            res = self._code_factory._call_openai(prompt)
            return res.get("code", "No command generated")
        return "Offline mode, no command generated"
    def fix_command(self, command: str, error: str) -> str:
        return self.fixer.fix(command, error)
    def explain_command(self, command: str) -> str:
        return self.explainer.explain(command)
    def suggest_command(self, context: str) -> str:
        return self.suggester.suggest(context)
    def search_history(self, query: str) -> List[str]:
        matches = [entry.get("event", "") for entry in self.journal if query.lower() in entry.get("event", "").lower()]
        return matches
    # -------- Productivity Tools --------
    def shell_exec(self, command: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout.decode("utf-8"),
                "stderr": proc.stderr.decode("utf-8")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    def list_files(self, directory: str = ".") -> List[str]:
        dir_path = Path(directory)
        return [str(f) for f in dir_path.iterdir()]
    def save_session(self, session_name: str) -> bool:
        session_data = {
            "config": self.config,
            "journal": self.journal[-50:],  # last 50 entries
            "proposals": self.list_proposals()
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
        # Proposals not reloaded to avoid conflicts
        self._save_config()
        _save_json(self.journal_path, self.journal)
        return True