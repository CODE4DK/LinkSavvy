# 5. Audit Engine architecture and scoring

Date: 2026-09-16

## Status

Accepted

## Context

Phase 04 needs a way to turn a `ProfileSnapshot` into a Health Score,
category breakdowns, and concrete recommendations — reliably, cheaply,
and honestly about what it doesn't know. It has to run as a background
job (an audit can take longer than a request should block on), call the
AI gateway only where a rule genuinely can't judge something, and never
penalize a user for a gap that isn't their fault (a field the LinkedIn
API doesn't expose, a hub they haven't used yet).

## Decisions

**Deterministic-first, and one shared AI answer instead of five.** Every
category audit (`app/audit/categories/*.py`) does everything a plain rule
can do first, and calls the gateway only for judgements a rule can't make:
profile writing quality (headline/About/experience, folded into a single
`audit.profile_quality.v1` call rather than three), and concrete manual
engagement ideas (`audit.engagement_opportunities.v1`). Career's role
alignment, Visibility's keyword density and skill alignment, and
Content's opportunity seeding all reuse one more AI answer —
`audit.role_keywords.v1`, the target role's expected vocabulary and
must-have skills — computed from it with plain set overlap, not a second
model call apiece. Since up to four categories want that identical,
role-generic answer, the orchestrator resolves it exactly once, before
fanning out to categories, and threads it through `AuditContext` as
already-resolved data. Resolving it independently per category would
have meant four concurrent gateway calls racing for the same
not-yet-cached cache key on every first audit for a role — a 4x
`ai_runs` quota cost for one piece of information.

**Never guess; skip and say why.** A category that can't compute a
component returns `None` for it rather than a low score, and
`weighted_average` (`app/audit/scoring.py`) renormalizes over whatever
*is* available rather than treating a missing component as a zero — the
same function serves both a category's own component rollup and the
orchestrator's cross-category overall score. When nothing in a category
is computable, its `CategoryResult.status` is `"skipped"`, not a
fabricated low score, and it carries an `inputs_available` map plus an
`unlock` message so the dashboard can say specifically what would turn
the gap into a score. This is why `career`'s `resume_presence` component
always contributes nothing today — there's no resume upload path yet —
without capping Career's score or treating the missing upload as a
failure.

**Category concurrency needs one database session per category, not
one shared session.** The five categories run via `asyncio.gather` so a
slow one (an AI call) doesn't serialize behind the others, but
`AsyncSession` isn't safe to use from more than one coroutine
concurrently — two categories both calling the gateway (which itself
commits, for quota reservation and invocation logging) at the same time
on one shared session raised `IllegalStateChangeError` in exactly the
way this decision predicts. The fix widens `JobHandler`
(`app/jobs/registry.py`) to receive the same `session_factory` the
worker itself was given, alongside the single-use `db` session, so any
handler that needs to fan work out concurrently — not just this one —
can open one session per coroutine from it. `app/audit/orchestrator.py`
does exactly that: `AuditContext` is built once, then
`dataclasses.replace`d with a fresh `db` per category, while everything
else (snapshot, completeness, role_keywords) stays shared, immutable,
read-only data. The orchestrator's own session is reserved for
sequential work — resolving role_keywords before the fan-out, and
persisting the `Audit`/`AuditCategoryResult`/`AuditFinding`/
`ScoreHistory`/`Recommendation` rows after it.

**A category failure degrades the audit, it doesn't fail it.** Each
category run is wrapped in `asyncio.wait_for` with a
30-second timeout and a bare `except Exception`; a timeout or an
unexpected exception is recorded as `status="failed"` (score `None`,
weight dropped from the overall score) rather than aborting the whole
audit. The `Audit` itself is marked `completed_with_errors` rather than
`failed`, since four working categories and a Health Score are still
useful to show a user even when one category broke.

**Recommendations are a fixed table, not a fourth AI call.** Turning a
finding into an actionable card — a title, a route, an estimated impact
in points — is a lookup by finding `code` in
`app/audit/recommendations.py`'s `_ROUTES`, ranked by severity then
impact. Two categories independently noticing the identical fact (both
Engagement and Visibility flag a missing custom URL) would otherwise
surface as two near-identical recommendation cards from one audit; only
one code per distinct fact is mapped, so the duplicate stays a finding
on its own category's detail without becoming a repeated card. Purely
informational "we need more input" findings (`*.no_target_role` and
similar) are deliberately left unmapped for the same reason — several
categories raise their own version of it, and turning each into its own
card would just repeat the same advice.

## Consequences

- `JobHandler`'s signature changed (`(Job, AsyncSession)` →
  `(Job, AsyncSession, SessionFactory)`) to fix the concurrency bug
  above. This phase is the first to register a real handler, so the
  change only touched this phase's own test fixtures — but any future
  job type now receives a `session_factory` it's free to ignore.
- Career's score can never reach a fully "complete" status until a later
  phase's Career Hub adds resume upload — `resume_presence` stays
  permanently unavailable until then. This is documented in
  `docs/scoring.md` rather than treated as a bug to work around now.
- `target_role` has no persistent home yet — it's accepted as an
  optional per-run parameter (meant to flow through the job payload),
  falling back to the profile's current experience title via
  `resolve_target_role()`, with `target_role_is_assumed` recorded so a
  category's evidence is honest about which source it used. A durable
  "target role" preference is a reasonable candidate for a later phase,
  not invented here to avoid a new schema column this phase doesn't
  otherwise need.
- Each category audit opening its own database session means
  an audit run holds up to six connections briefly (one orchestrator
  session, one per category) instead of one — acceptable at today's
  scale, but worth revisiting if connection-pool pressure ever shows up
  under real concurrent audit load.
