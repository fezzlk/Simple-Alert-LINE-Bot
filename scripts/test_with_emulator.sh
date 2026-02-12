#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${FIRESTORE_PROJECT_ID:-simple-alert-line-bot}"
EMULATOR_HOST="${FIRESTORE_EMULATOR_HOST:-localhost:8085}"

export FIRESTORE_PROJECT_ID="$PROJECT_ID"
export FIRESTORE_EMULATOR_HOST="$EMULATOR_HOST"

venv/bin/python -m pytest -q
