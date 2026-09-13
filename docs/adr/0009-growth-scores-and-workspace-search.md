# 9. Growth scores and Workspace search

Date: 2026-09-13

## Status

Accepted

## Context

Phase 08 built two hubs. The Growth Hub (Part A) adds four scores
(Health, Visibility, Consistency, Personal Branding), a deterministic
weekly recommendation engine, an AI Growth Coach, a networking
recommendations tool, and the progress views that tie them together
with real history. The Workspace Hub (Part B) builds the interface on
top of the assets layer Phase 05 already created — search, folders,
trash, versions, bulk operations, and a UI — without redesigning that
schema. This ADR records the decisions specific to both, plus the
migration renumbering the spec's own numbering didn't anticipate.

## Decisions

**Migrations are 0012-0015, not 0010 as the spec assumed.** The spec
was written assuming `weekly_plans`/`growth_goals` would be migration
0010, but Phases 01-07 had already used 0001-0011 by the time this
phase started. The four migrations this phase needed follow
sequentially: 0012 (`growth_goals`, `weekly_plans`), 0013
(`coach_sessions`, `coach_messages`, plus `growth_goals.coach_state`),
0014 (`growth_score_snapshots`), 0015 (`asset_versions`). Nothing else
about the spec's schema was renumbered or reshaped — only the leading
digits moved.

**Each Growth score reuses an existing computation rather than
inventing a second one, and every component that has nothing to say
returns no evidence rather than a fabricated one.** Per the spec's
rule ("a score with no evidence for a component is a bug"), every
`ScoreComponent` a score actually reports carries real evidence; a
component with nothing to measure is simply omitted from the list, not
included with an empty or default evidence blob:
- **Health** reshapes the audit engine's existing `ScoreHistory` rows
  (Phase 04) into the shared `GrowthScore` envelope — no new scoring
  logic, since the audit's overall score already is the Health Score.
- **Visibility** is deterministic except for keyword relevance, which
  reuses `app.audit.role_keywords.get_role_keywords` — the same
  gateway call Phase 04's audit already makes and the gateway already
  caches on `(prompt, target_role)`, so scoring Visibility repeatedly
  costs no additional AI calls beyond the first for a given target
  role. Its `photo_and_banner` component is disclosed as photo-only:
  `ProfileSnapshot` has never captured a banner image at any phase, so
  the component honestly scores on `profile_picture_url` alone and
  reports `banner_checked: false` in its evidence rather than silently
  scoring as though a missing banner were checked and found absent.
  Closing this gap means extending `ProfileSnapshot` to capture a
  banner reference first — out of scope here.
- **Consistency** reuses `app.content.calendar_service.consistency_strip`
  (Phase 06) unchanged — the Content Hub's own posting-cadence
  computation is exactly what a Consistency score needs, so this phase
  adds no new posting-cadence logic of its own.
- **Personal Branding** is the one genuinely new score, and the only
  one requiring an AI judgement per se (voice/tone consistency across
  a snapshot's own text). Its evidence-discard rule mirrors the rest
  of the codebase's "never fabricate": a sub-score whose supporting
  text quote comes back blank from the gateway is dropped from
  `components` entirely rather than kept with empty evidence; if every
  component is dropped this way the whole score reports `status:
  skipped` rather than a hollow `0`.

**The weekly recommendation engine is deterministic, not AI-driven.**
`app/growth/weekly_plan.py` never calls the gateway. It draws its 3-5
items from `app.audit.recommendations`'s existing fixed, ranked
`Recommendation` table (Phase 04) and applies a category-based minutes
estimate (`_ESTIMATED_MINUTES_BY_CATEGORY`) to guarantee at least one
item is realistically under 10 minutes, swapping one in if the top-N
picks don't naturally include one. This keeps the weekly plan
reproducible and free — the same underlying recommendations a user
would see in the Dashboard, resequenced into a weekly cadence, rather
than a second AI-generated opinion that could disagree with the first.
Retrospectives (`_reflect_on_previous_week`) are similarly
deterministic: a previous week's items are classified as
moved/did-not-move/carried-forward by checking real score and audit
state, not by asking the model to grade itself.

**Weekly plan generation is a standalone polling scheduler, not a
`Job` row.** `app/growth/weekly_plan_scheduler.py` runs as its own
process rather than adding a "run for every user on a schedule"
concept to the `jobs` table. `Job.user_id` is `NOT NULL` and every
other job type in the system is triggered by a specific user action;
inventing a scheduled, user-less job kind would touch a table every
other job type depends on, for a need only this one feature has.
Deduplication is on the `Job` row itself — `_already_enqueued_this_week`
checks a `week_start` value embedded in the job's JSON payload in
Python (portable across MySQL and SQLite, rather than a SQL JSON path
that would need dialect branching) — not on `WeeklyPlan` existence,
since the plan doesn't exist until the job actually runs; matching on
the job avoids a race where a busy worker lets the scheduler enqueue
the same week twice before the first job finishes.

**The AI Growth Coach is built directly on the gateway, deliberately
outside the Phase 09 assistant it will later become a mode of.**
`app/growth/coach.py` is a small, self-contained conversational loop
(`coach_sessions`/`coach_messages`, a 5-question interview cap enforced
by the prompt) rather than a preview of Phase 09's not-yet-built
architecture — building it against a system that doesn't exist yet
would violate CLAUDE.md's "never introduce a dependency on a module a
later phase is supposed to build."

**The Coach's honesty mechanism is a real per-score before/after
comparison, not a summary the model could embellish.** Every turn,
`_progress_since_last_visit` computes real elapsed days, calls
`app.growth.history.get_before_after` for an actual before/after value
per score type, counts real `ToolRun` activity, and counts real
weekly-plan completions — all rendered into the prompt context before
the gateway ever runs, so the model has no room to manufacture
encouragement the data doesn't support. This function was originally
written in A3, before `growth_score_snapshots` existed, when only the
audit engine's `ScoreHistory` gave any score real history — at that
point it could honestly report only the Health Score's movement, with
a disclosed caveat that the other three showed only their current
value. Once A5 built `growth_score_snapshots` with real daily history
for all four scores, that caveat became stale; this phase's close-out
found and fixed it, rewiring `_progress_since_last_visit` onto
`get_before_after` so every score's real movement is reported, not
just Health's. The Coach still never fabricates a benchmark, growth
tactic, or automation suggestion — `growth.coach.v1.prompt.md`'s
constraints on that are unchanged from A3.

**`growth.networking_recommendations` is a tool that refuses to do the
one thing "networking" usually implies.** It produces advice (who to
look for, what to say, how to follow up) grounded in the user's own
profile and goal — never a lead list, never scraped contacts, never a
bulk outreach draft. This is the same "assistant, not automation tool"
line CLAUDE.md draws for LinkedIn itself, applied to a tool that could
otherwise be tempted to imply LinkedIn contact scraping without ever
touching linkedin.com directly.

**`growth_score_snapshots` is append-only and compares scalars only,
not per-component breakdowns.** `record_snapshots` writes at most one
row per `(user, score_type, day)` and skips any score whose `value is
None` — recording a snapshot for a skipped score would fabricate a
data point that was never actually computed. This powers both the
6-month trend chart (`get_score_history`) and the before/after panel
(`get_before_after`, using the nearest snapshot on or before each
boundary date, since a snapshot only exists for a day the hub was
actually visited). The before/after panel compares each score's single
`value`, not its component-level detail — a Health Score improvement
is visible, but which specific component moved it is not reconstructable
from history alone. Component-level history is a real gap, deliberately
left for a future phase rather than doubling the snapshot table's width
speculatively now.

**Workspace's schema addition is exactly one new table:
`asset_versions`.** Per the spec's explicit constraint ("the assets
table already exists from Phase 5 — this phase builds its interface,"
verified again during this close-out), every other Workspace feature —
folders, search, trash, bulk operations, favourites — is built against
columns Phase 05 already defined. Version history needed a genuinely
new table since Phase 05 never captured prior states of an asset's
`title`/`body`; nothing else did.

**Search branches on database dialect: real MySQL FULLTEXT in
production, `ILIKE` in SQLite-backed tests.** `app/workspace/search.py`
checks `db.get_bind().dialect.name` (mirroring the same pattern
`app/billing/quota.py` already used) — MySQL gets
`MATCH(assets.title, assets.body) AGAINST (:q IN BOOLEAN MODE)` with
relevance-ordered results; SQLite, which is what the entire test suite
runs against, falls back to `ILIKE` ordered by recency.
`boolean_mode_query()` (converting free text into `+word*` boolean-mode
syntax) is a pure function, unit-tested independently of which dialect
executes it. This is a disclosed limitation: SQLite's fallback path is
never actually exercised against a real FULLTEXT index, so a
MySQL-specific FULLTEXT edge case (stopword handling, minimum word
length) could in principle behave differently in production than in
CI. B4's 5,000-asset performance test runs on SQLite for the same
reason every other test does, and still passes the 500ms search budget
on the `ILIKE` path — the MySQL FULLTEXT path should be faster, not
slower, so this is not judged to understate the real budget.

**Cursor pagination is keyed on `id` (UUIDv7), not `created_at`.** An
earlier version keyed cursors on `created_at`, which broke silently
under SQLite: `server_default=func.now()` produces a timestamp string
with no fractional seconds, while SQLAlchemy's `DateTime` type always
serializes a *bound* Python `datetime` parameter with fractional
seconds — two different TEXT strings in SQLite's storage, so
`created_at = :cursor_value` never matched and `<` always evaluated
true, producing overlapping pages. Rather than patching this with a
composite `(created_at, id)` tie-breaker, cursors were rewritten to
order and paginate strictly by `id` — a UUIDv7 is already unique and
already monotonically time-ordered, so it needs no tie-breaker at all
and sidesteps the equality-comparison bug entirely. This is a cleaner
fix than papering over the timestamp-precision mismatch, and it is
correct on MySQL as well as SQLite, not merely test-passing.

**Folder deletion unfiles assets and reparents subfolders in
application code, not by relying on `ondelete=SET NULL`.** The FK
constraints are still declared in the SQLAlchemy models (correct and
effective under real MySQL), but SQLite — the entire test suite's
database — does not enforce FK actions at all unless a session
explicitly sets `PRAGMA foreign_keys=ON`, which this codebase's test
conftest does not do. Relying on the database to do this would mean
the behavior is only ever verified in production, never in CI.
`app/workspace/folders.py`'s `delete_folder()` explicitly nulls
`Asset.folder_id` and reparents `AssetFolder.parent_id` to the root
before deleting, making the behavior identical and testable on both
databases.

**The 30-day trash purge is implemented but not yet scheduled.**
`app/workspace/assets.py`'s `purge_expired_trash()` is a real,
independently-tested function (hard-deletes anything past its 30-day
window), but nothing calls it on a schedule yet — there is no
Workspace-trash equivalent of the weekly-plan scheduler process. This
is a disclosed gap, not an oversight: wiring it to a scheduled job (or
folding it into the existing weekly-plan scheduler process) is
deferred to whichever future phase next touches the jobs system,
rather than adding a second standalone scheduler process for one
lightweight cleanup task.

**B4 index review: `ix_assets_user_folder(user_id, folder_id)` is left
as-is; no further Workspace indexes were added.** The existing
composite index (Phase 05) has `user_id` as its leftmost column, so it
already serves every current query shape: `user_id` alone (unfiltered
listing), `user_id + folder_id` (a folder view), and, combined with
`Asset.id`'s own primary-key ordering, the `id`-based cursor
pagination this phase introduced. The 5,000-asset performance test
(`tests/workspace/test_performance.py`) exercises both the unfiltered
listing and the search path and stays comfortably under the 500ms
budget without any additional index. A dedicated index for the search
path specifically is what MySQL's `FULLTEXT` index (declared
alongside the table, not added by this phase's migrations since the
`assets` table and its FULLTEXT index already existed from Phase 05)
already provides. No new index was added speculatively — at current
per-user asset counts, `ix_assets_user_folder` and the existing
FULLTEXT index cover every query this phase's UI issues; revisiting
this is only warranted if a future phase's access pattern (e.g.
cross-user or tag-only queries at much larger scale) shows up as slow
in practice.

## Consequences

- Every Growth score can be traced back to a computation that already
  existed somewhere else in the codebase except Personal Branding,
  which is the one genuinely new AI-graded score this phase adds.
- The Growth Coach's honesty guarantee now covers all four scores
  uniformly; the fix landed during this phase's own close-out, once
  A5's snapshot history made the earlier Health-only comparison
  visibly stale rather than merely incomplete.
- Component-level before/after detail and banner-based Visibility
  scoring are both real, disclosed gaps for a future phase, not silent
  simplifications.
- Workspace's schema footprint stayed to one new table
  (`asset_versions`); everything else is genuinely just new endpoints
  and query logic over Phase 05's existing columns.
- The UUIDv7-cursor fix and the explicit-unfiling fix are both cases
  where a SQLite-only test-suite gap (timestamp precision, FK
  enforcement) surfaced a latent bug that would otherwise only have
  been caught in production against real MySQL.
- Search behaves correctly and quickly in both the MySQL production
  path and the SQLite test path, but the two paths are not identical
  in their edge-case behavior (stopwords, minimum word length); this
  is disclosed rather than assumed away.
- Trash purging exists and is tested, but nothing currently invokes it
  on a schedule — 30-day expiry is enforced only from whenever a
  future phase wires up the call, not from today.
