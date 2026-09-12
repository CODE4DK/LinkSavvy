# LinkSavvy

LinkSavvy is an AI-powered LinkedIn Command Center: a web app that helps a LinkedIn user optimise their profile, create content, engage their audience, manage their career materials, and receive AI coaching — as an assistant, not an automation tool.

## Local setup

Prerequisites: Docker, Python 3.11 with [uv](https://docs.astral.sh/uv/), Node 22.

```sh
make bootstrap   # one-time: docker compose up, generate apps/api/.env, install
                 # deps for both apps, run migrations, seed data — safe to re-run
make dev         # runs the API (:8000) and web app (:5173) together; Ctrl+C stops both
```

Then open http://localhost:5173 and log in with a seeded account:
`admin@linksavvy.dev` / `AdminPass123!` or `demo@linksavvy.dev` / `DemoPass123!`.
MailHog (verification/reset emails sent in dev) is at http://localhost:8025.

`make down` stops the docker services. Other useful targets: `make test`
(pytest + vitest), `make lint` (ruff, black, mypy strict, eslint, tsc),
`make contracts` (regenerate `packages/contracts` from the API's OpenAPI
schema after changing any request/response model).

<details>
<summary>What <code>make bootstrap</code> does, step by step (and how to do it by hand)</summary>

1. `docker compose up -d --wait` — starts MySQL 9.7 and MailHog, and waits
   for MySQL's healthcheck to pass.
2. If `apps/api/.env` doesn't already exist, copies it from `.env.example`
   and fills in `JWT_SECRET`, `REFRESH_TOKEN_PEPPER`, and `ENCRYPTION_KEY`
   with freshly generated random values (`DATABASE_URL` etc. already match
   the `docker-compose.yml` credentials). An existing `.env` is never
   touched — edit it yourself if you need to change anything (e.g. LinkedIn
   OAuth credentials).
3. `cd apps/api && uv sync` — installs API dependencies into `.venv`.
4. `cd apps/web && npm install` — installs web dependencies.
5. `cd apps/api && uv run alembic upgrade head` — runs migrations.
6. `cd apps/api && uv run python scripts/seed.py` — seeds feature flags plus
   the admin/demo users above.

`scripts/bootstrap.sh` and `scripts/dev.sh` are plain, readable bash if you'd
rather run the steps yourself or adapt them.

</details>

### Repository layout

- `apps/api` — FastAPI (async SQLAlchemy 2.0, Alembic, Pydantic v2)
- `apps/web` — Vite + React 18 + TypeScript
- `packages/contracts` — TypeScript types generated from the API's OpenAPI
  schema; the web app imports request/response types from here, never
  redeclares them
- `docs/adr` — architecture decision records
