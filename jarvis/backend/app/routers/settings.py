import sqlite3

from fastapi import APIRouter, Depends

from ..config import settings as app_settings
from ..deps import get_conn
from ..schemas import SettingsIn
from ..services import repo

router = APIRouter(prefix="/api/settings", tags=["Einstellungen"])


@router.get("")
def get_settings(conn: sqlite3.Connection = Depends(get_conn)):
    return {**repo.get_settings(conn), "ai_enabled": app_settings.ai_enabled}


@router.put("")
def save_settings(body: SettingsIn, conn: sqlite3.Connection = Depends(get_conn)):
    return {**repo.save_settings(conn, body.model_dump()), "ai_enabled": app_settings.ai_enabled}
