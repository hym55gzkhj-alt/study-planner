"""Fasst alle Daten für das Dashboard in einer Antwort zusammen."""
from __future__ import annotations

import datetime as dt
import sqlite3

from . import clock, repo


def _greeting(hour: int) -> str:
    if hour < 11:
        return "Guten Morgen"
    if hour < 18:
        return "Guten Tag"
    return "Guten Abend"


def subject_progress(conn: sqlite3.Connection, exams: list[dict]) -> list[dict]:
    out = []
    for e in exams:
        r = conn.execute(
            "SELECT COALESCE(SUM(minutes),0) AS planned, "
            "COALESCE(SUM(CASE WHEN status='done' THEN minutes END),0) AS done "
            "FROM tasks WHERE exam_id = ? AND kind != 'break'",
            (e["id"],),
        ).fetchone()
        planned, done = r["planned"], r["done"]
        out.append({
            "exam_id": e["id"],
            "subject": e["subject"],
            "date": e["date"],
            "days_left": e["days_left"],
            "planned_minutes": planned,
            "done_minutes": done,
            "percent": round(100 * done / planned) if planned else 0,
        })
    return out


def week_stats(conn: sqlite3.Connection, today: dt.date) -> dict:
    days = [today - dt.timedelta(days=i) for i in range(6, -1, -1)]
    rows = conn.execute(
        "SELECT substr(completed_at,1,10) AS d, SUM(minutes) AS m, COUNT(*) AS n FROM history "
        "WHERE substr(completed_at,1,10) >= ? GROUP BY d",
        (days[0].isoformat(),),
    ).fetchall()
    by_day = {r["d"]: (r["m"], r["n"]) for r in rows}
    series = [{"date": d.isoformat(), "minutes": by_day.get(d.isoformat(), (0, 0))[0]} for d in days]
    # Lernserie: aufeinanderfolgende Tage mit erledigten Aufgaben (bis heute bzw. gestern)
    active = {r["d"] for r in conn.execute("SELECT DISTINCT substr(completed_at,1,10) AS d FROM history")}
    streak, cursor = 0, today
    if cursor.isoformat() not in active:
        cursor -= dt.timedelta(days=1)
    while cursor.isoformat() in active:
        streak += 1
        cursor -= dt.timedelta(days=1)
    return {
        "days": series,
        "total_minutes": sum(s["minutes"] for s in series),
        "tasks_done": sum(v[1] for v in by_day.values()),
        "streak": streak,
    }


def build(conn: sqlite3.Connection) -> dict:
    now = clock.now()
    today = now.date()
    cfg = repo.get_settings(conn)
    upcoming = repo.list_exams(conn, upcoming_only=True)
    today_tasks = repo.tasks_for_date(conn, today)
    overdue = repo.overdue_tasks(conn, today)
    progress = subject_progress(conn, upcoming)
    planned = sum(p["planned_minutes"] for p in progress)
    done = sum(p["done_minutes"] for p in progress)
    learn_today = [t for t in today_tasks if t["kind"] != "break"]
    return {
        "now": now.isoformat(timespec="minutes"),
        "today": today.isoformat(),
        "greeting": _greeting(now.hour),
        "user_name": cfg["user_name"],
        "class_name": cfg["class_name"],
        "next_exam": upcoming[0] if upcoming else None,
        "upcoming_exams": upcoming[:8],
        "exam_count": len(upcoming),
        "today_tasks": today_tasks,
        "today_summary": {
            "total": len(learn_today),
            "done": sum(1 for t in learn_today if t["status"] == "done"),
            "minutes": sum(t["minutes"] for t in learn_today),
        },
        "overdue_tasks": overdue,
        "subject_progress": progress,
        "overall_progress": {
            "planned_minutes": planned,
            "done_minutes": done,
            "percent": round(100 * done / planned) if planned else 0,
        },
        "week": week_stats(conn, today),
        "daily_minutes": cfg["daily_minutes"],
    }
