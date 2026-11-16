#!/bin/bash
# JARVIS starten (macOS/Linux): Doppelklick (macOS) oder ./start-mac-linux.command
cd "$(dirname "$0")" || exit 1
command -v python3 >/dev/null || { echo "Python fehlt. Bitte von https://www.python.org installieren."; read -r; exit 1; }
[ -d .venv ] || { echo "Erster Start: richte JARVIS ein ..."; python3 -m venv .venv || exit 1; }
source .venv/bin/activate
python -m pip install -q -r backend/requirements.txt || exit 1
[ -f .env ] || cp .env.example .env
( sleep 2; (command -v open >/dev/null && open http://127.0.0.1:8765) || xdg-open http://127.0.0.1:8765 ) >/dev/null 2>&1 &
python run.py
