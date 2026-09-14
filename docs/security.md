# Security

This document is the reference for how LinkSavvy protects the app and its
users, and the record of the OWASP Top 10 pass done for Phase 10. Where a
control lives in code, this doc points at the module rather than
duplicating its logic — read the module for the exact behavior.

## OWASP Top 10 (2021) pass

| # | Category | Status | Notes |
| --- | --- | --- | --- |
| A01 | Broken Access Control | Addressed | Every route requires `get_current_user`/`get_current_admin` (`app/deps.py`) except the deliberately public auth/health endpoints. Ownership is checked at the query level (`WHERE user_id = :current_user`), never inferred from a client-supplied id. Admin routes (`app/routers/admin.py`) require role `admin`. Impersonation is read-only, enforced at the transport level (`app/middleware/impersonation_guard.py`) — see "Impersonation" below. |
| A02 | Cryptographic Failures | Addressed | Passwords hashed with Argon2id (`app/security/passwords.py`). Refresh tokens are opaque, hashed at rest with a server-side pepper (`app/security/jwt.py`), never stored raw. Sensitive columns (OAuth tokens, uploaded résumés, pasted profile text) are encrypted at rest with Fernet (`app/security/crypto.py`) — see "Encryption at rest" below. TLS termination is the deploy environment's job (see `docs/runbook.md`); HSTS is sent in production (`app/middleware/security_headers.py`). |
| A03 | Injection | Addressed | SQLAlchemy Core/ORM with bound parameters everywhere; no raw string-interpolated SQL in the codebase. Pydantic v2 validates every request body; MySQL FULLTEXT search queries go through SQLAlchemy's `match` construct, not string concatenation. |
| A04 | Insecure Design | Addressed | The billing webhook is the sole source of truth for entitlements (never a client redirect) — see `app/billing/service.py`. Rate limiting and CSRF are defense-in-depth on top of bearer-token auth, not a substitute for it. The LinkedIn compliance guard (`scripts/check_compliance.py`) is a design-level control enforced in CI, not just code review. |
| A05 | Security Misconfiguration | Addressed | `app/middleware/security_headers.py` sets CSP (no `unsafe-inline`), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and HSTS in production. CORS is configured from an explicit allow-list (`settings.cors_origins`), never `*` with credentials. Debug/playground endpoints are gated behind an admin role *and* a feature flag (`app/routers/internal.py::require_playground_enabled`). |
| A06 | Vulnerable and Outdated Components | Addressed | `pip-audit` (Python) and `npm audit` (web) run in CI on every push — see "CI security scanning" below. |
| A07 | Identification and Authentication Failures | Addressed | JWT access tokens are short-lived (15 min) and never persisted; refresh tokens rotate on every use and the whole family is revoked on reuse detection (`app/routers/auth.py`, `test_reused_refresh_token_revokes_family`). Login/reset endpoints sit behind the `auth` rate-limit class (tighter burst allowance than any other class). |
| A08 | Software and Data Integrity Failures | Addressed | Webhook signatures are verified before any event is trusted (`app/billing/providers/{stripe,razorpay}.py::parse_webhook`); admin webhook replay re-parses the *stored* payload rather than accepting a re-submitted one from the client. CI pins exact dependency versions (`uv.lock`, `package-lock.json`). |
| A09 | Security Logging and Monitoring Failures | Addressed | Structured logs carry a correlation id per request/job (see `docs/performance.md` for the tracing story); AI invocation cost/latency/error rates are visible in the admin AI-ops tab (`app/admin/ai_ops.py`); the platform-health tab surfaces job-queue depth, dead letters, and circuit-breaker state (`app/admin/platform_health.py`). See "What never reaches logs" below for the flip side of this control. |
| A10 | Server-Side Request Forgery | Addressed | The only outbound calls the API makes to a caller-influenced host are billing provider SDK calls (fixed, allow-listed hostnames baked into the SDKs) and the LinkedIn OAuth/API client (`app/services/linkedin.py`, itself the one allowed exception to the no-scraping rule). Nothing in the codebase fetches a URL supplied in a request body. |

## Rate limiting

`app/middleware/rate_limit.py` implements per-IP and per-user token
buckets, keyed by an endpoint class (`auth`, `admin`, `ai`, `webhook`,
`default`) matched from the request path. A blocked request gets `429`
with a `Retry-After` header and the standard error envelope
(`RATE_LIMITED`). Per-user buckets get roughly double the per-IP capacity
for the same class, so a shared office IP doesn't starve individually
authenticated users of their own allowance.

This is deliberately **in-memory and per-process**, the same trade-off
`app/ai/circuit_breaker.py` already makes: CLAUDE.md rules out adding
Redis just to share this state across workers, and the failure mode of a
burst briefly getting through on a freshly started worker is cheap. A
production deployment running multiple workers or instances should treat
this as one layer and put a shared, durable limiter (a CDN or API
gateway) in front of it — see `docs/runbook.md`.

## CSRF protection

Exactly two endpoints authenticate purely from a cookie with no bearer
token: `POST /auth/refresh` and `POST /auth/logout`. Every other mutating
endpoint requires an `Authorization: Bearer` header, which a cross-site
request can't attach, so CSRF has no purchase there.

Those two endpoints are protected by a double-submit cookie
(`app/security/csrf.py`): login sets a non-httpOnly `csrf_token` cookie
alongside the httpOnly refresh-token cookie, and the frontend echoes it
back as an `X-CSRF-Token` header (`apps/web/src/lib/api.ts::readCsrfCookie`)
on every non-GET request. The check only runs when the CSRF cookie is
actually present — its absence means there's no cookie session to forge
in the first place, and that case is left to the endpoint's own "no
refresh token presented" handling for a clearer error.

The refresh cookie's own `SameSite=Lax` already blocks it being sent on a
cross-site POST in a compliant browser; the double-submit check is
defense-in-depth for browsers or proxies where that alone isn't a given.

## Security headers

`app/middleware/security_headers.py` applies to every response:

- `Content-Security-Policy` — `default-src 'self'`, a per-request nonce
  for `script-src` (no `'unsafe-inline'`), `frame-ancestors 'none'`.
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` — denies camera, microphone, geolocation, payment,
  USB, and FLoC-style interest-cohort tracking.
- `Strict-Transport-Security` — production only (local dev and the test
  suite run over plain HTTP, so the header would be a promise they can't
  keep).

## Impersonation

Admin impersonation issues a distinct JWT with `type: "impersonation"`
(`app/security/jwt.py::create_impersonation_token`), never `"access"`.
`ImpersonationGuardMiddleware` (`app/middleware/impersonation_guard.py`)
decodes the bearer token itself on every non-safe HTTP method and rejects
with `403` before any route handler runs — an impersonation session can
read anything the impersonated user could, but cannot mutate anything,
verified end-to-end in `tests/test_admin_router.py::test_impersonation_token_is_read_only`.
Every impersonation session start/end is written to `audit_log`, and the
frontend shows a persistent banner with a time limit for the duration
(`apps/web/src/components/layout/ImpersonationBanner.tsx`).

## Encryption at rest

`app/security/crypto.py` wraps Fernet (AES-128-CBC + HMAC) behind
`encrypt`/`decrypt` (strings) and `encrypt_bytes`/`decrypt_bytes` (binary).
The key comes from the `ENCRYPTION_KEY` environment variable and is never
committed. Encrypted at rest:

- LinkedIn OAuth access/refresh tokens
- Uploaded résumés and pasted profile text (`ProfileImportBlob.ciphertext`)
- Data export ZIPs (`DataExport.encrypted_zip`) — see `docs/privacy.md`

**Key rotation procedure:** Fernet keys support multi-key rotation via
`MultiFernet`, but LinkSavvy currently runs a single active key. To
rotate: generate a new key, deploy it as the *first* entry of a
`MultiFernet([new_key, old_key])`-wrapped cipher (a follow-up change to
`app/security/crypto.py`, not yet built — tracked for a future phase),
re-encrypt existing rows with the new key via a one-off maintenance job,
then remove the old key once no unrotated row remains. Until that
`MultiFernet` change lands, rotating the key requires a maintenance
window: stop writers, re-encrypt every affected table with the new key,
redeploy with the new `ENCRYPTION_KEY`.

## What never reaches logs

User-generated content (résumé text, pasted profile data, AI prompts and
completions, conversation messages) is never written to application logs
or forwarded to error reporting. AI invocation logging
(`app/ai/gateway.py`) records token counts, latency, cost, and a
correlation id — never the prompt or completion text. The privacy purge
job (`app/privacy/purge.py`) also caps how long AI invocation *payloads*
that are stored in the database (not logs) are retained
(`settings.ai_invocation_payload_retention_days`) — see `docs/privacy.md`.

## CI security scanning

Three scanners run on every push (`.github/workflows/ci.yml`):

- **bandit** (`uv run bandit -c pyproject.toml -r app`) — static analysis
  for Python security anti-patterns. Configured exceptions live in
  `apps/api/pyproject.toml`'s `[tool.bandit]` table: `B101` (assert used)
  is skipped codebase-wide because every use is an internal invariant the
  type checker can't express, never an input-validation or auth boundary
  (those raise `ApiError`); `B105`/`B106` (hardcoded password string) are
  skipped because every historical hit was a false positive on a constant
  merely named or shaped like a secret (a LinkedIn OAuth endpoint URL, a
  JWT `type` claim literal), holding no actual credential. Two
  call-specific `random.uniform` findings (retry-backoff jitter in
  `app/ai/gateway.py` and `app/jobs/worker.py`, not a cryptographic use)
  are suppressed inline with `# nosec B311` rather than a blanket skip.
  Any *new* bandit finding should default to being fixed, not suppressed;
  a suppression needs the same inline, reasoned comment as these two.
- **pip-audit** (`uv run pip-audit`) — fails the build on any known
  vulnerability in a resolved Python dependency. No blanket ignores are
  configured; if a future finding is a genuine false positive or an
  accepted risk, use `pip-audit --ignore-vuln <id>` with a comment in the
  CI step explaining why, not a silent skip.
- **npm audit** (`npm audit --omit=dev --audit-level=high`) — production
  dependencies only, failing on high/critical. Two categories of known,
  accepted findings exist today and are intentionally *not* blocking CI:
  - `react-router` (moderate, an open-redirect/SSR-hydration advisory) —
    the fix is a major-version bump (6.x → 7.x) across every route in the
    web app, which is a large, test-heavy migration out of scope for this
    security pass. Tracked as a follow-up; mitigated in the meantime by
    the CSP's `form-action 'self'` and the fact that the app never renders
    a redirect target from unauthenticated user input.
  - `vite`/`vitest`/`esbuild` (moderate/high/critical) — dev-only build
    and test tooling, not shipped to production, so `--omit=dev` already
    excludes them from the CI gate; running `npm audit` without `--omit=dev`
    locally will surface them for visibility.

  Re-run `npm audit --omit=dev` locally after any dependency bump to
  confirm no new findings before merging.
