# 12. Production topology

Date: 2026-12-19

## Status

Accepted

## Context

Phase 10 is the first phase that has to say something concrete about how
LinkSavvy actually runs outside a developer's laptop: what a deploy looks
like, how rate limiting and background jobs behave once there's more
than one process, and what observability exists before a real incident
forces the question. CLAUDE.md rules out Redis and any datastore beyond
MySQL, which shapes several of these decisions directly rather than
leaving them open. This ADR records the topology those constraints led
to, and — as honestly as ADR 0008's "no live LinkedIn app" disclosure —
which pieces are designed-but-unverified because this development
environment has no Docker daemon or MySQL server of its own to test
them against.

## Decisions

**Two containers, not one.** `apps/api/Dockerfile` (uv-built Python
venv, non-root runtime user) and `apps/web/Dockerfile` (Vite build
served by bare nginx) are independent images with independent deploy
cadences — a web-only content fix doesn't need an API redeploy and vice
versa. The web image's nginx reverse-proxies `/api/` to the API service
via `${API_UPSTREAM}`, substituted at container start through nginx's
own built-in envsubst-on-templates mechanism rather than a custom
entrypoint script, keeping the image itself free of any
environment-specific value.

**Rate limiting stays in-process and per-worker, not centralized.**
`app/middleware/rate_limit.py`'s token buckets are plain in-memory
dictionaries, explicitly following `app/ai/circuit_breaker.py`'s own
established "per-process, not durable" trade-off from Phase 3. The
alternative — a shared limiter — would need Redis or a MySQL-backed
counter table hit on every single request, either violating CLAUDE.md's
"MySQL is the sole datastore, no Redis" rule or adding real per-request
latency to every endpoint for a feature whose worst failure mode (a
burst briefly getting through on a freshly started worker, or a
limit being counted separately per worker instead of globally) is cheap
compared to that cost. A multi-instance production deployment should
treat this as one defense-in-depth layer and put a shared, durable
limiter (a CDN or API gateway's own rate limiting) in front of it —
recorded as a real gap in `docs/security.md`, not silently assumed away.

**Background jobs are a `jobs` table plus polling worker processes, not
a message queue.** This was decided in Phase 4 (`app/jobs/`), not this
phase, but Phase 10's containerization makes the consequence concrete:
the worker (`python -m app.jobs.worker`) runs as its own container/
process, separate from the API's request-handling containers, scaled
independently. Multiple worker processes polling the same `jobs` table
is safe by construction (`SELECT ... FOR UPDATE SKIP LOCKED`-style
leasing — see Phase 4's own ADR), so horizontal worker scaling needs no
new coordination mechanism this phase has to invent.

**Structured JSON logs plus a request-correlation id, not
OpenTelemetry, is this phase's actual observability story.**
`app/observability/logging.py` and
`app/middleware/correlation_id.py` give every log line a `request_id`
and every response the same value as a header — the concrete, working
piece. Full distributed tracing (spans across the API, the worker, and
outbound provider calls, exported to a tracing backend) needs a chosen
OTLP collector and backend this project doesn't have yet; building
trace instrumentation against no real export target would be
speculative work with nothing to verify it against. `docs/performance.md`
and `docs/runbook.md` both record this as a deliberate deferral with a
concrete trigger (once a backend is chosen) rather than a silently
dropped requirement.

**Migrations run as an explicit release step, before the new version
serves traffic — never inside application startup.** Every migration in
this codebase has been additive-first since Phase 1 (a new nullable
column or table, never a destructive change in the same release that
also depends on it), which is what makes `docs/runbook.md`'s rolling,
instance-by-instance deploy safe: an old-version instance can keep
serving correctly against an already-migrated schema for the brief
window until every instance is on the new version. This wasn't a new
decision this phase had to make — it's Phase 1's own migration
convention — but this phase is the first to depend on it explicitly for
zero-downtime deploys, so it's recorded here as load-bearing.

**Backup and restore are scripts, not a managed feature, and the
restore drill is honestly logged as not-yet-run.**
`scripts/backup_db.sh`/`restore_db.sh` wrap `mysqldump`/`mysql` directly
— no managed-database-specific tooling, since which managed MySQL
offering (if any) production runs on isn't decided yet, and a script
built against a specific provider's snapshot API would need rewriting
the moment that decision is made anyway. The Phase 10 spec's own
requirement was that the restore be *actually exercised*, not just
scripted; this development sandbox has no MySQL server or Docker daemon
to run that drill against, so `docs/runbook.md`'s restore-drill log
records this as pending with an explicit instruction to run it against
staging before the first production deploy, rather than fabricating a
result.

## Consequences

- Scaling the API horizontally is safe today; scaling it across
  multiple hosts without a shared rate limiter in front means the
  *effective* rate limit is `configured limit × instance count` — an
  accepted, disclosed gap until a gateway-level limiter is added.
- Worker scaling is already coordination-free; no change needed when a
  future phase needs more job throughput.
- The two Docker images have not been build-tested in this repository's
  own environment — the new `docker` CI job (`.github/workflows/ci.yml`)
  is the first real verification they build at all, since GitHub
  Actions runners have a Docker daemon this sandbox does not.
- Distributed tracing remains a documented follow-up, not a partial or
  fake implementation — nothing in this codebase claims OpenTelemetry
  coverage it doesn't have.
- The next team member to actually deploy this needs to run the restore
  drill and record its real duration before that deploy is safe to call
  "backed up" in anything but name.
