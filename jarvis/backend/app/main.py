"""JARVIS – FastAPI-Anwendung. Liefert die REST-API unter /api und das Frontend unter /."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR, settings
from .db import init_db
from .routers import dashboard, exams, settings as settings_router, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.db_path)
    yield


app = FastAPI(title="JARVIS API", version="0.1.0", lifespan=lifespan)

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


for r in (dashboard.router, exams.router, tasks.router, settings_router.router):
    app.include_router(r)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
