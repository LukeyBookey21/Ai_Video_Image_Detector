"""
Database module — SQLite storage for stats, waitlist, and API keys.
Replaces JSON/CSV file storage with proper database.
"""

import hashlib
import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger("ai-detector")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "detector.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_db():
    """Context manager for database connections with WAL mode."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_analyses INTEGER DEFAULT 0,
                ai_detected INTEGER DEFAULT 0,
                authentic INTEGER DEFAULT 0,
                uncertain INTEGER DEFAULT 0,
                last_updated TEXT
            );
            INSERT OR IGNORE INTO stats (id) VALUES (1);

            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                ip_hash TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                requests_today INTEGER DEFAULT 0,
                last_reset TEXT
            );

            CREATE TABLE IF NOT EXISTS analysis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                file_type TEXT,
                verdict TEXT,
                confidence REAL,
                ai_probability REAL,
                processing_time REAL,
                created_at TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                token TEXT UNIQUE NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT
            );

            CREATE TABLE IF NOT EXISTS saved_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                filename TEXT,
                file_type TEXT,
                verdict TEXT,
                confidence REAL,
                ai_probability REAL,
                explanation TEXT,
                created_at TEXT NOT NULL
            );
        """)
    logger.info("Database initialized")


def update_stats(verdict: str):
    """Increment analysis counters."""
    col = "ai_detected" if verdict == "AI-Generated" else "authentic" if verdict == "Real/Authentic" else "uncertain"
    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        conn.execute(
            f"UPDATE stats SET total_analyses = total_analyses + 1, {col} = {col} + 1, last_updated = ? WHERE id = 1",
            (now,),
        )


def get_stats() -> dict:
    """Return current stats."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM stats WHERE id = 1").fetchone()
        if row:
            return dict(row)
        return {"total_analyses": 0, "ai_detected": 0, "authentic": 0, "uncertain": 0, "last_updated": ""}


def log_analysis(
    filename: str, file_type: str, verdict: str, confidence: float, ai_probability: float, processing_time: float
):
    """Log an individual analysis for history."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO analysis_log (filename, file_type, verdict, confidence, ai_probability, processing_time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                filename,
                file_type,
                verdict,
                confidence,
                ai_probability,
                processing_time,
                datetime.utcnow().isoformat() + "Z",
            ),
        )


def add_to_waitlist(email: str, ip_hash: str) -> str:
    """Add email to waitlist. Returns 'added', 'already_registered', or raises."""
    with get_db() as conn:
        existing = conn.execute("SELECT 1 FROM waitlist WHERE email = ?", (email,)).fetchone()
        if existing:
            return "already_registered"
        conn.execute(
            "INSERT INTO waitlist (email, ip_hash, created_at) VALUES (?, ?, ?)",
            (email, ip_hash, datetime.utcnow().isoformat() + "Z"),
        )
        return "added"


def create_user(email: str) -> dict:
    """Create a new user with a magic link token. Returns user dict."""
    token = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            # Regenerate token for existing user (magic link re-auth)
            conn.execute("UPDATE users SET token = ?, last_login = ? WHERE email = ?", (token, now, email))
            return {"id": existing["id"], "email": email, "token": token, "new": False}
        conn.execute(
            "INSERT INTO users (email, token, created_at, last_login) VALUES (?, ?, ?, ?)",
            (email, token, now, now),
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"id": user_id, "email": email, "token": token, "new": True}


def get_user_by_token(token: str) -> dict | None:
    """Look up a user by their auth token."""
    with get_db() as conn:
        row = conn.execute("SELECT id, email, display_name, created_at FROM users WHERE token = ?", (token,)).fetchone()
        return dict(row) if row else None


def save_result(user_id: int, filename: str, file_type: str, verdict: str, confidence: float, ai_probability: float, explanation: str) -> int:
    """Save an analysis result for a user."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO saved_results (user_id, filename, file_type, verdict, confidence, ai_probability, explanation, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, filename, file_type, verdict, confidence, ai_probability, explanation, datetime.utcnow().isoformat() + "Z"),
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_user_results(user_id: int, limit: int = 50) -> list:
    """Return saved results for a user."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, filename, file_type, verdict, confidence, ai_probability, explanation, created_at FROM saved_results WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_user_result(user_id: int, result_id: int) -> bool:
    """Delete a saved result. Returns True if deleted."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM saved_results WHERE id = ? AND user_id = ?", (result_id, user_id))
        return cursor.rowcount > 0


def get_recent_analyses(limit: int = 50) -> list:
    """Return recent analyses for admin dashboard."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT filename, file_type, verdict, confidence, ai_probability, processing_time, created_at FROM analysis_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
