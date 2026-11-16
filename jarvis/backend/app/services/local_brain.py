"""JARVIS ohne KI-Schlüssel: beantwortet Fragen zu den gespeicherten Daten mit festen Regeln.

Es werden ausschließlich gespeicherte Daten verwendet – nichts wird erfunden.
"""
from __future__ import annotations

import datetime as dt
import re

from .context import date_de, task_line

NO_AI_HINT = (
    "Für Erklärungen, Abfragen und Zusammenfassungen brauche ich meinen KI-Kern. "
    "Trage dafür deinen Schlüssel als ANTHROPIC_API_KEY in die Datei .env ein und starte JARVIS neu. "
    "Ohne Schlüssel kann ich dir sagen, was heute ansteht, wann deine nächste Klausur ist, "
    "welche Klausur zuerst kommt, was du diese Woche geschafft hast, und einen Lernplan für morgen vorschlagen."
)


def _has(text: str, *words: str) -> bool:
    return any(re.search(rf"\b{w}", text) for w in words)


def suggest_plan(s: dict, day: dt.date) -> list[tuple[str, int]]:
    """Einfacher Vorschlag: verteilt die Tageslernzeit auf die nächsten Klausuren
    (je näher und je schwerer, desto mehr Zeit)."""
    budget = s["settings"]["daily_minutes"]
    exams = [e for e in s["upcoming"] if dt.date.fromisoformat(e["date"]) > day][:3]
    if not exams or budget <= 0:
        return []
    weights = []
    for e in exams:
        days = (dt.date.fromisoformat(e["date"]) - day).days
        weights.append(e["difficulty"] / max(days, 1))
    total = sum(weights)
    plan = []
    for e, w in zip(exams, weights):
        m = int(round(budget * w / total / 15) * 15)
        if m >= 15:
            plan.append((e["subject"], m))
    return plan


def answer(question: str, s: dict) -> str:
    q = question.lower()
    upcoming, cfg = s["upcoming"], s["settings"]
    name = cfg["user_name"]

    if _has(q, "hallo", "hi", "hey", "guten (morgen|tag|abend)", "moin", "servus") and len(q) < 30:
        return f"Hallo{' ' + name if name else ''}! Wobei kann ich dir helfen?"

    if _has(q, "morgen") and _has(q, "lernplan", "plan", "lernen"):
        tomorrow = s["today"] + dt.timedelta(days=1)
        if s["tomorrow_tasks"]:
            lines = [f"Für morgen ({date_de(tomorrow.isoformat())}) ist geplant:"]
            lines += [f"{i}. {task_line(t)}" for i, t in enumerate(s["tomorrow_tasks"], 1)]
            return "\n".join(lines)
        plan = suggest_plan(s, tomorrow)
        if not plan:
            return "Ich habe keine anstehenden Klausuren gespeichert, für die ich morgen einen Plan erstellen könnte."
        lines = [f"Vorschlag für morgen ({date_de(tomorrow.isoformat())}), {cfg['daily_minutes']} Minuten Lernzeit:"]
        lines += [f"{i}. {subj} – {m} Minuten" for i, (subj, m) in enumerate(plan, 1)]
        lines.append(f"Plane nach jedem Block {cfg['break_minutes']} Minuten Pause ein.")
        return "\n".join(lines)

    if _has(q, "woche", "geschafft", "erledigt", "fortschritt"):
        w = s["week"]
        if not w["tasks_done"]:
            return "In den letzten 7 Tagen hast du noch keine Lernaufgabe als erledigt markiert."
        lines = [f"In den letzten 7 Tagen hast du {w['tasks_done']} Aufgaben erledigt und {w['total_minutes']} Minuten gelernt."]
        lines += [f"- {r['subject']}: {r['m']} Minuten" for r in s["week_subjects"]]
        if w["streak"]:
            lines.append(f"Deine Lernserie: {w['streak']} Tag(e) in Folge. Weiter so!")
        return "\n".join(lines)

    if _has(q, "zuerst", "reihenfolge", "welche klausur", "alle klausuren", "klausuren"):
        if not upcoming:
            return "Ich habe keine anstehenden Klausuren gespeichert."
        lines = ["Deine nächsten Klausuren in zeitlicher Reihenfolge:"]
        lines += [f"{i}. {e['subject']} – {date_de(e['date'])}"
                  f"{' um ' + e['time'] + ' Uhr' if e['time'] else ''} (in {e['days_left']} Tagen)"
                  for i, e in enumerate(upcoming[:10], 1)]
        return "\n".join(lines)

    if _has(q, "nächste", "naechste", "wann", "klausur"):
        if not upcoming:
            return "Ich habe keine anstehenden Klausuren gespeichert."
        e = upcoming[0]
        when = "heute" if e["days_left"] == 0 else "morgen" if e["days_left"] == 1 else f"in {e['days_left']} Tagen"
        time = f" um {e['time']} Uhr" if e["time"] else " (die Uhrzeit ist nicht eingetragen)"
        return f"Deine nächste Klausur ist {e['subject']} am {date_de(e['date'])}{time} – also {when}."

    if _has(q, "heute", "lernen", "aufgabe", "tun", "machen"):
        if s["today_tasks"]:
            lines = ["Heute stehen folgende Aufgaben an:"]
            lines += [f"{i}. {task_line(t)}" for i, t in enumerate(s["today_tasks"], 1)]
        else:
            lines = ["Für heute sind keine Lernaufgaben eingetragen."]
            plan = suggest_plan(s, s["today"])
            if plan:
                lines.append("Mein Vorschlag:")
                lines += [f"{i}. {subj} – {m} Minuten" for i, (subj, m) in enumerate(plan, 1)]
        if s["overdue"]:
            lines.append(f"Außerdem sind noch {len(s['overdue'])} Aufgabe(n) von früher offen.")
        if upcoming:
            lines.append(f"Deine nächste Klausur ist {upcoming[0]['subject']} am {date_de(upcoming[0]['date'])}.")
        return "\n".join(lines)

    return NO_AI_HINT
