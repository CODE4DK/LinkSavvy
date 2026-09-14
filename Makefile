.PHONY: bootstrap dev test lint migrate seed contracts worker weekly-scheduler

BACKEND_DIR := backend
FRONTEND_DIR := frontend

# First-time setup: generate backend/.env, install dependencies, migrate,
# seed. Assumes MySQL is already installed and running locally (no
# Docker) -- see README.md for how to install it per OS. Safe to re-run.
bootstrap:
	./scripts/bootstrap.sh

# Runs the API (:8000) and web app (:5173) together. Ctrl+C stops both.
dev:
	./scripts/dev.sh

test:
	cd $(BACKEND_DIR) && uv run pytest
	cd $(FRONTEND_DIR) && npm run test -- --run

lint:
	cd $(BACKEND_DIR) && uv run ruff check . && uv run black --check . && uv run mypy app scripts tests alembic/env.py
	cd $(FRONTEND_DIR) && npm run lint && npm run typecheck

migrate:
	cd $(BACKEND_DIR) && uv run alembic upgrade head

seed:
	cd $(BACKEND_DIR) && uv run python scripts/seed.py

contracts:
	cd $(BACKEND_DIR) && uv run python scripts/export_openapi.py
	cd $(FRONTEND_DIR) && npm run generate:contracts

# Runs the background job worker loop (audits, and anything else enqueued
# to the `jobs` table). Separate from `make dev` since not every local
# session needs it running.
worker:
	cd $(BACKEND_DIR) && uv run python -m app.jobs.worker

# Polls for users whose local time is Monday 06:00 and enqueues their
# weekly_plan.generate job -- see docs/adr/0009. Requires `worker` to
# also be running to actually process what it enqueues.
weekly-scheduler:
	cd $(BACKEND_DIR) && uv run python -m app.growth.weekly_plan_scheduler
