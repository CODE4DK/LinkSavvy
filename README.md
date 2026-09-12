# LinkSavvy

LinkSavvy is an AI-powered LinkedIn Command Center: a web app that helps a LinkedIn user optimise their profile, create content, engage their audience, manage their career materials, and receive AI coaching — as an assistant, not an automation tool.

## Local setup

Prerequisites: Docker, Python 3.11 with [uv](https://docs.astral.sh/uv/), Node 22.

1. **Start MySQL and MailHog**

   ```sh
   docker compose up -d
   ```

   MailHog's web UI (for reading verification/reset emails sent in dev) is at
   http://localhost:8025.

2. **Configure the API**

   ```sh
   cd apps/api
   cp .env.example .env
   ```

   Fill in `JWT_SECRET`, `REFRESH_TOKEN_PEPPER`, and `ENCRYPTION_KEY` (the
   `.env.example` comments show one-liners to generate each). `DATABASE_URL`
   already matches the `docker-compose.yml` credentials.

3. **Install dependencies**

   ```sh
   cd apps/api && uv sync
   cd ../web && npm install
   ```

4. **Run migrations and seed data**

   ```sh
   make migrate   # alembic upgrade head
   make seed      # admin@linksavvy.dev / AdminPass123!, demo@linksavvy.dev / DemoPass123!
   ```

5. **Run both apps**

   ```sh
   make dev       # API on :8000, web on :5173 (proxies /api to :8000)
   ```

Other useful targets: `make test` (pytest + vitest), `make lint` (ruff, black,
mypy strict, eslint, tsc), `make contracts` (regenerate
`packages/contracts` from the API's OpenAPI schema after changing any
request/response model).

### Repository layout

- `apps/api` — FastAPI (async SQLAlchemy 2.0, Alembic, Pydantic v2)
- `apps/web` — Vite + React 18 + TypeScript
- `packages/contracts` — TypeScript types generated from the API's OpenAPI
  schema; the web app imports request/response types from here, never
  redeclares them
- `docs/adr` — architecture decision records
