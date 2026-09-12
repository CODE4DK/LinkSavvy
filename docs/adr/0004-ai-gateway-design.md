# 4. AI Gateway design

Date: 2026-09-14

## Status

Accepted

## Context

Phase 03 needs to give every later phase one way to call an LLM, so that
adding a hub feature means writing a prompt template and a tool
definition — never touching a vendor SDK, a cache table, or a quota
counter directly. It also needs to make LinkSavvy's AI usage governable
from day one: metered, rate-limited by plan, observable, and safe against
prompt injection and the specific failure mode CLAUDE.md's hard
compliance rule calls out — a model that tells a user to automate
LinkedIn, impersonate someone, or fabricate credentials or metrics.

## Decisions

**One Protocol, three implementations, one registry.** `LLMProvider`
(`complete`/`stream`) is implemented by `OpenAIProvider` and
`GeminiProvider` — thin `httpx` clients against each vendor's documented
REST API, no SDK dependency, consistent with how `app/services/
linkedin.py` already talks to LinkedIn — and by `FakeProvider`, a
fixture-driven deterministic double. `config/models.yaml` is the only
place a vendor model string may appear: `app.ai.providers.registry`
resolves `(tier, plan)` to a bound provider instance, so free users get
the cheaper model at a tier and pro users the stronger one, and neither a
prompt nor the gateway ever names a model. `tests/conftest.py`'s autouse
`_fake_ai_providers` fixture swaps both real provider classes for
`FakeProvider` at the registry level, for the whole suite — not just
AI-specific tests — which is what makes "zero network calls" a property
of the test suite rather than a convention every test has to remember.

**A prompt is a file, and its meaning is pinned by a version + lockfile,
not by convention.** `.prompt.md` files (YAML frontmatter + a Jinja2
body) are validated in full at registry-construction time — id/filename
match, tier is a real `ModelTier`, `output_schema` is either `"text"` or
a file that's actually valid JSON Schema, token/temperature bounds, a
non-empty body — so a malformed prompt fails application startup, not
the first request that hits it. `prompts.lock.json` records each
prompt's `(version, body_sha256)`; a test recomputes the hash and fails
if a body changed without the version bumping. This is deliberately
mechanical rather than a review-process rule: a prompt's behavior is
part of the system's contract (cached responses and pinned integrations
depend on a version meaning one specific thing forever), and a hash
check catches what a diff review might not.

**Rendering can't reach into anything.** `render_prompt` uses a
`SandboxedEnvironment` subclass that raises on *any* attribute or item
access — `{{ value.attr }}` and `{{ value['key'] }}` both fail — so a
template can only substitute flat, already-sanitized strings. Combined
with `app/ai/safety/sanitize.py` wrapping every context value in named
delimiters before it reaches the template, there's no attribute chain
for a `{{ ''.__class__… }}`-style trick to walk even before considering
whether the input itself looks like an injection attempt.

**Reserve quota before doing the expensive work, in one atomic
statement.** `app/billing/quota.py`'s `check_and_reserve` combines the
usage increment and the limit check into a single `INSERT ... ON
DUPLICATE KEY UPDATE` (MySQL, using `IF()` to cap the write) or `INSERT
... ON CONFLICT DO UPDATE ... WHERE` (SQLite), so two requests racing for
the last unit of quota can't both read "available" and both proceed —
there is no read-then-write gap for a race to land in. A denial is a
typed `QuotaExceeded` (already an `ApiError`, HTTP 402
`QUOTA_EXCEEDED`) carrying `{metric, used, limit, window, resets_at,
upgrade_required}`, matching what Phase 10's paywall needs without this
phase having to guess at that UI. Work that was reserved but didn't pan
out — provider exhaustion, a failed schema repair, a policy block —
calls `release()` to give the reservation back, and even a quota denial
itself is recorded as an `ai_invocations` row (`outcome=quota_denied`)
so "how often do users hit their limit" is answerable from day one.

**Retry, circuit-break, then fall back — and only then give up.** Each
provider call gets up to 3 attempts with jittered exponential backoff on
a retryable `ProviderError` or a timeout; a per-process `CircuitBreaker`
(in-memory, not durable — a hint about this worker's recent experience,
not shared state worth a database write per call) opens after repeated
failures and skips straight to the secondary provider without wasting a
retry budget on a provider that's already down. Only if the secondary
also fails does the gateway raise `AIProviderUnavailable`. A successful
fallback is recorded (`fallback_used=True`) with whichever provider and
model actually served the request, not the one originally resolved.

**Schema repair is one attempt, not a loop.** If a schema-declaring
prompt's output fails `jsonschema` validation, the gateway makes exactly
one repair call (the original conversation plus the invalid output and
"return only valid JSON") and validates again. A second failure raises
`AIOutputInvalid` rather than retrying indefinitely — an LLM that can't
produce valid JSON after being told exactly what was wrong isn't going
to on a third try, and an unbounded repair loop is an unbounded cost.

**Streaming trades mid-flight validation for real-time output.**
`stream=True` runs the identical pipeline but defers schema and policy
validation to the end of the stream, since repairing would mean
discarding tokens already shown to the client. An invalid or
policy-blocked ending is still recorded with the right outcome and
surfaces as an `error` frame — the tradeoff is that the client has
already seen the (unvalidated) text by then. Client cancellation (closing
the SSE connection) closes the gateway's async generator via
`contextlib.aclosing`, which cascades into the provider's own streaming
generator and is what actually aborts the upstream HTTP request, not
just the local iteration.

**Output policy is deterministic pattern matching, not a second model
call.** `app/ai/safety/output_policy.py` checks generated text against
three fixed categories — automation instructions, impersonation,
fabricated credentials/experience/metrics — the same three things
CLAUDE.md's hard compliance rule names. Pattern matching over a second
LLM call because it's free, fast, auditable, and can't itself be
prompt-injected into approving something it shouldn't.

**Observability never has a text field to leak.** Every invocation's
structured log line and its `ai_invocations` row carry only fixed,
structural fields (correlation id, prompt id/version, tier, provider,
model, token counts, cost, latency, cache/fallback flags, outcome) —
there's no field in that shape a prompt body or user's content could
occupy. The one gap — a vendor's HTTP error body occasionally echoing
back a fragment of the request that triggered it — is closed by
`app/ai/redact.py`, applied to any exception message before it's
logged. `/internal/metrics` computes p50/p95 latency, cache hit rate,
fallback rate, invalid-output rate, and cost-per-user-per-day directly
from `ai_invocations` at request time rather than maintaining in-process
counters, keeping it correct across restarts and multiple workers
without a new metrics store (CLAUDE.md rules out Redis and a separate
time-series database).

## Consequences

- Six of this phase's eight numbered sections were built out of the
  spec's own order (metering schema and quota before the gateway that
  depends on both) because the gateway's `run()` genuinely can't check
  quota or record an invocation against tables that don't exist yet.
  The commit history reflects the dependency order, not the section
  numbering; each commit still maps to one section.
- The circuit breaker is per-process and in-memory, so a multi-worker
  deployment has one breaker per worker rather than one shared view of a
  provider's health. Accepted for now — a shared breaker would need
  either a database write per call (too expensive) or a new piece of
  shared-state infrastructure this phase has no other reason to add.
- Cost accounting (`config/models.yaml`'s `costs_per_million_tokens_minor`)
  uses illustrative rates, not vendor-verified pricing — the schema and
  the arithmetic are real, but the numbers will need reconciling against
  actual invoices before cost-per-user dashboards are trusted for
  billing decisions.
- The developer playground runs every request through the real pipeline
  (real quota, real metering, no bypass), which means exercising it
  costs the admin's own `ai_runs` quota. This is deliberate — it's
  supposed to be the same path a hub feature will use, not a privileged
  shortcut — but it does mean a busy admin session could hit its own
  daily limit.
