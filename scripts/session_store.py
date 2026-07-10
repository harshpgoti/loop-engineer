#!/usr/bin/env python3
"""SQLite session store with FTS5 search for past session recall."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    workspace TEXT NOT NULL,
    command TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    title,
    body,
    command,
    tags,
    content='sessions',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
    INSERT INTO sessions_fts(rowid, title, body, command, tags)
    VALUES (new.id, new.title, new.body, new.command, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS sessions_ad AFTER DELETE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, title, body, command, tags)
    VALUES('delete', old.id, old.title, old.body, old.command, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, title, body, command, tags)
    VALUES('delete', old.id, old.title, old.body, old.command, old.tags);
    INSERT INTO sessions_fts(rowid, title, body, command, tags)
    VALUES (new.id, new.title, new.body, new.command, new.tags);
END;
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def init_db(db_path: Path) -> None:
    conn = connect(db_path)
    conn.close()


def log_session(
    db_path: Path,
    *,
    workspace: str,
    title: str,
    body: str,
    command: str | None = None,
    tags: str | None = None,
) -> int:
    conn = connect(db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO sessions (created_at, workspace, command, title, body, tags)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (now, workspace, command, title, body, tags),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def search_sessions(db_path: Path, query: str, limit: int = 20) -> list[dict]:
    if not db_path.exists():
        return []
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT s.id, s.created_at, s.workspace, s.command, s.title, s.body, s.tags
            FROM sessions_fts f
            JOIN sessions s ON s.id = f.rowid
            WHERE sessions_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def recent_sessions(db_path: Path, limit: int = 10) -> list[dict]:
    if not db_path.exists():
        return []
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, created_at, workspace, command, title, body, tags
            FROM sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
