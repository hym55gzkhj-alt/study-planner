import json

from app.config import settings


def _ask(client, message, **kw):
    r = client.post("/api/chat", json={"message": message, **kw})
    assert r.status_code == 200
    events = [json.loads(line) for line in r.text.splitlines() if line]
    assert events[-1]["type"] == "done"
    return "".join(e.get("text", "") for e in events if e["type"] == "delta"), events


def _seed(client):
    client.post("/api/exams", json={"subject": "Physik", "date": "2026-11-19", "difficulty": 4})
    client.post("/api/exams", json={"subject": "Geschichte", "date": "2026-11-17", "time": "08:00"})
    client.post("/api/exams", json={"subject": "Mathe", "date": "2026-12-18", "difficulty": 5})


def test_default_name_is_noah(client):
    assert client.get("/api/settings").json()["user_name"] == "Noah"
    text, _ = _ask(client, "Hallo")
    assert "Noah" in text


def test_offline_answers_use_stored_data_only(client):
    text, events = _ask(client, "Was muss ich heute lernen?")
    assert events[0] == {"type": "meta", "ai": False}
    assert "keine Lernaufgaben" in text
    _seed(client)
    text, _ = _ask(client, "Wann schreibe ich meine nächste Klausur?")
    assert "Geschichte" in text and "08:00" in text and "morgen" in text
    text, _ = _ask(client, "Welche Klausur kommt zuerst?")
    assert text.index("Geschichte") < text.index("Physik") < text.index("Mathe")
    text, _ = _ask(client, "Erstelle mir einen Lernplan für morgen.")
    assert "Vorschlag" in text and "Physik" in text and "Geschichte" not in text  # Geschichte ist dann vorbei
    text, _ = _ask(client, "Was habe ich diese Woche geschafft?")
    assert "noch keine" in text
    text, _ = _ask(client, "Erkläre mir die Photosynthese", mode="explain")
    assert "ANTHROPIC_API_KEY" in text


def test_history_persists_and_clears(client):
    _ask(client, "Hallo")
    msgs = client.get("/api/chat").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert client.delete("/api/chat").status_code == 204
    assert client.get("/api/chat").json()["messages"] == []


def test_chat_validation(client):
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "   "}).status_code == 422
    assert client.post("/api/chat", json={"message": "x", "mode": "evil"}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 4001}).status_code == 422


def test_online_tutor_gets_data_context(client, monkeypatch):
    from app.services import tutor

    seen = {}

    def fake_stream(history, data_text, mode, subject):
        seen.update(history=history, data=data_text, mode=mode, subject=subject)
        yield "Frage 1: "
        yield "Was ist **Induktion**?"

    monkeypatch.setattr(tutor, "stream_reply", fake_stream)
    monkeypatch.setattr(type(settings), "ai_enabled", property(lambda self: True))
    _seed(client)
    _ask(client, "Hallo")  # Vorgeschichte
    text, events = _ask(client, "Frag mich ab", mode="quiz", subject="Physik")
    assert events[0] == {"type": "meta", "ai": True}
    assert text == "Frage 1: Was ist **Induktion**?"
    assert seen["mode"] == "quiz" and seen["subject"] == "Physik"
    assert "Physik: Donnerstag, 19. November" in seen["data"] and "Noah" in seen["data"]
    assert seen["history"][0]["role"] == "user" and seen["history"][-1]["content"].endswith("Frag mich ab")
    roles = [m["role"] for m in seen["history"]]
    assert all(a != b for a, b in zip(roles, roles[1:]))  # abwechselnd
    assert client.get("/api/chat").json()["messages"][-1]["content"] == text


def test_online_error_is_reported(client, monkeypatch):
    from app.services import tutor

    def broken(*a, **kw):
        raise tutor.TutorError("Der API-Schlüssel ist ungültig.")
        yield  # pragma: no cover

    monkeypatch.setattr(tutor, "stream_reply", broken)
    monkeypatch.setattr(type(settings), "ai_enabled", property(lambda self: True))
    _, events = _ask(client, "Hallo")
    assert {"type": "error", "message": "Der API-Schlüssel ist ungültig."} in events
