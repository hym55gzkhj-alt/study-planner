"""Fasst die gespeicherten Daten als Text zusammen – für den Chat (lokal und KI)."""
from __future__ import annotations

import datetime as dt
import sqlite3

from . import clock, dashboard, repo

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def date_de(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{WEEKDAYS[d.weekday()]}, {d.day}. {MONTHS[d.month - 1]}"


def exam_line(e: dict) -> str:
    time = f" um {e['time']} Uhr" if e["time"] else " (Uhrzeit unbekannt)"
    extra = f" – Notizen: {e['notes']}" if e["notes"] else ""
    return f"{e['subject']}: {date_de(e['date'])}{time}, noch {e['days_left']} Tage, Lernbedarf {e['difficulty']}/5{extra}"


def task_line(t: dict) -> str:
    status = {"done": "erledigt", "open": "offen", "skipped": "übersprungen"}[t["status"]]
    subj = f"{t['subject']} – " if t.get("subject") else ""
    return f"{subj}{t['title']} ({t['minutes']} min, {status})"


def snapshot(conn: sqlite3.Connection) -> dict:
    """Alle Fakten, die der Chat kennen darf."""
    today = clock.today()
    return {
        "today": today,
        "settings": repo.get_settings(conn),
        "upcoming": repo.list_exams(conn, upcoming_only=True),
        "today_tasks": [t for t in repo.tasks_for_date(conn, today) if t["kind"] != "break"],
        "tomorrow_tasks": [t for t in repo.tasks_for_date(conn, today + dt.timedelta(days=1)) if t["kind"] != "break"],
        "overdue": repo.overdue_tasks(conn, today),
        "week": dashboard.week_stats(conn, today),
        "week_subjects": conn.execute(
            "SELECT subject, SUM(minutes) AS m, COUNT(*) AS n FROM history "
            "WHERE substr(completed_at,1,10) >= ? GROUP BY subject ORDER BY m DESC",
            ((today - dt.timedelta(days=6)).isoformat(),),
        ).fetchall(),
    }


def as_text(s: dict) -> str:
    cfg = s["settings"]
    lines = [
        f"Heute ist {date_de(s['today'].isoformat())} {s['today'].year}.",
        f"Schüler: {cfg['user_name'] or 'unbekannt'}, Klasse {cfg['class_name']}. "
        f"Verfügbare Lernzeit pro Tag: {cfg['daily_minutes']} Minuten.",
        "",
        "Anstehende Klausuren (chronologisch):",
    ]
    lines += [f"- {exam_line(e)}" for e in s["upcoming"]] or ["- keine gespeichert"]
    lines += ["", "Lernaufgaben heute:"]
    lines += [f"- {task_line(t)}" for t in s["today_tasks"]] or ["- keine geplant"]
    lines += ["", "Lernaufgaben morgen:"]
    lines += [f"- {task_line(t)}" for t in s["tomorrow_tasks"]] or ["- keine geplant"]
    if s["overdue"]:
        lines += ["", "Nicht erledigte Aufgaben aus den letzten Tagen:"]
        lines += [f"- {task_line(t)} vom {t['date']}" for t in s["overdue"]]
    w = s["week"]
    lines += ["", f"Letzte 7 Tage: {w['total_minutes']} Lernminuten, {w['tasks_done']} Aufgaben erledigt, Lernserie {w['streak']} Tage."]
    lines += [f"- {r['subject']}: {r['m']} min" for r in s["week_subjects"]]
    return "\n".join(lines)
