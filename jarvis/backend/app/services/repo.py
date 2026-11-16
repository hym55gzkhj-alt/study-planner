"""Datenzugriff (nur parametrisierte SQL-Abfragen)."""
from __future__ import annotations

import datetime as dt
import sqlite3

from ..db import DEFAULT_SETTINGS
from . import clock


def exam_row(r: sqlite3.Row, today: dt.date | None = None) -> dict:
    today = today or clock.today()
    d = dt.date.fromisoformat(r["date"])
    return {
        "id": r["id"],
        "subject": r["subject"],
        "date": r["date"],
        "time": r["time"],
        "notes": r["notes"],
        "difficulty": r["difficulty"],
        "source": r["source"],
        "days_left": (d - today).days,
    }


def list_exams(conn: sqlite3.Connection, upcoming_only: bool = False) -> list[dict]:
    today = clock.today()
    if upcoming_only:
        rows = conn.execute(
            "SELECT * FROM exams WHERE date >= ? ORDER BY date, time IS NULL, time, subject",
            (today.isoformat(),),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM exams ORDER BY date, time IS NULL, time, subject").fetchall()
    return [exam_row(r, today) for r in rows]


def get_exam(conn: sqlite3.Connection, exam_id: int) -> dict | None:
    r = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    return exam_row(r) if r else None


def create_exam(conn: sqlite3.Connection, data: dict, source: str = "manual") -> dict:
    cur = conn.execute(
        "INSERT INTO exams(subject, date, time, notes, difficulty, source) VALUES (?,?,?,?,?,?)",
        (data["subject"], data["date"].isoformat(), data.get("time"), data.get("notes", ""),
         data.get("difficulty", 3), source),
    )
    return get_exam(conn, cur.lastrowid)


def update_exam(conn: sqlite3.Connection, exam_id: int, data: dict) -> dict | None:
    cur = conn.execute(
        "UPDATE exams SET subject=?, date=?, time=?, notes=?, difficulty=?, updated_at=datetime('now') "
        "WHERE id=?",
        (data["subject"], data["date"].isoformat(), data.get("time"), data.get("notes", ""),
         data.get("difficulty", 3), exam_id),
    )
    return get_exam(conn, exam_id) if cur.rowcount else None


def delete_exam(conn: sqlite3.Connection, exam_id: int) -> bool:
    return conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,)).rowcount > 0


# ---------- Aufgaben ----------

def task_row(r: sqlite3.Row) -> dict:
    return {k: r[k] for k in r.keys()}


TASK_SELECT = (
    "SELECT t.*, e.subject AS subject, e.date AS exam_date FROM tasks t "
    "LEFT JOIN exams e ON e.id = t.exam_id "
)


def tasks_for_date(conn: sqlite3.Connection, day: dt.date) -> list[dict]:
    rows = conn.execute(
        TASK_SELECT + "WHERE t.date = ? ORDER BY t.start_time IS NULL, t.start_time, t.id",
        (day.isoformat(),),
    ).fetchall()
    return [task_row(r) for r in rows]


def overdue_tasks(conn: sqlite3.Connection, day: dt.date) -> list[dict]:
    rows = conn.execute(
        TASK_SELECT + "WHERE t.date < ? AND t.status = 'open' AND t.kind != 'break' ORDER BY t.date, t.id",
        (day.isoformat(),),
    ).fetchall()
    return [task_row(r) for r in rows]


def set_task_status(conn: sqlite3.Connection, task_id: int, status: str) -> dict | None:
    r = conn.execute(TASK_SELECT + "WHERE t.id = ?", (task_id,)).fetchone()
    if not r:
        return None
    if status == "done" and r["status"] != "done":
        conn.execute("UPDATE tasks SET status='done', done_at=datetime('now') WHERE id=?", (task_id,))
        if r["kind"] != "break":
            conn.execute(
                "INSERT INTO history(task_id, exam_id, subject, minutes, completed_at) VALUES (?,?,?,?,?)",
                (task_id, r["exam_id"], r["subject"] or r["title"], r["minutes"],
                 clock.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
    elif status != "done":
        conn.execute("UPDATE tasks SET status=?, done_at=NULL WHERE id=?", (status, task_id))
        conn.execute("DELETE FROM history WHERE task_id = ?", (task_id,))
    r = conn.execute(TASK_SELECT + "WHERE t.id = ?", (task_id,)).fetchone()
    return task_row(r)


# ---------- Einstellungen ----------

INT_SETTINGS = {"daily_minutes", "session_minutes", "break_minutes"}


def get_settings(conn: sqlite3.Connection) -> dict:
    out: dict = dict(DEFAULT_SETTINGS)
    for r in conn.execute("SELECT key, value FROM settings"):
        out[r["key"]] = r["value"]
    for k in INT_SETTINGS:
        out[k] = int(out[k])
    return out


def save_settings(conn: sqlite3.Connection, values: dict) -> dict:
    for k, v in values.items():
        if v is None or k not in DEFAULT_SETTINGS:
            continue
        conn.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, str(v)),
        )
    return get_settings(conn)
