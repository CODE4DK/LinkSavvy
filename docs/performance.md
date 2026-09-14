# Performance and reliability

## Load testing

`apps/api/loadtest/dashboard_and_tools.js` is a [k6](https://k6.io) script
covering the FRD's two named latency budgets:

- `GET /api/v1/dashboard` — p95 < 3s
- `POST /api/v1/tools/{tool_id}/run` — p95 < 10s

It runs against a real deployed environment (staging — never production)
with a seeded test account, not in this repository's CI or dev sandbox:
a meaningful run needs a live server, a MySQL instance with realistic
data volume, and (for the tool-run scenario) live AI provider
credentials, none of which CI has. See the script's own header comment
for exact invocation. `docs/runbook.md` covers the staging setup this
depends on.

Backend query-latency budgets that *can* run in CI (no live server, no
network) exist as ordinary pytest assertions instead, seeding realistic
row counts and asserting on wall-clock time or query count directly:

- `apps/api/tests/workspace/test_performance.py` — Workspace search over
  5,000 seeded assets stays under its latency budget.
- `apps/api/tests/test_dashboard_router.py::test_dashboard_query_count_does_not_grow_with_recommendation_volume` —
  the dashboard aggregate's query count is constant regardless of how
  much recommendation history a user has (the N+1 query pattern this
  guards against is a much more common p95 killer than raw row count).

## Index review

LinkSavvy hasn't shipped to production, so there is no real slow query
log to mine yet — this review instead cross-referenced every
`select`/`update`/`delete` `.where()`/`.order_by()` clause in `app/**/*.py`
against the indexes actually declared in `app/models/*.py` and
`alembic/versions/*.py`, looking for a query pattern relying on nothing
but a table scan or a single-column FK index.

The first pass of this review, checked only against the ORM models,
found nine apparent gaps. Verifying the resulting migration against a
real MySQL instance (the close-out procedure's `alembic upgrade head`
step — SQLite, what the test suite runs against, doesn't enforce enough
to have caught this) turned out to be essential: four of those nine
already existed, created by earlier phases' own migrations directly via
`op.create_index` with no corresponding `Index()` ever added to the ORM
model — a real, separate gap in this codebase's model/migration parity,
just not the one this review set out to fix. `docs/adr/0012` and the
close-out procedure it's part of exist specifically to catch this class
of thing before it reaches a real deploy. The eight genuinely new
indexes below actually shipped in `0021_performance_indexes.py`; the
other four were fixed by adding the missing `Index()` declaration to
their model instead (no new migration needed, since the index itself
was already there):

| Table | Index | Status | Query it serves |
| --- | --- | --- | --- |
| `notifications` | `(user_id, read_at, created_at)` | New (`0021`) | Notification centre feed: unread-first, newest-first, one user (`app/notifications/service.py`) — supersedes two narrower pre-existing indexes (`ix_notifications_user_created`, `ix_notifications_user_unread`) for this specific query, though both are left in place |
| `login_attempts` | `(email_normalized, attempted_at)`, `(ip_hash, attempted_at)` | New (`0021`) | Login/register rate limiting, checked on every attempt (`app/services/rate_limit.py`) |
| `refresh_tokens` | `(user_id, revoked_at)` | New (`0021`) | Session listing/revocation (`app/services/sessions.py`) |
| `subscriptions` | `(status, plan, current_period_end)`, `(status, plan, updated_at)` | New (`0021`) | The billing period sweep's two scans (`app/billing/period_sweep.py`) |
| `subscriptions` | `(provider, provider_subscription_id)` | **Already existed** (`0017_billing.py`) | Webhook-to-subscription lookup (`app/billing/service.py`) — this review rediscovered the same need independently |
| `resumes` | `(user_id, created_at)` | New (`0021`) | Resume list (`app/career/service.py`) |
| `resumes` | `(user_id, is_active)` | **Already existed** (`0011_resume_pipeline.py`), model declaration added this phase | Activation (deactivating a user's other resumes) |
| `resume_matches` | `(user_id, created_at)` | New (`0021`) | Match history list (`app/career/service.py`) |
| `content_plans` | `(user_id, status)` | New (`0021`) | "What have I posted" lookup (`app/content/content_history.py`) |
| `content_plans` | `(user_id, planned_for)` | **Already existed** (`0010_content_plans.py`), model declaration added this phase | Calendar date-range view (`app/content/calendar_service.py`) |
| `growth_goals` | `(user_id, status)` | **Already existed** (`0012_growth_plans_and_goals.py`), model declaration added this phase | Active-goal lookup (`app/growth/goals.py`) |
| `weekly_plans` | `(user_id, week_start)`, unique | **Already existed** as `ux_weekly_plans_user_week` (`0012_growth_plans_and_goals.py`), model declaration corrected this phase (it previously named and described a different, non-existent index) | Previous-week reflection lookup (`app/growth/weekly_plan.py`) |

Every other high-traffic query pattern checked (jobs, tool runs, assets,
audits, AI invocations, feature flags) already had a supporting index
from its own phase's migration — `ai_invocations`
(`ix_ai_invocations_user_created`) was the model this review's naming
convention followed.

The same real-MySQL verification also caught genuine bugs across earlier
phases' migrations that had never been exercised against MySQL before
(the whole test suite runs against SQLite, which enforces none of this):

- Migration 0012 declared a literal `server_default=""` on a `TEXT`
  column, which MySQL rejects outright (`Error 1101`).
- Migration 0007's downgrade dropped an index before the foreign key
  constraint that depended on it, instead of after — MySQL refuses to
  drop an index still backing one of the table's own foreign keys
  (`Error 1553`).
- Eighteen migrations, from `0001_initial_schema.py` onward, dropped an
  index immediately before dropping the table that index belonged to —
  the exact same `Error 1553` as above, hit whenever that index happened
  to be the sole one covering a foreign-keyed column. Dropping a table
  already removes its indexes, so every one of these calls was both
  redundant and, some of the time, actively broken; all were removed.

All of the above are fixed in place, not via a new migration — none of
them has ever successfully completed a downgrade against real MySQL, so
there is no live schema state anywhere to migrate away from, and an
in-place fix is the correct move per `docs/runbook.md`'s own rule
against editing an already-*shipped* migration (these were never
shipped in the sense that matters: never applied to a real, running
database). This is exactly the class of bug the close-out procedure's
`alembic upgrade head` / `downgrade base` verification step exists to
catch before a real deploy hits it — see `docs/adr/0012-production-topology.md`.

## HTTP caching

FastAPI has no built-in conditional-request support, so it's opt-in per
endpoint via `app/http_cache.py::etag_or_none` rather than a blanket
middleware — most of this API's responses are per-user, frequently
changing, and would only pay ETag-computation cost for no benefit.
`GET /api/v1/tools` (`app/routers/tools.py::list_tools`) is the first
endpoint wired up: it computes an ETag over the response body, returns a
bare `304 Not Modified` when the client's `If-None-Match` still matches,
and sets `Cache-Control: private, max-age=0, must-revalidate` so a
browser or SDK always revalidates rather than serving a stale list
without asking. The same `etag_or_none` call is the pattern to reuse for
any other read-heavy, rarely-changing endpoint (see
`tests/test_tools_router.py::test_list_tools_supports_conditional_get`).

## Frontend code splitting

`apps/web/src/routes/router.tsx` loads every leaf page through React
Router's `lazy` route field (`lazy: () => import(...).then(m => ({
Component: m.PageName }))`) instead of a top-level import, so Vite emits
one chunk per page instead of one monolithic bundle. Before this change
every route's code shipped on first load regardless of which page was
requested; after it, `npm run build` in `apps/web` produces dozens of
small per-page chunks (roughly 0.4 kB to 17 kB each) alongside a single
shared entry chunk. Layout and guard components (`AppShell`,
`RequireAuth`, `RequireAdmin`) stay eagerly imported since they're small
and needed on every route regardless.

## Bundle budget

`apps/web/scripts/check-bundle-budget.mjs` gzips the built entry chunk
and fails if it exceeds 150 kB (current actual size: ~104-107 kB gzip,
depending on the build — see the script's own output). It deliberately
only measures the entry chunk, not route chunks: a big page nobody has
opened yet shouldn't fail CI, only the bytes every visitor pays on first
load regardless of which page they land on. Wired into CI as
`npm run build && npm run check:bundle-budget` in the `web` job
(`.github/workflows/ci.yml`). Raising the budget is a deliberate,
recorded decision — see the script's own comment for the process.

## Image optimization

There is currently no user-facing image content in the web app to
optimize: no `<img>` tag exists anywhere in `apps/web/src`, and the one
avatar field on `User` (`avatar_url`) stores an externally-hosted URL —
this app never re-hosts or resizes it, consistent with the LinkedIn
compliance rule against scraping or re-serving LinkedIn-sourced media.
The one place the backend generates binary image content is the carousel
PNG export (`app/content/carousel_png.py`, Pillow-rendered, on-demand
download rather than a repeatedly-served asset), which now saves with
`optimize=True` for a smaller file with no quality loss. If a future
phase adds user-uploaded images (e.g. custom carousel backgrounds), this
section should be revisited with real optimization (resizing, format
negotiation) at that point — building it now against no real content
would be premature.

## Graceful degradation when AI providers are down

Already built and tested from Phase 3, not new to this phase:
`app/ai/gateway.py::_call_with_fallback` tries the primary provider
(unless its circuit breaker — `app/ai/circuit_breaker.py` — is already
open), falls back to the secondary provider on failure, and raises a
clean `AIProviderUnavailable` (mapped to `502 AI_PROVIDER_UNAVAILABLE`,
never a raw 500) only if *both* fail.
`tests/ai/test_gateway.py::test_both_providers_failing_raises_and_releases_quota`
disables both providers by making each raise on every retry attempt and
asserts the gateway degrades cleanly — including releasing the quota
reservation it had taken, so a user isn't charged usage for a request
that never completed. See `docs/slo.md` "AI availability" for how this
is tracked as an ongoing SLO rather than a one-time test.

## Structured logging and tracing

`app/observability/logging.py` configures the root logger to emit
single-line JSON (timestamp, level, logger name, message, plus any
`extra={...}` fields a call site already passes — cost/tokens/outcome
for AI invocations, job ids for the worker, etc.). Every response also
carries a per-request correlation id: `app/middleware/correlation_id.py`
reuses an inbound `X-Request-ID` header if a proxy already set one,
otherwise generates one, stores it in a `contextvar` for the duration of
the request so every log line emitted while handling it includes
`request_id`, and echoes it back as a response header — the single value
to grep a distributed log stream for when chasing one failing request.
This correlation id is deliberately distinct from the AI gateway's own
`correlation_id` (`app/ai/gateway.py`), which identifies one AI
invocation and can outlive a single HTTP request (retries, background
jobs); a log line inside an AI call carries both.

Full distributed tracing (OpenTelemetry spans across the API, the job
worker, and outbound AI/billing provider calls, exported to a tracing
backend) is not wired up in this phase — it needs a concrete deployment
target (which OTLP collector, which backend) that doesn't exist yet for
LinkSavvy. The correlation-id-tagged structured logs above are the
practical substitute until that target is chosen; `docs/runbook.md`
tracks OpenTelemetry wiring as a deployment-time follow-up, not a code
gap in this repository.

## Uptime and alerting

See `docs/slo.md` for the actual uptime/latency/error-rate targets and
alert thresholds. `GET /ready` (`app/main.py`) is what an external
uptime monitor should poll — unlike `/health`, it round-trips the
database, so it fails the moment the app can't actually serve a real
request.
