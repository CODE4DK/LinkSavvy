#!/usr/bin/env bash
# Runs the API and web dev servers together. Ctrl+C stops both.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }

if [ ! -f "$ROOT_DIR/apps/api/.env" ]; then
  log "apps/api/.env not found — run 'make bootstrap' first."
  exit 1
fi

# Kill every process in this script's process group on exit, so the API and
# web dev servers (and their children) never outlive Ctrl+C.
trap 'kill 0' EXIT INT TERM

log "Starting MySQL + MailHog (docker compose)"
(cd "$ROOT_DIR" && docker compose up -d --wait)

log "Starting API on http://localhost:8000"
(cd "$ROOT_DIR/apps/api" && uv run fastapi dev app/main.py --port 8000) &

log "Starting web app on http://localhost:5173"
(cd "$ROOT_DIR/apps/web" && npm run dev) &

wait
