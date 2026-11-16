import datetime as dt
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path

from ..deps import get_conn
from ..schemas import TaskStatusIn
from ..services import clock, repo

router = APIRouter(prefix="/api/tasks", tags=["Aufgaben"])


@router.get("")
def list_tasks(date: dt.date | None = None, conn: sqlite3.Connection = Depends(get_conn)):
    return repo.tasks_for_date(conn, date or clock.today())


@router.patch("/{task_id}")
def set_status(body: TaskStatusIn, task_id: int = Path(ge=1), conn: sqlite3.Connection = Depends(get_conn)):
    task = repo.set_task_status(conn, task_id, body.status)
    if not task:
        raise HTTPException(404, "Aufgabe nicht gefunden")
    return task
