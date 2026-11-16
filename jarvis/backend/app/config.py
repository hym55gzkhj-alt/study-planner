"""Zentrale Konfiguration. Alle Werte kommen aus Umgebungsvariablen (optional aus einer .env-Datei)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parents[2]  # .../jarvis
FRONTEND_DIR = ROOT_DIR / "frontend"


def _load_dotenv(path: Path) -> None:
    """Minimaler .env-Leser: setzt nur Variablen, die noch nicht gesetzt sind."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    tz: ZoneInfo
    db_path: Path
    anthropic_api_key: str | None
    ai_model: str
    ai_effort: str

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


def load_settings() -> Settings:
    db = Path(os.environ.get("JARVIS_DB_PATH", "data/jarvis.db"))
    if not db.is_absolute():
        db = ROOT_DIR / db
    return Settings(
        host=os.environ.get("JARVIS_HOST", "127.0.0.1"),
        port=int(os.environ.get("JARVIS_PORT", "8765")),
        tz=ZoneInfo(os.environ.get("JARVIS_TZ", "Europe/Berlin")),
        db_path=db,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        ai_model=os.environ.get("JARVIS_AI_MODEL", "claude-opus-5-5"),
        ai_effort=os.environ.get("JARVIS_AI_EFFORT", "low"),
    )


settings = load_settings()
