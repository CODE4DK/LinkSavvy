# 13. Drop monorepo tooling and Docker for local development

Date: 2026-09-14

## Status

Accepted

## Context

The repository was structured as an npm-workspace monorepo (`apps/api`,
`apps/web`, `packages/contracts`) with Docker Compose providing local
MySQL and MailHog. This gave correct, working local dev, but added
concepts (npm workspaces, a shared package with its own `package.json`,
Docker as a prerequisite) that weren't earning their keep for a
two-service project with no other consumers of the shared package, and
made the project harder to explain to someone unfamiliar with monorepo
tooling.

`packages/contracts` was real, working code (generated OpenAPI types plus
a couple of hand-written Zod schemas), not dead weight — but it was
consumed by exactly one thing: `apps/web`. A separate npm workspace
package is the right shape when multiple independent consumers share
code; with a single consumer, it's just indirection.

Separately, `app/services/email.py` (verification/reset email) called
`aiosmtplib.send()` unconditionally, bypassing the `EMAIL_PROVIDER`
setting the newer `app/notifications/email/` module already respected
(defaulting to a `console` sender that logs instead of sending). That
made MailHog a hard requirement for local dev's registration flow, not
just a convenience.

## Decision

- Renamed `apps/api` → `backend/` and `apps/web` → `frontend/`, each a
  fully independent project (own dependency manager, own lockfile). Not
  nested under `apps/` any further, since there are only two and the
  extra directory level wasn't adding clarity.
- Moved `packages/contracts/src/*` into `frontend/src/contracts/`,
  rewriting its 60 import sites from `@linksavvy/contracts` to `@/contracts`
  (the alias already used for everything else under `frontend/src`).
  Deleted `packages/`, the root `package.json`'s npm-workspaces array, and
  the root `package.json`/`package-lock.json` entirely — `frontend/` now
  has its own standalone lockfile.
- Fixed `app/services/email.py` to route through
  `app.notifications.email.registry.get_email_sender()`, the same
  `EMAIL_PROVIDER`-selected sender the newer notification code already
  used. Local dev now needs no mail server at all by default.
- Removed `docker-compose.yml` and the root `.dockerignore` (both now
  unused) from the local dev path. `make bootstrap`/`make dev` create and
  check a natively-installed local MySQL instead of starting a container.
  `backend/Dockerfile` and `frontend/Dockerfile` are unchanged in
  substance (each already only ever ran `uvicorn`/serves a Vite build, not
  a dev server) and are kept for CI and deployment, now building from
  their own folder as context (`frontend/Dockerfile` no longer needs the
  repo root as build context, since it no longer depends on a sibling
  workspace package).
- `docs/adr/*.md` predating this change keep their old path references
  as written — they're dated decision records, not living docs.

## Consequences

- A new contributor installs MySQL once (Homebrew/apt/the MySQL
  installer) instead of running `docker compose up` — genuinely more
  manual for that one step, the explicit tradeoff of "no Docker required"
  for local development.
- `uvicorn app.main:app --reload` and `npm run dev`, run directly from
  `backend/` and `frontend/`, are now the actual, complete local dev
  loop — nothing about them was hiding a workspace-only build step.
- Regenerating contracts after an API schema change is still `make
  contracts`, now writing directly into `frontend/src/contracts/` instead
  of a sibling package.
- CI and the Docker image builds are otherwise unaffected: same jobs,
  same checks, only their working directories and image-build contexts
  changed to match the new folder names.
