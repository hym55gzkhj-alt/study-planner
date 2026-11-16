@echo off
REM JARVIS starten (Windows): Doppelklick auf diese Datei
cd /d "%~dp0"
where python >nul 2>nul || (echo Python fehlt. Bitte von https://www.python.org installieren ^(Haken bei "Add Python to PATH"^). & pause & exit /b 1)
if not exist .venv (
  echo Erster Start: richte JARVIS ein ...
  python -m venv .venv || (pause & exit /b 1)
)
call .venv\Scripts\activate.bat
python -m pip install -q -r backend\requirements.txt || (pause & exit /b 1)
if not exist .env copy .env.example .env >nul
start "" http://127.0.0.1:8765
python run.py
pause
