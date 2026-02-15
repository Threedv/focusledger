#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip -q install --upgrade pip
pip -q install -r requirements.txt
python app.py
