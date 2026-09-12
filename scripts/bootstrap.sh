#!/usr/bin/env bash
# One-shot first-time setup: brings up MySQL + MailHog, writes apps/api/.env
# with generated secrets (if it doesn't exist yet), installs dependencies for
# both apps, runs migrations, and seeds an admin/demo user. Safe to re-run —
# it never overwrites an existing .env or re-seeds data that's already there.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

log() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || fail "docker is required: https://docs.docker.com/get-docker/"
command -v uv >/dev/null 2>&1 || fail "uv is required: https://docs.astral.sh/uv/"
command -v node >/dev/null 2>&1 || fail "node (v22+) is required: https://nodejs.org/"
command -v openssl >/dev/null 2>&1 || fail "openssl is required to generate secrets"

log "Starting MySQL + MailHog (docker compose)"
(cd "$ROOT_DIR" && docker compose up -d --wait)

if [ -f "$API_DIR/.env" ]; then
  log "apps/api/.env already exists — leaving it alone"
else
  log "Creating apps/api/.env with generated secrets"
  cp "$API_DIR/.env.example" "$API_DIR/.env"

  jwt_secret=$(openssl rand -base64 48 | tr -d '\n')
  refresh_pepper=$(openssl rand -base64 48 | tr -d '\n')
  # Fernet keys are 32 random bytes, url-safe base64 encoded.
  encryption_key=$(openssl rand -base64 32 | tr '+/' '-_')

  tmp_env=$(mktemp)
  sed \
    -e "s#^JWT_SECRET=.*#JWT_SECRET=${jwt_secret}#" \
    -e "s#^REFRESH_TOKEN_PEPPER=.*#REFRESH_TOKEN_PEPPER=${refresh_pepper}#" \
    -e "s#^ENCRYPTION_KEY=.*#ENCRYPTION_KEY=${encryption_key}#" \
    "$API_DIR/.env" > "$tmp_env"
  mv "$tmp_env" "$API_DIR/.env"
fi

log "Installing API dependencies (uv sync)"
(cd "$API_DIR" && uv sync)

log "Installing web dependencies (npm install, workspace root)"
(cd "$ROOT_DIR" && npm install)

log "Running database migrations"
(cd "$API_DIR" && uv run alembic upgrade head)

log "Seeding feature flags and admin/demo users"
(cd "$API_DIR" && uv run python scripts/seed.py)

log "Done. Run 'make dev' to start the API (:8000) and web app (:5173)."
