# LinkSavvy — Project Primer

## What this is
LinkSavvy is an AI-powered LinkedIn Command Center: a web app where a LinkedIn user optimises their profile, creates content, engages their audience, manages their career materials, and receives AI coaching. It is an assistant, not an automation tool.

## Hard compliance rule (never violate)
The codebase MUST NOT, under any circumstance:
- scrape LinkedIn, parse LinkedIn HTML, or drive a headless browser against linkedin.com
- auto-like, auto-comment, auto-connect, auto-message, or auto-post to LinkedIn
- store LinkedIn credentials

The ONLY network calls permitted to LinkedIn are to its official OAuth and API hosts, for authentication and for whatever profile fields the official API grants us. Every feature must also work for a user who never connects LinkedIn at all — this is the "parity path": upload, paste, or type. API path and parity path must reach the same capability. If a task seems to require a prohibited action, stop and say so instead of implementing it.

This rule is enforced in CI, not just by convention: `scripts/check_compliance.py` scans every source file under `apps/api/app`, `apps/api/alembic`, `apps/web/src`, and `packages/contracts/src` and fails the build if it finds a `linkedin.com` host reference outside `apps/api/app/services/linkedin.py` (the one allowlisted OAuth/API client), an import of a browser-automation library (selenium/playwright/puppeteer) outside a test file, an import of an HTML-scraping library (BeautifulSoup/bs4/cheerio), or a scraping-shaped declaration (a function, class, or variable named `scrape*`/`crawl*`). Run it locally with `python3 scripts/check_compliance.py`. If it flags something that genuinely needs a new LinkedIn endpoint, extend the OAuth/API client rather than the allowlist.

## Stack
- Monorepo: `apps/web` (React 18, Vite 5, TypeScript strict), `apps/api` (Python 3.11, FastAPI async), `packages/contracts` (TypeScript types generated from the API's OpenAPI schema).
- Database: MySQL 9.7, the sole datastore. No Redis, no Celery, no separate vector database. Background jobs use a `jobs` table plus a worker loop. Search uses MySQL FULLTEXT.
- ORM: SQLAlchemy 2.0 async + Alembic. Every schema change is a migration; no `create_all` outside tests.
- Validation: Pydantic v2 on the API, Zod on the web. Request and response models are explicit; no bare dicts cross a route boundary.
- Auth: JWT access token (15 min) in memory + rotating refresh token in an httpOnly, SameSite=Lax, Secure cookie.
- Local dev: `docker compose up` brings MySQL and MailHog; `make dev` runs both apps.

## Conventions
- Primary keys: UUIDv7 stored as `BINARY(16)`, exposed as strings. Never expose auto-increment ids.
- Tables: snake_case plural. Every table has `created_at`, `updated_at`; user-owned tables have `user_id` and a soft-delete `deleted_at`.
- Money: integer minor units plus a currency column. Never floats.
- Times: UTC in the database, ISO-8601 with offset on the wire, user timezone applied only in the UI.
- API: `/api/v1/...`, plural nouns, cursor pagination (`?cursor=&limit=`). Errors use a single envelope: `{"error": {"code": "SNAKE_CASE_CODE", "message": "human text", "details": {...}}}`. Codes are a closed enum in `app/errors.py`.
- Python: ruff + black + mypy strict. TypeScript: eslint + prettier, `strict: true`, no `any`.
- Tests live beside the code. A feature is not done until it has tests.
- Feature flags: every hub sits behind a flag in a `feature_flags` table so incomplete hubs can ship dark.

## Product vocabulary (use these exact names in code)
Hubs: Profile Hub, Content Hub, Engagement Hub, Career Hub, Growth Hub, Workspace Hub. Plus Dashboard and AI Assistant.
Core objects: `ProfileSnapshot`, `Audit`, `AuditFinding`, `Recommendation`, `HealthScore`, `ToolDefinition`, `ToolRun`, `Asset`, `Conversation`, `Subscription`, `UsageCounter`.
Roles: `user`, `pro`, `admin`.

## How to work
- Read this file at the start of every session.
- Before writing code for a phase, restate the phase's acceptance checklist and plan the commits.
- Record non-obvious decisions in `docs/adr/`.
- Never introduce a dependency on a module that a later phase is supposed to build; stub behind an interface instead.
