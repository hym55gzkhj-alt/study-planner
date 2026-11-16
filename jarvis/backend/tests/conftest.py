import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Testdatenbank in einem temporären Ordner – niemals die echte Datenbank anfassen
_tmp = tempfile.mkdtemp(prefix="jarvis-test-")
os.environ["JARVIS_DB_PATH"] = str(Path(_tmp) / "test.db")
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import clock  # noqa: E402


@pytest.fixture()
def client():
    if settings.db_path.exists():
        settings.db_path.unlink()
    clock.set_now(dt.datetime(2026, 11, 16, 7, 0, tzinfo=settings.tz))
    with TestClient(app) as c:
        yield c
    clock.set_now(None)
