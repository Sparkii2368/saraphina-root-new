#!/usr/bin/env python3
"""
SQLite database layer for Saraphina
- Initializes primary schemas
- Provides connection helpers and backup utilities
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

DB_DIR = Path("ai_data")
DB_FILE = DB_DIR / "saraphina.db"

def _ensure_dirs():
    DB_DIR.mkdir(parents=True, exist_ok=True)

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite connection with row factory and FK enabled.
    Also enables WAL for better concurrency.
    """
    _ensure_dirs()
    path = Path(db_path) if db_path else DB_FILE
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn

def get_encrypted_connection(db_path: Optional[str], key: str):
    """Optional SQLCipher connection; requires pysqlcipher3. Returns sqlite3-like connection or raises."""
    _ensure_dirs()
    path = Path(db_path) if db_path else DB_FILE
    try:
        from pysqlcipher3 import dbapi2 as sqlcipher
    except Exception as e:
        raise RuntimeError("SQLCipher not available: install pysqlcipher3")
    conn = sqlcipher.connect(str(path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA key = ?", (key,))
    cur.execute("PRAGMA foreign_keys = ON;")
    try:
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn

def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they do not exist (idempotent)."""
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS facts (
          id TEXT PRIMARY KEY,
          topic TEXT,
          summary TEXT,
          content TEXT,
          source TEXT,
          confidence REAL,
          created_at TEXT,
          updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS fact_aliases (
          alias TEXT,
          fact_id TEXT
        );

        CREATE TABLE IF NOT EXISTS fact_versions (
          version_id TEXT PRIMARY KEY,
          fact_id TEXT,
          content TEXT,
          changed_at TEXT,
          reason TEXT
        );

        CREATE TABLE IF NOT EXISTS concept_links (
          id TEXT PRIMARY KEY,
          from_fact TEXT,
          to_fact TEXT,
          relation_type TEXT
        );

        CREATE TABLE IF NOT EXISTS queries (
          id TEXT PRIMARY KEY,
          text TEXT,
          fact_id TEXT,
          response_text TEXT,
          timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS preferences (
          key TEXT PRIMARY KEY,
          value TEXT
        );

        CREATE TABLE IF NOT EXISTS devices (
          device_id TEXT PRIMARY KEY,
          name TEXT,
          platform TEXT,
          owner TEXT,
          public_key TEXT,
          enrolled_at TEXT,
          last_seen TEXT,
          capabilities TEXT,
          last_location TEXT
        );

        CREATE TABLE IF NOT EXISTS device_agents (
          agent_id TEXT PRIMARY KEY,
          device_id TEXT,
          public_key TEXT,
          heartbeat_ts TEXT,
          status TEXT
        );

        CREATE TABLE IF NOT EXISTS device_policies (
          policy_id TEXT PRIMARY KEY,
          device_id TEXT,
          policy_json TEXT,
          created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
          log_id TEXT PRIMARY KEY,
          actor TEXT,
          action TEXT,
          target TEXT,
          details TEXT,
          timestamp TEXT
        );

        -- Enforce append-only audit logs (no UPDATE/DELETE)
        CREATE TRIGGER IF NOT EXISTS audit_logs_no_update
        BEFORE UPDATE ON audit_logs
        BEGIN
          SELECT RAISE(ABORT, 'audit logs are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS audit_logs_no_delete
        BEFORE DELETE ON audit_logs
        BEGIN
          SELECT RAISE(ABORT, 'audit logs are immutable');
        END;

        CREATE TABLE IF NOT EXISTS skills_xp (
          skill TEXT PRIMARY KEY,
          level REAL,
          xp REAL
        );

        CREATE TABLE IF NOT EXISTS code_artifacts (
          artifact_id TEXT PRIMARY KEY,
          title TEXT,
          code TEXT,
          tests TEXT,
          author TEXT,
          status TEXT,
          created_at TEXT
        );

        -- Human memory tables
        CREATE TABLE IF NOT EXISTS episodic_memory (
          id TEXT PRIMARY KEY,
          timestamp TEXT,
          speaker TEXT,
          text TEXT,
          mood TEXT,
          tags TEXT
        );

        CREATE TABLE IF NOT EXISTS semantic_memory (
          id TEXT PRIMARY KEY,
          keyphrase TEXT,
          summary TEXT,
          importance REAL,
          last_refreshed TEXT
        );

        CREATE TABLE IF NOT EXISTS entity_links (
          id TEXT PRIMARY KEY,
          src TEXT,
          dst TEXT,
          relation TEXT,
          weight REAL,
          updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS reminders (
          id TEXT PRIMARY KEY,
          text TEXT,
          due_ts TEXT,
          status TEXT,
          created_at TEXT
        );

        -- Learning journal for meta-learning
        CREATE TABLE IF NOT EXISTS learning_journal (
          id TEXT PRIMARY KEY,
          timestamp TEXT,
          query TEXT,
          response TEXT,
          strategy TEXT,
          success REAL,
          notes TEXT,
          metrics TEXT
        );

        -- Shadow nodes (redundancy)
        CREATE TABLE IF NOT EXISTS shadow_nodes (
          id TEXT PRIMARY KEY,
          name TEXT,
          device_id TEXT,
          path TEXT,
          added_at TEXT,
          active INTEGER
        );

        -- Review queue for manual approvals
        CREATE TABLE IF NOT EXISTS review_queue (
          id TEXT PRIMARY KEY,
          item_type TEXT,
          reason TEXT,
          payload TEXT,
          status TEXT,
          created_at TEXT,
          reviewed_at TEXT
        );

        -- Persona artifacts (modular persona upgrades)
        CREATE TABLE IF NOT EXISTS persona_artifacts (
          id TEXT PRIMARY KEY,
          title TEXT,
          profile_json TEXT,
          status TEXT,
          created_at TEXT,
          approved_at TEXT
        );

        -- Belief store (values & principles)
        CREATE TABLE IF NOT EXISTS belief_store (
          id TEXT PRIMARY KEY,
          key TEXT,
          description TEXT,
          weight REAL,
          created_at TEXT
        );

        -- Ethical journal
        CREATE TABLE IF NOT EXISTS ethical_journal (
          id TEXT PRIMARY KEY,
          timestamp TEXT,
          plan_goal TEXT,
          score_alignment REAL,
          conflicts TEXT,
          decision TEXT,
          notes TEXT
        );

        -- Mood journal for emotion engine
        CREATE TABLE IF NOT EXISTS mood_journal (
          id TEXT PRIMARY KEY,
          timestamp TEXT,
          mood TEXT,
          intensity REAL,
          note TEXT
        );

        -- Research reports
        CREATE TABLE IF NOT EXISTS research_reports (
          id TEXT PRIMARY KEY,
          topic TEXT,
          summary TEXT,
          content TEXT,
          sources TEXT,
          created_at TEXT
        );

        -- Dream log
        CREATE TABLE IF NOT EXISTS dream_log (
          id TEXT PRIMARY KEY,
          timestamp TEXT,
          mood TEXT,
          text TEXT
        );

        -- Embedding vectors for facts
        CREATE TABLE IF NOT EXISTS fact_vectors (
          fact_id TEXT PRIMARY KEY,
          vector_json TEXT,
          updated_at TEXT
        );

        -- Indices for performance
        CREATE INDEX IF NOT EXISTS idx_facts_topic ON facts(topic);
        CREATE INDEX IF NOT EXISTS idx_facts_updated_at ON facts(updated_at);
        CREATE INDEX IF NOT EXISTS idx_queries_fact_id ON queries(fact_id);
        CREATE INDEX IF NOT EXISTS idx_fact_vectors_updated ON fact_vectors(updated_at);
        CREATE INDEX IF NOT EXISTS idx_episodic_ts ON episodic_memory(timestamp);
        CREATE INDEX IF NOT EXISTS idx_semantic_key ON semantic_memory(keyphrase);
        CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_ts);
        CREATE INDEX IF NOT EXISTS idx_journal_ts ON learning_journal(timestamp);
        CREATE INDEX IF NOT EXISTS idx_shadow_active ON shadow_nodes(active);

        -- Full-text search for facts
        CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
          id,
          summary,
          content,
          topic,
          tokenize='porter'
        );
        CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
          INSERT INTO facts_fts (id, summary, content, topic)
          VALUES (new.id, new.summary, new.content, new.topic);
        END;
        CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
          UPDATE facts_fts SET summary=new.summary, content=new.content, topic=new.topic WHERE id=old.id;
        END;
        CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
          DELETE FROM facts_fts WHERE id=old.id;
        END;

        -- Emulate cascade deletes for related tables (for existing schemas without FKs)
        CREATE TRIGGER IF NOT EXISTS facts_delete_versions AFTER DELETE ON facts BEGIN
          DELETE FROM fact_versions WHERE fact_id=old.id;
          DELETE FROM fact_aliases WHERE fact_id=old.id;
          DELETE FROM concept_links WHERE from_fact=old.id OR to_fact=old.id;
          DELETE FROM fact_vectors WHERE fact_id=old.id;
        END;

        -- System metadata (real version tracking, NOT GPT-4 fallback)
        CREATE TABLE IF NOT EXISTS system_metadata (
          key TEXT PRIMARY KEY,
          value TEXT,
          updated_at TEXT
        );
        
        -- Minimal migrations registry
        CREATE TABLE IF NOT EXISTS migrations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE,
          applied_at TEXT
        );
        """
    )
    conn.commit()

def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    # Allow optional SQLCipher via environment.
    use_cipher = os.getenv('SARAPHINA_SQLCIPHER', 'false').lower() in ['1','true','yes','on']
    if use_cipher:
        key = os.getenv('SARAPHINA_SQLCIPHER_KEY')
        path = os.getenv('SARAPHINA_SQLCIPHER_PATH') or (str(DB_FILE).replace('.db', '_sqlcipher.db'))
        if not key:
            # Fallback to plain if key missing
            conn = get_connection(db_path)
            initialize_schema(conn)
            return conn
        try:
            conn = get_encrypted_connection(path, key)
            initialize_schema(conn)
            return conn
        except Exception:
            # Fallback to plain on failure (non-fatal)
            conn = get_connection(db_path)
            initialize_schema(conn)
            return conn
    else:
        conn = get_connection(db_path)
        initialize_schema(conn)
        return conn

def backup_db(conn: sqlite3.Connection, dest_path: str) -> str:
    """Create a consistent backup of the database to dest_path."""
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(dest)) as dest_conn:
        conn.backup(dest_conn)
    return str(dest)

# --- SQLCipher helpers ---

def sqlcipher_available() -> bool:
    try:
        from pysqlcipher3 import dbapi2 as _sqlcipher  # noqa: F401
        return True
    except Exception:
        return False


def migrate_plain_to_sqlcipher(plain_path: str, cipher_path: str, key: str) -> Dict[str, Any]:
    """Export a plaintext SQLite DB to a new SQLCipher-encrypted DB.
    Returns a result dict with 'ok' and 'path'.
    """
    if not sqlcipher_available():
        raise RuntimeError("SQLCipher not available: pip install pysqlcipher3")
    from pysqlcipher3 import dbapi2 as sqlcipher
    plain = Path(plain_path)
    cipher = Path(cipher_path)
    cipher.parent.mkdir(parents=True, exist_ok=True)
    # Create encrypted DB and export
    conn = sqlcipher.connect(str(cipher))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA key = ?", (key,))
    # Attach plaintext DB
    cur.execute("ATTACH DATABASE ? AS plaintext KEY ''", (str(plain.resolve()),))
    cur.execute("SELECT sqlcipher_export('main','plaintext');")
    cur.execute("DETACH DATABASE plaintext;")
    conn.commit()
    conn.close()
    return {"ok": True, "path": str(cipher)}


def try_open_sqlcipher(path: str, key: str) -> bool:
    if not sqlcipher_available():
        return False
    from pysqlcipher3 import dbapi2 as sqlcipher
    try:
        conn = sqlcipher.connect(str(path))
        cur = conn.cursor()
        cur.execute("PRAGMA key = ?", (key,))
        cur.execute("SELECT count(1) FROM sqlite_master;")
        _ = cur.fetchone()
        conn.close()
        return True
    except Exception:
        return False


def rekey_sqlcipher(path: str, old_key: str, new_key: str) -> bool:
    if not sqlcipher_available():
        raise RuntimeError("SQLCipher not available: pip install pysqlcipher3")
    from pysqlcipher3 import dbapi2 as sqlcipher
    conn = sqlcipher.connect(str(path))
    cur = conn.cursor()
    cur.execute("PRAGMA key = ?", (old_key,))
    cur.execute("PRAGMA rekey = ?", (new_key,))
    conn.commit()
    conn.close()
    return True

def write_audit_log(conn: sqlite3.Connection, actor: str, action: str, target: str, details: dict) -> None:
    from uuid import uuid4
    from datetime import datetime
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_logs (log_id, actor, action, target, details, timestamp) VALUES (?,?,?,?,?,?)",
        (str(uuid4()), actor, action, target, json.dumps(details, ensure_ascii=False), datetime.utcnow().isoformat())
    )
    conn.commit()

def get_preference(conn: sqlite3.Connection, key: str) -> Optional[str]:
    cur = conn.cursor()
    cur.execute("SELECT value FROM preferences WHERE key=?", (key,))
    row = cur.fetchone()
    return row[0] if row else None

def set_preference(conn: sqlite3.Connection, key: str, value: str) -> None:
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?,?)", (key, value))
    conn.commit()

def get_system_metadata(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """Get system metadata (version, build date, etc.) - TRUTH, not GPT-4 fallback."""
    cur = conn.cursor()
    cur.execute("SELECT value FROM system_metadata WHERE key=?", (key,))
    row = cur.fetchone()
    return row[0] if row else None

def set_system_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Set system metadata with timestamp."""
    from datetime import datetime
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO system_metadata (key, value, updated_at) VALUES (?,?,?)",
        (key, value, datetime.utcnow().isoformat())
    )
    conn.commit()

def initialize_system_metadata(conn: sqlite3.Connection) -> None:
    """Initialize system metadata on startup with real values."""
    from datetime import datetime
    import platform
    
    # Version and build info
    version = "1.0.0-ultra"  # Update this with each release
    build_date = datetime.utcnow().strftime('%Y-%m-%d')
    session_start = datetime.utcnow().isoformat()
    
    # Only set if not exists (preserve build_date across sessions)
    if not get_system_metadata(conn, 'build_date'):
        set_system_metadata(conn, 'build_date', build_date)
    
    # Always update these on startup
    set_system_metadata(conn, 'version', version)
    set_system_metadata(conn, 'last_session_start', session_start)
    set_system_metadata(conn, 'last_update', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    set_system_metadata(conn, 'platform', platform.system())
    set_system_metadata(conn, 'python_version', platform.python_version())
