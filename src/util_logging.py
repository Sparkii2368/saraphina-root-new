#!/usr/bin/env python3
"""
Utility Logging Module for Saraphina
Upgraded to support file rotation, console output, and rich data formatting.
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "saraphina_core.log"

# Configure global logging
logger = logging.getLogger("SaraphinaCore")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

# File Handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

# Stream Handler (Console)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# Add handlers if not already added
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

def safe_log(message: str, level: str = "INFO", data: dict = None):
    """
    Centralized safe logging function.
    Handles standard string logging and structured data logging.
    """
    log_msg = message
    
    # If data is provided, format it nicely but compactly
    if data:
        try:
            data_str = json.dumps(data, default=str)
            if len(data_str) > 200: # Truncate long data for console readability
                log_msg += f" | Data: {data_str[:200]}..."
            else:
                log_msg += f" | Data: {data_str}"
        except Exception:
            log_msg += f" | Data: <non-serializable>"

    lvl = level.upper()
    if lvl == "DEBUG":
        logger.debug(log_msg)
    elif lvl == "WARNING":
        logger.warning(log_msg)
    elif lvl == "ERROR":
        logger.error(log_msg)
    elif lvl == "CRITICAL":
        logger.critical(log_msg)
    else:
        logger.info(log_msg)