# Runbook

Operational procedures for deploying, rolling back, and responding to
incidents. LinkSavvy has not shipped to production as of Phase 10 — this
document describes the procedures the containerized apps
(`apps/api/Dockerfile`, `apps/web/Dockerfile`) and CI are built to
support, some of which (marked below) still need a first live run against
real staging infrastructure once one exists, since this repository's own
dev sandbox has no Docker daemon or MySQL server to run them against.

## Containers

- `apps/api/Dockerfile` — multi-stage: a `builder` stage resolves
  dependencies with `uv` into a virtualenv, the `runtime` stage copies
  only that venv plus source, running as a non-root `app` user. Exposes
  `8000`; its `HEALTHCHECK` polls `/ready` (round-trips the database, not
  just "the process is alive" — see `docs/slo.md`).
  Build from `apps/api`: `docker build -t linksavvy-api apps/api`.
- `apps/web/Dockerfile` — multi-stage: `builder` runs the npm workspace
  install and `vite build`, `runtime` is bare `nginx:1.27-alpine` serving
  only the built static output. `apps/web/nginx.conf.template` reverse-
  proxies `/api/` to `${API_UPSTREAM}` (nginx's built-in envsubst-on-
  startup templating substitutes it — no custom entrypoint script needed)
  and falls back to `index.html` for client-side routing.
  Build from the **repo root** (it needs the workspace lockfile and
  `packages/contracts`): `docker build -t linksavvy-web -f apps/web/Dockerfile .`.

Neither image has been build-tested in this repository's own dev sandbox
(no Docker daemon available here) — both should be built and smoke-tested
once a real Docker host is available, before the first real deploy.

## Environment configuration

Required environment variables are documented with generation
instructions in `apps/api/.env.example` — that file is the source of
truth for variable names; this section only calls out what differs by
environment:

- `ENV` — `staging` or `production` (never `development` outside a
  laptop; `development` disables `Strict-Transport-Security`, see
  `docs/security.md`).
- `DATABASE_URL` — points at the environment's own MySQL instance, never
  shared between staging and production.
- `CORS_ORIGINS` — the environment's own frontend origin(s) only.
- `EMAIL_PROVIDER` — `console`/`smtp` in dev, `resend` or `ses` in
  staging/production (see `app/notifications/email/`).
- `API_UPSTREAM` (web image only) — the API's internal address for
  nginx's reverse proxy, e.g. `http://linksavvy-api:8000`.

Secrets (`JWT_SECRET`, `REFRESH_TOKEN_PEPPER`, `ENCRYPTION_KEY`, AI/
billing provider keys) are injected by the deployment platform's own
secrets manager — never baked into an image or committed to this repo.

## Deploying

Migrations run as an explicit release step **before** the new API
version starts serving traffic, not as part of application startup (a
crash mid-migration on app boot is much harder to reason about than a
release step that either completes or the release is aborted):

1. Run `alembic upgrade head` against the target database using the
   **new** release's migration files (a release always carries forward
   whatever the previous release's migrations already applied).
2. Only once that succeeds, roll out the new API and web images.
3. Roll out API instances one at a time (or per your platform's rolling-
   update primitive), each gated on its own `/ready` passing before the
   next one starts — this is what makes the deploy zero-downtime: a
   load balancer only sends traffic to instances that are actually ready,
   and at least one old-version instance keeps serving until every new
   one is healthy.
4. Roll out the web image the same way (or, if served from a CDN/static
   host instead of the nginx container, invalidate the CDN cache for
   `index.html` only — the hashed JS/CSS chunks are immutable and never
   need invalidating, see `docs/performance.md` "Bundle budget").

Because every migration in this codebase is additive-first by
convention (add a nullable column or a new table; a later phase's
migration drops what's no longer needed once nothing reads it), the old
API version can keep running correctly against the new schema during the
rollout window — this is what makes step 3's "old and new versions
briefly serving traffic against the same, already-migrated database" safe.

## Rollback

- **App-level rollback** (the new code has a bug, but the migration was
  schema-compatible with the old version): redeploy the previous image
  tag. No database action needed if the migration was additive-only,
  which it should always be for exactly this reason.
- **Migration rollback** (a migration itself is the problem): run
  `alembic downgrade -1` against the target database, then redeploy the
  previous image tag. Every migration in this codebase has a working
  `downgrade()` — verified on every phase close-out by running
  `alembic upgrade head` then `alembic downgrade base` against a scratch
  database (see the close-out procedure this phase followed).
- Never hand-edit the database to work around a bad migration; downgrade
  through Alembic so the migration history stays the single source of
  truth for schema state.

## Backups and restore

`scripts/backup_db.sh` runs `mysqldump --single-transaction` (safe
against a live, being-written-to database) and gzips the output; it
takes `DB_HOST`/`DB_PORT`/`DB_USER`/`DB_PASSWORD`/`DB_NAME` and an
optional `BACKUP_DIR`. Schedule it nightly via whatever the deployment
platform's own cron/scheduled-job primitive is (there is no in-app
scheduler for this — it's infrastructure, not application code) and ship
its output to object storage outside the database host itself; a backup
that lives on the same disk as the database it backs up isn't a backup
against a host-level failure.

`scripts/restore_db.sh <backup-file>` restores a dump into a **new**
database by default (`linksavvy_restore_test`, never the live database
name unless `DB_NAME` is explicitly overridden) — a restore drill can
never accidentally clobber a live database through a slipped environment
variable. It prints the elapsed restore time and a sanity-checked table
count at the end.

**Restore drill log** (a tested restore is only real once it's actually
been run — this table is the record):

| Date | Backup size | Restore duration | Run by | Notes |
| --- | --- | --- | --- | --- |
| _pending_ | — | — | — | Not yet run: this repository's dev sandbox has no MySQL server or Docker daemon to run `scripts/restore_db.sh` against. **Run this drill against staging before the first production deploy**, and record the real result here — this is not optional, per the Phase 10 spec's own requirement that the restore be actually exercised, not just scripted. |

## Zero-downtime deploys

Covered inline above under "Deploying" — the two load-bearing pieces are
(1) migrations always being additive-first, so old and new code can both
run against the post-migration schema, and (2) rolling instance-by-
instance gated on `/ready`, so the load balancer never routes to an
instance that isn't actually ready to serve. Neither piece is new
infrastructure this phase needs to build; `/ready` already exists
(`app/main.py`, added in this phase's Section 4), and every migration
from Phase 1 onward already follows the additive-first convention.

## Incidents

1. Check `/ready` and the admin platform-health tab
   (`app/admin/platform_health.py`: job queue depth, dead-lettered jobs,
   circuit-breaker state, error rates) first — most incidents show up in
   one of these before a user reports them.
2. Pull the correlation id from a user's error report or a failing
   request's `X-Request-ID` response header (see
   `docs/performance.md` "Structured logging"), and grep the structured
   JSON logs for it to get every log line from that one request across
   every module it touched.
3. Follow `docs/slo.md` "Alerting" for what severity of response a given
   symptom (error rate, latency, AI unavailability) warrants.
4. For anything touching entitlements, billing state, or user data
   integrity, treat `app/billing/service.py::process_webhook_event`'s
   idempotency guarantee as the safety net: replaying a webhook (see
   below) is always safe to reach for if billing state looks wrong.

## AI provider outage

Already handled automatically — see `docs/performance.md` "Graceful
degradation when AI providers are down" and `docs/slo.md` "AI
availability". No manual intervention is needed for a single provider
being down (the gateway falls back to the other one and the circuit
breaker stops hammering the failing one); if the AI-unavailable rate
crosses the alert threshold in `docs/slo.md`, check the failing
provider's own status page before assuming it's this codebase.

## Webhook replay

A billing webhook that failed to process (visible in the admin
subscriptions tab's webhook history, `app/admin/subscriptions.py`) can be
replayed from its stored payload without needing the provider to
re-send it: `app.billing.service.reprocess_stored_event` re-parses the
already-stored `WebhookEvent.payload` (no signature to re-verify, since
that's already been verified once at the time it was first received) and
re-runs `_apply_normalised_event`. The admin UI's "replay" action on a
failed webhook row calls exactly this.

**Known caveat** (also documented in `app/billing/service.py`): replaying
an event that already fully succeeded (as opposed to one that failed
outright) can duplicate a side-effect row like `Payment` — the same
caveat every real payment provider's own "resend webhook" tooling
carries. Only replay events the webhook history shows as failed, not
ones that already succeeded.

## Monitoring setup

Not yet wired to a concrete provider (see `docs/performance.md`
"Structured logging and tracing" for why) — this is a deployment-time
decision, tracked here rather than in application code:

1. Choose an uptime monitor (e.g. a synthetic-check service) polling
   `GET /ready` from at least two regions at 1-minute intervals, alerting
   per `docs/slo.md` "Alerting"'s consecutive-failure thresholds.
2. Choose a log aggregator that can ingest the API's structured JSON
   stdout logs (`app/observability/logging.py`) and index on
   `request_id` for the correlation-id-based incident workflow above.
3. Wire OpenTelemetry export once a tracing backend is chosen — deferred
   from this phase per `docs/performance.md`, not yet a gap in this
   runbook so much as a follow-up with no target to build against yet.
