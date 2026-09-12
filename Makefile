.PHONY: bootstrap dev down test lint migrate seed contracts worker

API_DIR := apps/api
WEB_DIR := apps/web

# First-time setup: docker compose up, generate apps/api/.env, install
# dependencies, migrate, seed. Safe to re-run.
bootstrap:
	./scripts/bootstrap.sh

# Runs the API (:8000) and web app (:5173) together. Ctrl+C stops both.
dev:
	./scripts/dev.sh

down:
	docker compose down

test:
	cd $(API_DIR) && uv run pytest
	cd $(WEB_DIR) && npm run test -- --run

lint:
	cd $(API_DIR) && uv run ruff check . && uv run black --check . && uv run mypy app scripts tests alembic/env.py
	cd $(WEB_DIR) && npm run lint && npm run typecheck

migrate:
	cd $(API_DIR) && uv run alembic upgrade head

seed:
	cd $(API_DIR) && uv run python scripts/seed.py

contracts:
	cd $(API_DIR) && uv run python scripts/export_openapi.py
	cd $(WEB_DIR) && npm run generate:contracts

# Runs the background job worker loop (audits, and anything else enqueued
# to the `jobs` table). Separate from `make dev` since not every local
# session needs it running.
worker:
	cd $(API_DIR) && uv run python -m app.jobs.worker
