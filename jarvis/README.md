# J.A.R.V.I.S – persönlicher KI-Klausurassistent

Lokale Web-App, die Klausurtermine verwaltet und daraus tägliche Lernpläne erstellt.
Alle Daten liegen in einer SQLite-Datenbank auf deinem Computer und bleiben nach einem Neustart erhalten.

## Stand

| Schritt | Inhalt | Status |
|---|---|---|
| 1–2 | Projektstruktur, Datenbank, REST-API | ✅ |
| 3 | Dashboard (Begrüßung, Countdown, Aufgaben, Fortschritt, Woche), Klausuren verwalten, Einstellungen | ✅ |
| 4 | Klausurplan-Import (PDF, PNG, JPG, Excel) mit Bestätigung | ⏳ |
| 5 | Automatischer Lernplan | ⏳ |
| 6 | JARVIS-Chat | ⏳ |
| 7 | Tagesbericht um 07:00 Uhr mit Benachrichtigung | ⏳ |

## Voraussetzungen

- **Python 3.10 oder neuer** ([python.org](https://www.python.org/downloads/) – unter Windows beim Installieren „Add Python to PATH“ anhaken)

## Installation (einmalig)

Im Terminal (Windows: „Eingabeaufforderung“ oder PowerShell) in den Ordner `jarvis` wechseln:

```bash
cd study-planner/jarvis

# virtuelle Umgebung anlegen
python -m venv .venv

# aktivieren
#   Windows:      .venv\Scripts\activate
#   macOS/Linux:  source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r backend/requirements.txt

# Konfiguration anlegen (optional, die Standardwerte funktionieren)
#   Windows:      copy .env.example .env
#   macOS/Linux:  cp .env.example .env
```

## Starten

```bash
# (virtuelle Umgebung aktivieren, siehe oben)
python run.py
```

Dann im Browser öffnen: **http://127.0.0.1:8765**

Beenden mit `Strg + C`. Deine Daten liegen in `data/jarvis.db`.

**Auf dem Smartphone:** Setze in `.env` `JARVIS_HOST=0.0.0.0` und öffne auf dem Handy (im selben WLAN)
`http://<IP-deines-Computers>:8765`. Mach das nur in einem vertrauenswürdigen Netzwerk, denn die App hat keine Anmeldung.

## Konfiguration (`.env`)

| Variable | Standard | Bedeutung |
|---|---|---|
| `JARVIS_HOST` | `127.0.0.1` | Adresse des Servers |
| `JARVIS_PORT` | `8765` | Port |
| `JARVIS_TZ` | `Europe/Berlin` | Zeitzone für „heute“ und den Tagesbericht |
| `JARVIS_DB_PATH` | `data/jarvis.db` | Speicherort der Datenbank |
| `ANTHROPIC_API_KEY` | – | optional, für Chat und Bilderkennung (ab Schritt 4/6) |

API-Schlüssel stehen **nur** in `.env` bzw. in Umgebungsvariablen. `.env` wird nicht ins Git-Repository eingecheckt.

## Architektur

```
jarvis/
├── run.py                 Startskript (uvicorn)
├── backend/
│   ├── app/
│   │   ├── main.py        FastAPI-App, Sicherheits-Header, liefert das Frontend aus
│   │   ├── config.py      Konfiguration aus Umgebungsvariablen
│   │   ├── db.py          SQLite-Schema (exams, tasks, history, settings, briefings)
│   │   ├── schemas.py     Validierung aller Eingaben (Pydantic)
│   │   ├── routers/       REST-Endpunkte (/api/…)
│   │   └── services/      Logik: Datenzugriff, Dashboard, Zeit
│   └── tests/             pytest
├── frontend/              HTML/CSS/JavaScript-Module ohne Build-Schritt
└── data/                  SQLite-Datenbank (nicht im Git)
```

API-Dokumentation bei laufendem Server: http://127.0.0.1:8765/docs

## Tests

```bash
pip install -r backend/requirements-dev.txt
cd backend && python -m pytest -q
```

## Sicherheit

- Alle Eingaben werden serverseitig validiert (Länge, Datums- und Zeitformat, Wertebereiche).
- Nur parametrisierte SQL-Abfragen.
- Das Frontend fügt Benutzerdaten nur als Text ein (kein `innerHTML`). Eine strikte Content-Security-Policy ist aktiv.
- Der Server lauscht standardmäßig nur auf `127.0.0.1`.
- Es werden keine Klausurtermine erfunden: Termine kommen nur aus deinen Eingaben oder aus einem Import, den du bestätigst.
