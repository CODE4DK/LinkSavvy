.PHONY: dev test lint migrate seed contracts

API_DIR := apps/api
WEB_DIR := apps/web

dev:
	docker compose up -d
	( cd $(API_DIR) && uv run fastapi dev app/main.py --port 8000 ) & \
	( cd $(WEB_DIR) && npm run dev )

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
