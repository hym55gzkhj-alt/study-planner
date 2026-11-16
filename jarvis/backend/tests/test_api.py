import sqlite3

from app.config import settings


def test_health_and_frontend(client):
    assert client.get("/api/health").json()["status"] == "online"
    r = client.get("/")
    assert r.status_code == 200 and "JARVIS" in r.text
    assert "Content-Security-Policy" in r.headers
    assert client.get("/static/js/app.js").status_code == 200


def test_empty_dashboard(client):
    d = client.get("/api/dashboard").json()
    assert d["next_exam"] is None
    assert d["exam_count"] == 0
    assert d["greeting"] == "Guten Morgen"
    assert len(d["week"]["days"]) == 7


def test_exam_crud_and_ordering(client):
    a = client.post("/api/exams", json={"subject": "Physik", "date": "2026-11-19"}).json()
    b = client.post("/api/exams", json={"subject": "Geschichte", "date": "2026-11-17", "time": "08:00", "difficulty": 4}).json()
    client.post("/api/exams", json={"subject": "Alt", "date": "2026-11-01"})
    assert a["days_left"] == 3 and a["time"] is None
    upcoming = client.get("/api/exams?upcoming=true").json()
    assert [e["subject"] for e in upcoming] == ["Geschichte", "Physik"]
    assert len(client.get("/api/exams").json()) == 3

    r = client.put(f"/api/exams/{a['id']}", json={"subject": "Physik", "date": "2026-11-19", "time": "09:45", "notes": "Optik"})
    assert r.json()["time"] == "09:45" and r.json()["notes"] == "Optik"

    d = client.get("/api/dashboard").json()
    assert d["next_exam"]["id"] == b["id"]
    assert d["next_exam"]["days_left"] == 1

    assert client.delete(f"/api/exams/{b['id']}").status_code == 204
    assert client.delete(f"/api/exams/{b['id']}").status_code == 404


def test_exam_validation(client):
    bad = [
        {"subject": "", "date": "2026-11-19"},
        {"subject": "   ", "date": "2026-11-19"},
        {"subject": "M", "date": "19.11.2026"},
        {"subject": "M", "date": "2026-11-19", "time": "25:00"},
        {"subject": "M", "date": "2026-11-19", "difficulty": 9},
        {"subject": "x" * 81, "date": "2026-11-19"},
    ]
    for body in bad:
        assert client.post("/api/exams", json=body).status_code == 422, body
    # SQL-Injection wird als normaler Text gespeichert
    r = client.post("/api/exams", json={"subject": "M'); DROP TABLE exams;--", "date": "2026-11-19"})
    assert r.status_code == 201
    assert len(client.get("/api/exams").json()) == 1


def test_task_completion_writes_history(client):
    exam = client.post("/api/exams", json={"subject": "Physik", "date": "2026-11-19"}).json()
    conn = sqlite3.connect(settings.db_path)
    conn.execute("INSERT INTO tasks(exam_id, date, minutes, title) VALUES (?, '2026-11-16', 45, 'Optik wiederholen')", (exam["id"],))
    conn.execute("INSERT INTO tasks(exam_id, date, minutes, title) VALUES (?, '2026-11-15', 30, 'Alte Aufgabe')", (exam["id"],))
    conn.commit(); conn.close()

    d = client.get("/api/dashboard").json()
    assert d["today_summary"] == {"total": 1, "done": 0, "minutes": 45}
    assert len(d["overdue_tasks"]) == 1
    tid = d["today_tasks"][0]["id"]

    assert client.patch(f"/api/tasks/{tid}", json={"status": "done"}).json()["status"] == "done"
    d = client.get("/api/dashboard").json()
    assert d["today_summary"]["done"] == 1
    assert d["week"]["total_minutes"] == 45 and d["week"]["streak"] == 1
    assert d["subject_progress"][0]["percent"] == 60  # 45 von 75 Minuten
    assert d["overall_progress"]["done_minutes"] == 45

    client.patch(f"/api/tasks/{tid}", json={"status": "open"})
    assert client.get("/api/dashboard").json()["week"]["total_minutes"] == 0
    assert client.patch(f"/api/tasks/{tid}", json={"status": "hacked"}).status_code == 422


def test_settings_persist(client):
    s = client.get("/api/settings").json()
    assert s["briefing_time"] == "07:00" and s["ai_enabled"] is False
    r = client.put("/api/settings", json={"user_name": "Markus", "daily_minutes": 90})
    assert r.json()["user_name"] == "Markus" and r.json()["daily_minutes"] == 90
    assert client.put("/api/settings", json={"briefing_time": "7 Uhr"}).status_code == 422
    assert client.get("/api/dashboard").json()["user_name"] == "Markus"
