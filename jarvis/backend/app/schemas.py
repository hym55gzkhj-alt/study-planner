"""Eingabe-Validierung. Alles, was vom Browser kommt, läuft durch diese Modelle."""
from __future__ import annotations

import datetime as dt
import re

from pydantic import BaseModel, Field, field_validator

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _clean_text(v: str) -> str:
    # Steuerzeichen entfernen, Leerraum normalisieren
    v = "".join(ch for ch in v if ch == "\n" or ch >= " ")
    return v.strip()


def _check_time(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    if not TIME_RE.match(v):
        raise ValueError("Uhrzeit muss im Format HH:MM sein")
    return v


class ExamIn(BaseModel):
    subject: str = Field(min_length=1, max_length=80)
    date: dt.date
    time: str | None = None
    notes: str = Field(default="", max_length=1000)
    difficulty: int = Field(default=3, ge=1, le=5)

    @field_validator("subject", "notes")
    @classmethod
    def _texts(cls, v: str, info) -> str:
        v = _clean_text(v)
        if info.field_name == "subject" and not v:
            raise ValueError("Fach darf nicht leer sein")
        return v

    @field_validator("time")
    @classmethod
    def _time(cls, v: str | None) -> str | None:
        return _check_time(v)

    @field_validator("date")
    @classmethod
    def _plausible_date(cls, v: dt.date) -> dt.date:
        if not (2000 <= v.year <= 2100):
            raise ValueError("Datum außerhalb des gültigen Bereichs")
        return v


class Exam(ExamIn):
    id: int
    source: str
    days_left: int


class TaskStatusIn(BaseModel):
    status: str = Field(pattern="^(open|done|skipped)$")


class SettingsIn(BaseModel):
    user_name: str | None = Field(default=None, max_length=40)
    class_name: str | None = Field(default=None, max_length=20)
    daily_minutes: int | None = Field(default=None, ge=0, le=720)
    session_minutes: int | None = Field(default=None, ge=15, le=180)
    break_minutes: int | None = Field(default=None, ge=0, le=60)
    study_start: str | None = None
    briefing_time: str | None = None
    rest_weekdays: str | None = Field(default=None, pattern=r"^([0-6](,[0-6])*)?$")

    @field_validator("study_start", "briefing_time")
    @classmethod
    def _times(cls, v: str | None) -> str | None:
        return _check_time(v)

    @field_validator("user_name", "class_name")
    @classmethod
    def _texts(cls, v: str | None) -> str | None:
        return _clean_text(v) if v is not None else v


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="chat", pattern="^(chat|explain|quiz|cards|summary)$")
    subject: str | None = Field(default=None, max_length=80)

    @field_validator("message", "subject")
    @classmethod
    def _texts(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        v = _clean_text(v)
        if info.field_name == "message" and not v:
            raise ValueError("Nachricht darf nicht leer sein")
        return v or None
