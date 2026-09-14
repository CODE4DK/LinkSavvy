#!/usr/bin/env bash
# Runs the API and web dev servers together. Ctrl+C stops both. Assumes
# MySQL is already installed and running locally (no Docker) -- see
# README.md for how to install and start it per OS.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; exit 1; }

if [ ! -f "$ROOT_DIR/backend/.env" ]; then
  log "backend/.env not found — run 'make bootstrap' first."
  exit 1
fi

mysqladmin ping >/dev/null 2>&1 || fail "MySQL isn't reachable on localhost -- start it first (see README.md)"

# Kill every process in this script's process group on exit, so the API and
# web dev servers (and their children) never outlive Ctrl+C.
trap 'kill 0' EXIT INT TERM

log "Starting API on http://localhost:8000"
(cd "$ROOT_DIR/backend" && uv run uvicorn app.main:app --reload --port 8000) &

log "Starting web app on http://localhost:5173"
(cd "$ROOT_DIR/frontend" && npm run dev) &

wait
