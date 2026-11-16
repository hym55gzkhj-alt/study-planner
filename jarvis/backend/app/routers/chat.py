"""JARVIS-Chat: Fragen zu den eigenen Daten und KI-Lernpartner."""
from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..config import settings
from ..db import connect
from ..deps import get_conn
from ..schemas import ChatIn
from ..services import context, local_brain

router = APIRouter(prefix="/api/chat", tags=["Chat"])

HISTORY_LIMIT = 20  # so viele frühere Nachrichten bekommt die KI als Gedächtnis


def _event(**kw) -> bytes:
    return (json.dumps(kw, ensure_ascii=False) + "\n").encode()


def _save(role: str, content: str, mode: str, subject: str | None) -> None:
    conn = connect(settings.db_path)
    with conn:
        conn.execute("INSERT INTO chat_messages(role, content, mode, subject) VALUES (?,?,?,?)",
                     (role, content, mode, subject))
    conn.close()


@router.get("")
def history(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute(
        "SELECT * FROM (SELECT id, role, content, mode, subject, created_at FROM chat_messages "
        "ORDER BY id DESC LIMIT 100) ORDER BY id"
    ).fetchall()
    return {"ai_enabled": settings.ai_enabled, "messages": [dict(r) for r in rows]}


@router.delete("", status_code=204)
def clear(conn: sqlite3.Connection = Depends(get_conn)):
    conn.execute("DELETE FROM chat_messages")


@router.post("")
def send(body: ChatIn, conn: sqlite3.Connection = Depends(get_conn)):
    snap = context.snapshot(conn)
    past = conn.execute(
        "SELECT role, content FROM (SELECT id, role, content FROM chat_messages ORDER BY id DESC LIMIT ?) ORDER BY id",
        (HISTORY_LIMIT,),
    ).fetchall()
    conn.execute("INSERT INTO chat_messages(role, content, mode, subject) VALUES ('user',?,?,?)",
                 (body.message, body.mode, body.subject))
    conn.commit()

    if not settings.ai_enabled:
        reply = local_brain.answer(body.message, snap)
        _save("assistant", reply, body.mode, body.subject)

        def offline():
            yield _event(type="meta", ai=False)
            yield _event(type="delta", text=reply)
            yield _event(type="done")

        return StreamingResponse(offline(), media_type="application/x-ndjson")

    from ..services import tutor  # erst laden, wenn die KI wirklich genutzt wird

    # Verlauf für die API: muss mit "user" beginnen und abwechseln
    messages: list[dict] = []
    for r in past:
        if messages and messages[-1]["role"] == r["role"]:
            messages[-1]["content"] += "\n\n" + r["content"]
        elif messages or r["role"] == "user":
            messages.append({"role": r["role"], "content": r["content"]})
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += "\n\n" + body.message
    else:
        messages.append({"role": "user", "content": body.message})
    data_text = context.as_text(snap)

    def online():
        yield _event(type="meta", ai=True)
        parts: list[str] = []
        try:
            for chunk in tutor.stream_reply(messages, data_text, body.mode, body.subject):
                parts.append(chunk)
                yield _event(type="delta", text=chunk)
        except tutor.TutorError as e:
            yield _event(type="error", message=str(e))
        if parts:
            _save("assistant", "".join(parts), body.mode, body.subject)
        yield _event(type="done")

    return StreamingResponse(online(), media_type="application/x-ndjson")
