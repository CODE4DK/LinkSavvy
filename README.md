# LinkSavvy

LinkSavvy is an AI-powered LinkedIn Command Center: a web app that helps a LinkedIn user optimise their profile, create content, engage their audience, manage their career materials, and receive AI coaching — as an assistant, not an automation tool.

## Local setup

Prerequisites: MySQL (installed and running locally — no Docker), Python 3.11 with [uv](https://docs.astral.sh/uv/), Node 22, `openssl`.

**Install MySQL** if you don't already have it running:

```sh
# macOS
brew install mysql && brew services start mysql

# Ubuntu/Debian
sudo apt-get install mysql-server && sudo systemctl start mysql

# Windows
# Use the MySQL installer: https://dev.mysql.com/downloads/installer/
# (or run the apt/brew steps above inside WSL2)
```

```sh
make bootstrap   # one-time: creates the local linksavvy DB/user, generates
                 # backend/.env, installs deps for both apps, runs
                 # migrations, seeds data — safe to re-run
make dev         # runs the API (:8000) and web app (:5173) together; Ctrl+C stops both
```

Then open http://localhost:5173 and log in with a seeded account:
`admin@linksavvy.dev` / `AdminPass123!` or `demo@linksavvy.dev` / `DemoPass123!`.
Verification/reset emails print to the backend's own terminal in dev
(`EMAIL_PROVIDER=console`, the default) — no mail server needed.

Other useful targets: `make test` (pytest + vitest), `make lint` (ruff,
black, mypy strict, eslint, tsc), `make contracts` (regenerate
`frontend/src/contracts` from the backend's OpenAPI schema after changing
any request/response model).

<details>
<summary>What <code>make bootstrap</code> does, step by step (and how to do it by hand)</summary>

1. Checks MySQL is reachable locally, then creates the `linksavvy`
   database and `linksavvy` user if they don't already exist (matching
   `backend/.env.example`'s `DATABASE_URL`) — if your MySQL's root account
   needs a password, create these yourself instead (see the SQL in
   `scripts/bootstrap.sh`), then re-run the script.
2. If `backend/.env` doesn't already exist, copies it from `.env.example`
   and fills in `JWT_SECRET`, `REFRESH_TOKEN_PEPPER`, and `ENCRYPTION_KEY`
   with freshly generated random values. An existing `.env` is never
   touched — edit it yourself if you need to change anything (e.g. LinkedIn
   OAuth credentials).
3. `cd backend && uv sync` — installs backend dependencies into `.venv`.
4. `cd frontend && npm install` — installs frontend dependencies; the
   frontend is a self-contained npm project with its own lockfile.
5. `cd backend && uv run alembic upgrade head` — runs migrations.
6. `cd backend && uv run python scripts/seed.py` — seeds feature flags plus
   the admin/demo users above.

`scripts/bootstrap.sh` and `scripts/dev.sh` are plain, readable bash if you'd
rather run the steps yourself or adapt them.

</details>

### Repository layout

- `backend/` — FastAPI (async SQLAlchemy 2.0, Alembic, Pydantic v2). Run
  directly with `uvicorn app.main:app --reload` from inside this folder.
- `frontend/` — Vite + React 18 + TypeScript, a self-contained npm project
  (own `package.json`/lockfile, no workspace). Run with `npm run dev` from
  inside this folder.
  - `frontend/src/contracts/` — TypeScript types generated from the
    backend's OpenAPI schema, plus hand-maintained Zod mirrors (e.g.
    `ProfileSnapshot`) for request/response shapes the frontend needs to
    validate at runtime, not just type-check. Imported via `@/contracts`;
    never hand-edit `schema.d.ts` (regenerate with `make contracts`).
- `docs/adr` — architecture decision records

Both apps are independent projects that happen to live in the same repo —
neither depends on the other at the code level. `backend/Dockerfile` and
`frontend/Dockerfile` exist for CI and deployment only; local development
never uses Docker.
