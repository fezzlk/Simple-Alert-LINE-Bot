#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${FIRESTORE_PROJECT_ID:-simple-alert-line-bot}"

if command -v docker >/dev/null 2>&1; then
  docker compose -f docker-compose.dev.yml up -d firestore-emulator
  exit 0
fi

if command -v firebase >/dev/null 2>&1; then
  firebase emulators:start --only firestore --project "$PROJECT_ID"
  exit 0
fi

if command -v npx >/dev/null 2>&1; then
  npx --yes firebase-tools@latest emulators:start --only firestore --project "$PROJECT_ID"
  exit 0
fi

echo "firebase-tools is not installed. Install it or ensure npx is available."
exit 1
