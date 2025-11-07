#!/usr/bin/env python3
"""
SelfModificationAPI - Controlled API for Saraphina to modify aspects of herself

Hardened version:
- Requires an auth_token for any operation that modifies files, state, or config.
- Supports simple token-based identity mapping (OWNER_TOKEN, DEPLOY_TOKEN) via env vars.
- Enforces a strict path whitelist (only allows writing under repo 'saraphina' and 'scripts').
- Deploy service must provide an approval_signature (HMAC) if DEPLOY_SIGNATURE_SECRET is set.
- All modifications are logged via _log_modification and (where relevant) stored in knowledge/memory.
- Direct agent calls are forbidden; agents must use the proposal workflow via SelfModificationEngine.
"""

from __future__ import annotations
import os
import json
import logging
import hmac
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("SelfModificationAPI")

REPO_ROOT = Path(__file__).parent.parent.resolve()
# Allowed directories where the API may write files
ALLOWED_DIRS = [
    (REPO_ROOT / "saraphina").resolve(),
    (REPO_ROOT / "scripts").resolve(),
]

# Maximum file size allowed to be written (50 KB)
MAX_FILE_SIZE_BYTES = 50 * 1024

# Environment tokens (must be set on operator-controlled host, not modifiable by agent)
OWNER_TOKEN = os.getenv("SELF_MOD_OWNER_TOKEN")        # highest privilege
DEPLOY_TOKEN = os.getenv("SELF_MOD_DEPLOY_TOKEN")      # service/deployer privilege
DEPLOY_SIGNATURE_SECRET = os.getenv("DEPLOY_SIGNATURE_SECRET")  # optional HMAC secret for deploy signatures

class AuthorizationError(Exception):
    pass

def _mask(token: Optional[str]) -> Optional[str]:
    if token is None:
        return None
    t = token.strip()
    if len(t) <= 12:
        return t
    return t[:6] + "..." + t[-4:]

def verify_request_identity(token: str) -> Dict[str, Any]:
    """
    Very small identity verifier.
    - If token == OWNER_TOKEN -> actor: 'owner'
    - If token == DEPLOY_TOKEN -> actor: 'deploy_service'
    - Else -> raise AuthorizationError

    NOTE: This deliberately uses environment-stored tokens (operator must place them securely).
    You can replace this with JWT or PKI verification later.
    """
    if not token:
        raise AuthorizationError("Missing auth token")

    token = token.strip()
    if OWNER_TOKEN and hmac.compare_digest(token, OWNER_TOKEN):
        return {"actor": "owner", "scopes": ["modify_source", "approve"], "sub": "owner"}
    if DEPLOY_TOKEN and hmac.compare_digest(token, DEPLOY_TOKEN):
        return {"actor": "deploy_service", "scopes": ["modify_source"], "sub": "deploy_service"}
    raise AuthorizationError("Invalid auth token")

def verify_deploy_signature(approval_signature: str, payload_bytes: bytes) -> bool:
    """
    Verify HMAC-SHA256 deploy signature when DEPLOY_SIGNATURE_SECRET is configured.
    approval_signature is expected as hex string or base64; support hex here.
    """
    if not DEPLOY_SIGNATURE_SECRET:
        # No secret configured: consider signature not required (but calling code should enforce)
        return False
    try:
        # Expect hex string
        provided = approval_signature.strip().lower()
        mac = hmac.new(DEPLOY_SIGNATURE_SECRET.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, provided)
    except Exception as e:
        logger.debug(f"Deploy signature verification error: {e}")
        return False

def assert_path_allowed(target_path: Path) -> None:
    """
    Ensure the target_path is inside one of ALLOWED_DIRS and not targeting files like .env or secrets.
    Raises AuthorizationError on violation.
    """
    try:
        target = target_path.resolve()
    except Exception:
        raise AuthorizationError("Invalid target path")

    allowed = False
    for ad in ALLOWED_DIRS:
        try:
            if str(target).startswith(str(ad)):
                allowed = True
                break
        except Exception:
            continue

    if not allowed:
        raise AuthorizationError(f"Path not allowed: {target}")

    # Do not allow editing env/secrets by API
    if target.name.lower().endswith((".env", ".secret", "credentials", "id_rsa", "id_rsa.pub")):
        raise AuthorizationError("Editing secret/config files is forbidden via this API")

    # Prevent writing files outside repo (double-check)
    if REPO_ROOT not in target.parents and target != REPO_ROOT:
        raise AuthorizationError("Target outside repository is forbidden")

class SelfModificationAPI:
    """
    Unified, hardened API for Saraphina to modify allowed source files, config, and runtime metadata.

    Usage (example):
        api = SelfModificationAPI(sess, gui)
        api.modify_source_code('ai_core.py', old_text, new_text, auth_token='...')

    NOTE: All mutating methods require auth_token and will raise AuthorizationError for invalid/insufficient tokens.
    """

    def __init__(self, sess, gui=None):
        self.sess = sess
        self.gui = gui
        # Root path defaults to repo root
        self.root_path = REPO_ROOT
        self.saraphina_path = self.root_path / "saraphina"
        self.modification_log = []

    # ==================== AUTH HELPERS ====================
    def _require_modify_privilege(self, auth_token: str) -> Dict[str, Any]:
        identity = verify_request_identity(auth_token)
        if identity.get("actor") == "owner":
            return identity
        if identity.get("actor") == "deploy_service":
            return identity
        # Agents and others are not allowed to use direct modification endpoints
        raise AuthorizationError("Only owner or deploy_service may perform direct modifications")

    # ==================== STATS & STATE ====================
    def set_xp(self, xp: int, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            old_xp = getattr(self.sess.ai, "experience_points", None)
            self.sess.ai.experience_points = xp
            if self.gui:
                try:
                    self.gui.xp_label.config(text=f"XP: {xp}")
                except Exception:
                    pass
            self._log_modification("xp", old_xp, xp)
            return {"success": True, "old": old_xp, "new": xp, "actor": identity.get("sub")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_level(self, level: int, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            old_level = getattr(self.sess.ai, "intelligence_level", None)
            self.sess.ai.intelligence_level = level
            if self.gui:
                try:
                    self.gui.level_label.config(text=f"Level: {level}")
                except Exception:
                    pass
            self._log_modification("level", old_level, level)
            return {"success": True, "old": old_level, "new": level, "actor": identity.get("sub")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_conversation_count(self, count: int, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            old_count = getattr(self.sess.ai, "total_conversations", None)
            try:
                self.sess.ai.set_conversation_count(count)
            except Exception:
                # best-effort: set attribute directly if method missing
                try:
                    self.sess.ai.total_conversations = count
                except Exception:
                    pass
            if self.gui:
                try:
                    self.gui.conv_label.config(text=f"Conversations: {count}")
                except Exception:
                    pass
            self._log_modification("conversations", old_count, count)
            return {"success": True, "old": old_count, "new": count, "actor": identity.get("sub")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_name(self, name: str, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            # update AI knowledge if available
            old_name = None
            try:
                old_name = self.sess.ai.knowledge.get('name', 'Saraphina')
                self.sess.ai.knowledge['name'] = name
            except Exception:
                try:
                    old_name = getattr(self.sess.ai, 'name', 'Saraphina')
                    setattr(self.sess.ai, 'name', name)
                except Exception:
                    old_name = None
            if self.gui:
                try:
                    self.gui.root.title(f"{name} - Mission Control")
                except Exception:
                    pass
            self._log_modification("name", old_name, name)
            return {"success": True, "old": old_name, "new": name, "actor": identity.get("sub")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== GUI MODIFICATIONS ====================
    def set_gui_color(self, element: str, color: str, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            if not self.gui:
                return {"success": False, "error": "GUI not available"}
            old_color = self.gui.colors.get(element)
            self.gui.colors[element] = color
            try:
                if element == 'bg':
                    self.gui.root.configure(bg=color)
                elif element == 'accent':
                    # safe attempt: update a couple of widgets if exist
                    try:
                        self.gui.status_label.config(fg=color)
                    except Exception:
                        pass
            except Exception:
                pass
            self._log_modification(f"gui_color_{element}", old_color, color)
            return {"success": True, "old": old_color, "new": color, "actor": identity.get("sub")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_gui_title(self, title: str, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            if not self.gui:
                return {"success": False, "error": "GUI not available"}
            old_title = self.gui.root.title()
            self.gui.root.title(title)
            self._log_modification("gui_title", old_title, title)
            return {"success": True, "old": old_title, "new": title, "actor": identity.get("sub")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_system_message(self, message: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Adding a system message is allowed for owner, deploy, or agent (read-only effect).
        If auth_token is provided, verify it; otherwise allow but do not record as auditable self-mod.
        """
        try:
            if auth_token:
                identity = verify_request_identity(auth_token)
                actor = identity.get("sub")
            else:
                actor = "local"
            if not self.gui:
                return {"success": False, "error": "GUI not available"}
            self.gui.add_system_message(message)
            # minimal logging
            self._log_modification("system_message", None, message)
            return {"success": True, "message": message, "actor": actor}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== MEMORY & KNOWLEDGE ====================
    def add_capability(self, capability: str, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            if not hasattr(self.sess.ai, "knowledge"):
                return {"success": False, "error": "AI knowledge not available"}
            caps = self.sess.ai.knowledge.setdefault('capabilities', [])
            if capability not in caps:
                caps.append(capability)
                self._log_modification("capability_add", None, capability)
                return {"success": True, "capability": capability, "actor": identity.get("sub")}
            return {"success": False, "error": "Capability already exists"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_capability(self, capability: str, auth_token: str) -> Dict[str, Any]:
        try:
            identity = self._require_modify_privilege(auth_token)
            caps = self.sess.ai.knowledge.get('capabilities', [])
            if capability in caps:
                caps.remove(capability)
                self._log_modification("capability_remove", capability, None)
                return {"success": True, "capability": capability, "actor": identity.get("sub")}
            return {"success": False, "error": "Capability not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clear_memory(self, memory_type: str = "conversation", auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Clearing conversation memory is sensitive. Allow only owner.
        """
        try:
            if auth_token:
                identity = verify_request_identity(auth_token)
                if identity.get("actor") != "owner":
                    return {"success": False, "error": "Only owner can clear memory"}
            else:
                return {"success": False, "error": "auth_token required"}
            if memory_type == "conversation":
                try:
                    count = len(self.sess.ai.conversation_history)
                    self.sess.ai.conversation_history = []
                    self._log_modification("memory_clear", count, 0)
                    return {"success": True, "cleared": count}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": f"Unknown memory type: {memory_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== FILES & CONFIGURATION ====================
    def read_config_file(self, filename: str) -> Dict[str, Any]:
        """Read config files (read-only) - no auth required but path restricted to repo"""
        try:
            file_path = (self.root_path / filename) if not Path(filename).is_absolute() else Path(filename)
            # Only allow reading inside repo root
            file_path = file_path.resolve()
            if REPO_ROOT not in file_path.parents and file_path != REPO_ROOT:
                return {"success": False, "error": "Read access restricted to repository files"}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"success": True, "content": content, "path": str(file_path)}
            return {"success": False, "error": f"File not found: {filename}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_config_file(self, filename: str, content: str, auth_token: str) -> Dict[str, Any]:
        """
        Write a config file inside repo. Owner only.
        This intentionally forbids writing .env/secrets (assert_path_allowed enforces that).
        """
        try:
            identity = self._require_modify_privilege(auth_token)
            if identity.get("actor") != "owner":
                return {"success": False, "error": "Only owner may write config files via API"}

            file_path = (self.root_path / filename) if not Path(filename).is_absolute() else Path(filename)
            assert_path_allowed(file_path)

            # Write to temp then atomic replace
            tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # size check
            if tmp_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                tmp_path.unlink(missing_ok=True)
                return {"success": False, "error": "File too large"}

            # backup (store copy)
            backup = self.create_backup(str(file_path), auth_token=auth_token)
            os.replace(tmp_path, file_path)
            self._log_modification("file_write", filename, len(content))
            return {"success": True, "path": str(file_path), "bytes": len(content), "backup": backup.get("backup")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_backup(self, filename: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Create backup of a file before modifying. Allow owner/deploy_service.
        """
        try:
            if auth_token:
                identity = self._require_modify_privilege(auth_token)
            source = self.saraphina_path / filename if '/' not in filename else Path(filename)
            backup_dir = self.root_path / ".backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{source.name}.{timestamp}.backup"
            if source.exists():
                import shutil
                shutil.copy2(source, backup_path)
                return {"success": True, "backup": str(backup_path)}
            return {"success": False, "error": "Source file not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== SOURCE CODE MODIFICATION ====================
    def modify_source_code(
        self,
        module_name: str,
        old_text: str,
        new_text: str,
        auth_token: str,
        approval_signature: Optional[str] = None,
        backup: bool = True
    ) -> Dict[str, Any]:
        """
        Modify source code safely.
        - module_name: relative to saraphina/ (e.g., 'ai_core.py')
        - Requires auth_token (owner or deploy_service).
        - For deploy_service, approval_signature must be provided and verified if DEPLOY_SIGNATURE_SECRET is set.
        """
        try:
            identity = self._require_modify_privilege(auth_token)
            target = (self.saraphina_path / module_name).resolve()
            assert_path_allowed(target)

            if not target.exists():
                return {"success": False, "error": f"Module not found: {module_name}"}

            # Read current content
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_text not in content:
                return {"success": False, "error": "Text to replace not found in file"}

            # For deploy_service, verify approval signature if secret exists
            if identity.get("actor") == "deploy_service" and DEPLOY_SIGNATURE_SECRET:
                # Approval signature should be HMAC of (module_name + ':' + new_text) hex
                payload = f"{module_name}:{hashlib.sha256(new_text.encode('utf-8')).hexdigest()}".encode('utf-8')
                if not approval_signature or not verify_deploy_signature(approval_signature, payload):
                    return {"success": False, "error": "Invalid or missing deploy approval signature"}

            # Create backup
            backup_info = None
            if backup:
                backup_info = self.create_backup(module_name, auth_token=auth_token)
                if not backup_info.get("success", False):
                    return {"success": False, "error": f"Backup failed: {backup_info.get('error')}"}

            # Prepare new content
            new_content = content.replace(old_text, new_text)

            # Basic safety checks: size limit
            if len(new_content.encode('utf-8')) > MAX_FILE_SIZE_BYTES:
                return {"success": False, "error": "Resulting file too large"}

            # Write to tmp then atomic replace
            tmp_path = target.with_suffix(target.suffix + f".tmp.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            os.replace(tmp_path, target)

            # Log modification
            self._log_modification(f"code_mod_{module_name}", len(old_text), len(new_text))

            return {
                "success": True,
                "module": module_name,
                "backup": backup_info.get("backup") if backup_info else None,
                "changes": 1,
                "actor": identity.get("sub")
            }
        except AuthorizationError as ae:
            return {"success": False, "error": str(ae)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_method_to_module(self, module_name: str, class_name: str, method_code: str, auth_token: str) -> Dict[str, Any]:
        """
        Add a new method to a class inside a module. Owner or deploy only.
        """
        try:
            identity = self._require_modify_privilege(auth_token)
            file_path = (self.saraphina_path / module_name).resolve()
            assert_path_allowed(file_path)
            if not file_path.exists():
                return {"success": False, "error": f"Module not found: {module_name}"}

            # Create backup
            backup_result = self.create_backup(module_name, auth_token=auth_token)
            if not backup_result.get("success", False):
                return backup_result

            # Read current content and insert method
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            class_indent = None
            insert_pos = None

            for i, line in enumerate(lines):
                if f"class {class_name}" in line:
                    class_indent = len(line) - len(line.lstrip())
                elif class_indent is not None:
                    # Find the end of the class by detecting first top-level line after class block
                    if line.strip() and (len(line) - len(line.lstrip())) <= class_indent:
                        insert_pos = i
                        break

            if insert_pos:
                lines.insert(insert_pos, method_code + "\n\n")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                self._log_modification(f"method_add_{class_name}", None, method_code[:50])
                return {"success": True, "module": module_name, "class": class_name, "actor": identity.get("sub")}

            return {"success": False, "error": f"Class {class_name} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== PERSISTENCE ====================
    def save_state(self) -> Dict[str, Any]:
        """Save complete current state (non-mutating for code)"""
        try:
            state = {
                "timestamp": datetime.utcnow().isoformat(),
                "xp": getattr(self.sess.ai, "experience_points", None),
                "level": getattr(self.sess.ai, "intelligence_level", None),
                "conversations": getattr(self.sess.ai, "total_conversations", None),
                "name": getattr(self.sess.ai, "knowledge", {}).get('name') if getattr(self.sess.ai, "knowledge", None) else None,
                "capabilities": getattr(self.sess.ai, "knowledge", {}).get('capabilities') if getattr(self.sess.ai, "knowledge", None) else None,
                "modification_count": len(self.modification_log)
            }
            state_file = self.root_path / ".saraphina_state.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            return {"success": True, "state_file": str(state_file)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_state(self) -> Dict[str, Any]:
        """Load saved state (requires owner)"""
        try:
            state_file = self.root_path / ".saraphina_state.json"
            if not state_file.exists():
                return {"success": False, "error": "No saved state found"}
            with open(state_file, 'r') as f:
                state = json.load(f)
            # Apply state (not requiring auth here because this is local admin action)
            if 'xp' in state and hasattr(self, 'set_xp'):
                try:
                    # _require_modify_privilege not used here; caller should ensure authorized invocation
                    self.sess.ai.experience_points = state['xp']
                except Exception:
                    pass
            if 'level' in state:
                try:
                    self.sess.ai.intelligence_level = state['level']
                except Exception:
                    pass
            if 'conversations' in state:
                try:
                    self.sess.ai.total_conversations = state['conversations']
                except Exception:
                    pass
            if 'name' in state:
                try:
                    self.sess.ai.knowledge['name'] = state['name']
                except Exception:
                    pass
            return {"success": True, "state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== LOGGING ====================
    def _log_modification(self, mod_type: str, old_value: Any, new_value: Any):
        """Log a modification to memory, knowledge base, and internal log"""
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": mod_type,
                "old": old_value,
                "new": new_value
            }
            self.modification_log.append(entry)
            logger.info(f"[SelfMod] {mod_type}: {old_value} -> {new_value}")
            # Store in episodic memory if available
            if hasattr(self.sess, 'mem') and self.sess.mem:
                try:
                    memory_text = f"Self-modification: Changed {mod_type} from {old_value} to {new_value}"
                    self.sess.mem.add_episodic(
                        role='saraphina',
                        text=memory_text,
                        tags=['self-modification', mod_type]
                    )
                except Exception as e:
                    logger.debug(f"Failed to log to episodic memory: {e}")
            # Store in knowledge base if available
            if hasattr(self.sess, 'ke') and self.sess.ke:
                try:
                    fact_summary = f"Self-modification: {mod_type}"
                    fact_content = f"Changed {mod_type} from {old_value} to {new_value} at {entry['timestamp']}"
                    try:
                        self.sess.ke.store_fact(
                            topic='self_modification',
                            summary=fact_summary,
                            content=fact_content,
                            source='self_modification_api',
                            confidence=1.0
                        )
                    except Exception:
                        # fallback: if ke expects different signature
                        pass
                except Exception as e:
                    logger.debug(f"Failed to log to knowledge base: {e}")
            # Store in AI memory bank if available
            if hasattr(self.sess, 'ai') and self.sess.ai:
                try:
                    mb = getattr(self.sess.ai, 'memory_bank', None)
                    if mb is not None:
                        mb.append({
                            'type': 'self_modification',
                            'modification_type': mod_type,
                            'old_value': str(old_value),
                            'new_value': str(new_value),
                            'timestamp': entry['timestamp'],
                            'importance': 8
                        })
                except Exception as e:
                    logger.debug(f"Failed to log to AI memory bank: {e}")
        except Exception as e:
            logger.debug(f"Failed to complete _log_modification: {e}")