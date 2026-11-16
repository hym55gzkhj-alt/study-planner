"""SQLite-Datenbank: Verbindung und Schema. Alle Daten bleiben nach einem Neustart erhalten."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Klausuren und andere Prüfungstermine
CREATE TABLE IF NOT EXISTS exams (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject     TEXT NOT NULL,
    date        TEXT NOT NULL,              -- ISO: YYYY-MM-DD
    time        TEXT,                       -- HH:MM oder NULL (unbekannt)
    notes       TEXT NOT NULL DEFAULT '',
    difficulty  INTEGER NOT NULL DEFAULT 3 CHECK (difficulty BETWEEN 1 AND 5),
    source      TEXT NOT NULL DEFAULT 'manual',   -- manual | import
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(date);

-- Lernaufgaben (werden ab Schritt 5 vom Lernplaner erzeugt)
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id     INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,              -- geplanter Tag
    start_time  TEXT,                       -- HH:MM
    minutes     INTEGER NOT NULL CHECK (minutes BETWEEN 5 AND 600),
    title       TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'learn',  -- learn | review | break
    status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','done','skipped')),
    done_at     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks(date);

-- Lernhistorie: ein Eintrag pro erledigter Aufgabe
CREATE TABLE IF NOT EXISTS history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    exam_id     INTEGER REFERENCES exams(id) ON DELETE SET NULL,
    subject     TEXT NOT NULL,
    minutes     INTEGER NOT NULL,
    completed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- JARVIS-Chat (Verlauf bleibt nach Neustart erhalten)
CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT NOT NULL CHECK (role IN ('user','assistant')),
    content     TEXT NOT NULL,
    mode        TEXT NOT NULL DEFAULT 'chat',
    subject     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tagesberichte (07:00-Uhr-Begrüßung)
CREATE TABLE IF NOT EXISTS briefings (
    date        TEXT PRIMARY KEY,
    text        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    seen_at     TEXT
);
"""

DEFAULT_SETTINGS = {
    "user_name": "Noah",
    "class_name": "BG11d",
    "daily_minutes": "120",      # verfügbare Lernzeit pro Tag
    "session_minutes": "45",     # Länge eines Lernblocks
    "break_minutes": "10",       # Pause zwischen Blöcken
    "study_start": "15:30",      # frühester Lernbeginn
    "briefing_time": "07:00",
    "rest_weekdays": "",         # z. B. "6" = Sonntag frei (0=Mo … 6=So)
}


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(path: Path) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
            DEFAULT_SETTINGS.items(),
        )
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.close()


def get_conn_factory(path: Path):
    """FastAPI-Dependency: eine Verbindung pro Request."""

    def _dep() -> Iterator[sqlite3.Connection]:
        conn = connect(path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    return _dep
