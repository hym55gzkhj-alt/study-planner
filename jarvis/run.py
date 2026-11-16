"""Startet JARVIS:  python run.py   →   http://127.0.0.1:8765"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

import uvicorn  # noqa: E402

from app.config import settings  # noqa: E402

if __name__ == "__main__":
    print(f"\n  JARVIS online  →  http://{settings.host}:{settings.port}\n")
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, log_level="warning")
