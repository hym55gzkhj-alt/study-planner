import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path

from ..deps import get_conn
from ..schemas import ExamIn
from ..services import repo

router = APIRouter(prefix="/api/exams", tags=["Klausuren"])


@router.get("")
def list_exams(upcoming: bool = False, conn: sqlite3.Connection = Depends(get_conn)):
    return repo.list_exams(conn, upcoming_only=upcoming)


@router.post("", status_code=201)
def create_exam(body: ExamIn, conn: sqlite3.Connection = Depends(get_conn)):
    return repo.create_exam(conn, body.model_dump())


@router.put("/{exam_id}")
def update_exam(body: ExamIn, exam_id: int = Path(ge=1), conn: sqlite3.Connection = Depends(get_conn)):
    exam = repo.update_exam(conn, exam_id, body.model_dump())
    if not exam:
        raise HTTPException(404, "Klausur nicht gefunden")
    return exam


@router.delete("/{exam_id}", status_code=204)
def delete_exam(exam_id: int = Path(ge=1), conn: sqlite3.Connection = Depends(get_conn)):
    if not repo.delete_exam(conn, exam_id):
        raise HTTPException(404, "Klausur nicht gefunden")
