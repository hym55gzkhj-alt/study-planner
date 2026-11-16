import sqlite3

from fastapi import APIRouter, Depends

from ..deps import get_conn
from ..services import dashboard

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard")
def get_dashboard(conn: sqlite3.Connection = Depends(get_conn)):
    return dashboard.build(conn)


@router.get("/health")
def health():
    return {"status": "online", "name": "JARVIS"}
