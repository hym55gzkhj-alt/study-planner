"""Zeitfunktionen in der konfigurierten Zeitzone (testbar über set_now)."""
from __future__ import annotations

import datetime as dt

from ..config import settings

_fixed_now: dt.datetime | None = None


def now() -> dt.datetime:
    return _fixed_now or dt.datetime.now(settings.tz)


def today() -> dt.date:
    return now().date()


def set_now(value: dt.datetime | None) -> None:
    """Nur für Tests: feste Uhrzeit setzen."""
    global _fixed_now
    _fixed_now = value
