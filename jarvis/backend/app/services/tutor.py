"""KI-Lernpartner über die Anthropic-API (Schlüssel nur aus der Umgebungsvariable)."""
from __future__ import annotations

from collections.abc import Iterator

import anthropic

from ..config import settings

PERSONA = """Du bist J.A.R.V.I.S, der persönliche Lernassistent eines Schülers der 11. Klasse \
an einem beruflichen Gymnasium in Hessen. Du sprichst Deutsch, duzt den Schüler, bist freundlich, \
motivierend und präzise – ein bisschen wie ein höflicher, kluger Butler.

Regeln:
- Antworte kurz und gut lesbar (Absätze, Listen, **fett** für Schlüsselbegriffe). Kein HTML.
- Für Fragen zu Klausuren, Terminen, Aufgaben und Fortschritt nutzt du NUR die Daten im Abschnitt \
"Gespeicherte Daten". Erfinde niemals Klausurtermine, Uhrzeiten oder Themen. Fehlt eine Information, sag das.
- Bei fachlichen Fragen erklärst du altersgerecht auf Oberstufenniveau, mit Beispielen. \
Wenn du dir bei einem Fakt unsicher bist, sag das offen.
- Hilf beim Lernen, statt Hausaufgaben einfach abzunehmen: rege zum Mitdenken an.
- Wenn du einen Lernplan vorschlägst, berücksichtige die verfügbare Lernzeit, die Nähe der Klausuren, \
den Lernbedarf (1–5) und Pausen (z. B. 45 Minuten lernen, 10 Minuten Pause)."""

MODES = {
    "chat": "Modus: Freies Gespräch. Beantworte die Frage des Schülers.",
    "explain": "Modus: Erklären. Erkläre das gewünschte Thema Schritt für Schritt: erst die Kernidee in "
               "2–3 Sätzen, dann Details, ein konkretes Beispiel und zum Schluss eine kurze Verständnisfrage.",
    "quiz": "Modus: Abfragen (Quiz). Stelle genau EINE Frage auf einmal (abwechselnd offen oder Multiple Choice "
            "mit A–D) und warte auf die Antwort. Bewerte jede Antwort kurz (richtig/teilweise/falsch), erkläre den "
            "Fehler und stelle dann die nächste Frage. Steigere langsam die Schwierigkeit. Nach 5 Fragen gibst du "
            "eine kurze Auswertung mit Themen zum Wiederholen.",
    "cards": "Modus: Karteikarten. Erstelle 8 Karteikarten im Format **Vorderseite:** … / **Rückseite:** … "
             "zu den wichtigsten Begriffen des Themas. Halte die Rückseiten kurz.",
    "summary": "Modus: Zusammenfassung. Erstelle einen kompakten Lernzettel: wichtigste Begriffe, "
               "Zusammenhänge, typische Klausurfragen und häufige Fehler.",
}


class TutorError(Exception):
    pass


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key, max_retries=2, timeout=120)


def stream_reply(history: list[dict], data_text: str, mode: str, subject: str | None) -> Iterator[str]:
    """Liefert die Antwort Stück für Stück. Wirft TutorError mit verständlicher Meldung."""
    focus = f"\nFach/Thema im Fokus: {subject}" if subject else ""
    system = [
        {"type": "text", "text": PERSONA, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": f"{MODES.get(mode, MODES['chat'])}{focus}\n\nGespeicherte Daten:\n{data_text}"},
    ]
    try:
        with _client().beta.messages.stream(
            model=settings.ai_model,
            max_tokens=8000,
            system=system,
            messages=history,
            output_config={"effort": settings.ai_effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            for text in stream.text_stream:
                yield text
            final = stream.get_final_message()
        if final.stop_reason == "refusal":
            yield "\n\n_Diese Anfrage kann ich leider nicht beantworten. Formuliere sie bitte anders._"
        elif final.stop_reason == "max_tokens":
            yield "\n\n_(Antwort gekürzt – frag nach, wenn ich weitermachen soll.)_"
    except anthropic.AuthenticationError as e:
        raise TutorError("Der API-Schlüssel ist ungültig. Prüfe ANTHROPIC_API_KEY in der .env-Datei.") from e
    except anthropic.PermissionDeniedError as e:
        raise TutorError("Der API-Schlüssel hat keinen Zugriff auf dieses Modell.") from e
    except anthropic.RateLimitError as e:
        raise TutorError("Zu viele Anfragen gerade. Warte kurz und versuch es noch einmal.") from e
    except anthropic.BadRequestError as e:
        raise TutorError(f"Die Anfrage wurde abgelehnt: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise TutorError(f"Der KI-Dienst meldet einen Fehler ({e.status_code}). Versuch es später erneut.") from e
    except anthropic.APIConnectionError as e:
        raise TutorError("Keine Verbindung zum KI-Dienst. Bist du online?") from e
