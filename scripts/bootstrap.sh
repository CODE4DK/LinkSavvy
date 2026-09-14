#!/usr/bin/env bash
# One-shot first-time setup: writes backend/.env with generated secrets (if
# it doesn't exist yet), creates the local MySQL database/user, installs
# dependencies for both apps, runs migrations, and seeds an admin/demo
# user. Safe to re-run -- it never overwrites an existing .env or re-seeds
# data that's already there. Requires MySQL to already be installed and
# running locally (see README.md for per-OS install instructions).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

log() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; exit 1; }

command -v uv >/dev/null 2>&1 || fail "uv is required: https://docs.astral.sh/uv/"
command -v node >/dev/null 2>&1 || fail "node (v22+) is required: https://nodejs.org/"
command -v openssl >/dev/null 2>&1 || fail "openssl is required to generate secrets"
command -v mysql >/dev/null 2>&1 || fail "mysql client is required -- install MySQL locally (see README.md)"

log "Checking MySQL is running locally"
mysqladmin ping >/dev/null 2>&1 || fail "MySQL isn't reachable on localhost -- start it first (see README.md)"

log "Creating the linksavvy database/user if they don't already exist"
mysql -u root -e "
  CREATE DATABASE IF NOT EXISTS linksavvy CHARACTER SET utf8mb4;
  CREATE USER IF NOT EXISTS 'linksavvy'@'localhost' IDENTIFIED BY 'linksavvy';
  GRANT ALL PRIVILEGES ON linksavvy.* TO 'linksavvy'@'localhost';
  FLUSH PRIVILEGES;
" 2>/dev/null || log "Could not connect as root@localhost with no password -- if the linksavvy database/user don't already exist, create them yourself (see README.md), then re-run this script."

if [ -f "$BACKEND_DIR/.env" ]; then
  log "backend/.env already exists — leaving it alone"
else
  log "Creating backend/.env with generated secrets"
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"

  jwt_secret=$(openssl rand -base64 48 | tr -d '\n')
  refresh_pepper=$(openssl rand -base64 48 | tr -d '\n')
  # Fernet keys are 32 random bytes, url-safe base64 encoded.
  encryption_key=$(openssl rand -base64 32 | tr '+/' '-_')

  tmp_env=$(mktemp)
  sed \
    -e "s#^JWT_SECRET=.*#JWT_SECRET=${jwt_secret}#" \
    -e "s#^REFRESH_TOKEN_PEPPER=.*#REFRESH_TOKEN_PEPPER=${refresh_pepper}#" \
    -e "s#^ENCRYPTION_KEY=.*#ENCRYPTION_KEY=${encryption_key}#" \
    "$BACKEND_DIR/.env" > "$tmp_env"
  mv "$tmp_env" "$BACKEND_DIR/.env"
fi

log "Installing backend dependencies (uv sync)"
(cd "$BACKEND_DIR" && uv sync)

log "Installing frontend dependencies (npm install)"
(cd "$FRONTEND_DIR" && npm install)

log "Running database migrations"
(cd "$BACKEND_DIR" && uv run alembic upgrade head)

log "Seeding feature flags and admin/demo users"
(cd "$BACKEND_DIR" && uv run python scripts/seed.py)

log "Done. Run 'make dev' to start the API (:8000) and web app (:5173)."
