python
#!/usr/bin/env python3
"""
Saraphina — Final Form GUI (Windows, Smart-Hybrid Voice)
Hardened + improved playback and robustness (refactor for clarity)
Author: Curated upgrade for Jacques Schutte
Date: 2025-11-12 (upgraded)
"""

from __future__ import annotations
import os
import logging
import datetime
from pathlib import Path
import psutil

# ===== Back-compat core alias helper =====
def _sara_patch_core_aliases(core):
    """Ensure UltraAICore exposes .ultra, .core, and .ai for legacy paths."""
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
# ===== /helper =====

# ==== Early .env loader (hard-wired to D:\\Saraphina Root\\.env) ====
def _sara_apply_env():
    p = Path(r"D:\\Saraphina Root\\.env")
    if not p.exists():
        return
    allow = {
        "ELEVENLABS_API_KEY", "ELEVEN_API_KEY", "ELEVEN_VOICE_ID",
        "OPENAI_API_KEY", "SARA_THEME_ACCENT",
        "SELF_MOD_ENABLE", "SELF_MOD_OWNER_TOKEN", "SELF_MOD_DEPLOY_TOKEN", "SELF_MOD_SECRET"
    }
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip(); v = v.strip().strip("'").strip('"')
        if k in allow and v:
            os.environ[k] = v
_sara_apply_env()
# ==== /env loader ====

# ==== Saraphina hardwired launch & logging (D:\\Saraphina Root) ====
try:
    import os as _os
    import logging as _logging
    import datetime as _dt
    from pathlib import Path as _Path
    _PROJECT_ROOT = _Path(r"D:\\Saraphina Root")
    _SRC_DIR = _PROJECT_ROOT / "src"
    if _SRC_DIR.exists():
        _os.chdir(str(_SRC_DIR))
    _LOG_DIR = _PROJECT_ROOT / "logs"
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(
        filename=str(_LOG_DIR / f"log_{_dt.datetime.now().strftime('%Y%m%d')}.log"),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Log system information
    logging.info("Starting Saraphina GUI")
    logging.info(f"Python version: {os.sys.version}")
    logging.info(f"Current working directory: {os.getcwd()}")

    # Log system resource usage
    process = psutil.Process()
    logging.info(f"Process ID: {process.pid}")
    logging.info(f"Memory Info: {process.memory_info()}")
    logging.info(f"CPU Usage: {process.cpu_percent(interval=1)}%")

except Exception as e:
    logging.error(f"Error during initialization: {e}")
# ==== /launch & logging ====
