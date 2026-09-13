# 6. Tool Framework architecture

Date: 2026-09-13

## Status

Accepted

## Context

Phase 05 needs a way to ship many AI-backed "hub tools" — the seven
Profile Hub tools this phase ships, and every Content/Engagement/
Career/Growth Hub tool a later phase will add — without each one
growing its own router endpoint, context-gathering code, and frontend
form. The explicit mandate was to treat the framework as the
deliverable and the seven tools as its proof: if a tool needed bespoke
UI code, the framework was wrong and needed fixing, not the tool.

## Decisions

**A tool is a `ToolDefinition`, not a router.** `app/tools/definition.py`
is a frozen dataclass — input/output Pydantic schemas, a `prompt_id`,
required/optional context keys, plan/quota/renderer/asset-type flags —
and nothing else. `app/tools/registry.py` auto-discovers every
`DEFINITION` under `app/tools/definitions/**/*.py` (mirroring
`app/ai/prompts/loader.py`'s eager-load-at-startup discipline) and
cross-validates each one's `output_schema.model_json_schema()` against
its prompt's declared JSON Schema file, byte for byte — a tool and its
prompt drifting apart is a startup failure, not a runtime surprise. One
real bug this caught early: the dynamic loader (`importlib.util
.spec_from_file_location`) never registered a loaded module in
`sys.modules`, which every one-flat-class tool definition happened not
to need but which Pydantic's forward-reference resolution for a nested
output model (`list[SomeSubModel]`, needed by five of the seven real
tools) requires to exist. The fix registers each definition module in
`sys.modules` before executing it — a framework fix, exactly the kind
the phase's mandate anticipated, surfaced by building real tools with
real output shapes rather than the single-flat-field fixtures Section 1
shipped with.

**Context is assembled from a closed, named vocabulary, not a free-form
dict.** `app/tools/context.py`'s `ContextKey` enum (`profile.identity`,
`profile.about`, ..., `target_role`, `user_supplied_text`) is the only
vocabulary a tool's `required_context`/`optional_context` can draw from;
each key has exactly one serializer and one priority. `assemble()`
never truncates mid-record when a token budget is tight — it drops the
lowest-priority *optional* key whole, and never drops a required one,
raising a typed `ContextUnavailable` naming exactly what's missing and
how to fix it instead. The one gap this closed vocabulary couldn't
cover — the Completeness Checker needing Phase 2's deterministic
`compute_completeness` result, which isn't profile data and has no
natural `ContextKey` — was closed with a narrow escape hatch instead of
stretching the enum: `ToolDefinition.precompute`, an optional async hook
whose returned `{template_var: labelled_block}` dict is merged into the
assembled context, exempt from budget trimming since it's small and
never optional. It stays a framework primitive, not a special case for
one tool — any future tool wrapping a deterministic engine uses the
same hook.

**Two independent quota layers, on purpose.** `app/ai/gateway.py`
already meters every provider call against a single global `ai_runs`
metric, regardless of which tool triggered it. `app/tools/service.py`
adds a second, tool-facing layer on top: `quota_metric` (pooled
`tool_runs`/`saved_assets` counters, reused unchanged from Phase 3's
seeded `PlanLimit` rows) for the standard per-plan cost, plus an
optional `free_daily_cap` — a stricter, per-tool ceiling enforced with a
direct `COUNT(*)` against `tool_runs` rather than through the generic
quota table, since seeding a `PlanLimit` row per tool for a feature only
some tools need would be schema and seed-data complexity most tools
never touch. A tool run therefore debits both layers; releasing one on
failure never touches the other, since they answer different questions
("can this plan afford it" vs. "how many gateway calls did this cost").

**Streaming reuses Phase 3's SSE contract and adds exactly one frame.**
`?stream=true` yields the same `meta`/`delta`/`error`/`done` frames
`internal.py`'s playground already established, then — only after a
successful `done` — a `tool_run` frame carrying the persisted run's id,
the context keys it used, and its quota snapshot: the same information
the non-streaming path returns in one `ToolRunResponse`, so the client
doesn't need two different result shapes depending on how it asked.

**The frontend is one component, driven entirely by the tool's own
JSON Schema.** `<ToolRunner>` (`apps/web/src/tools/ToolRunner.tsx`)
never branches on a tool id. Every widget it can render — string,
longtext, enum, multi-select, number, boolean, and a `profile_section`
picker over the user's own profile data — is a switch on a *field's own
schema shape* (`schema-form.ts`), driven by conventions any tool's input
model can opt into (`format: "textarea"`, `x-default-source`,
`x-profile-section-kind`), never a field or tool name. The six result
renderers (`renderers.tsx`) work the same way in reverse: dispatch is on
`result_renderer` alone, and each renderer owns a fixed output-shape
contract (documented at the top of that file) every tool choosing that
renderer must conform to — the "strict output schema" the phase asked
for is what keeps a tool's prompt output and its renderer's expectations
from silently drifting apart. `test.echo` (Section 7) is the framework's
own proof of this: it exists as a definition file and a prompt only, is
hidden from everyone except an admin with the `dev.playground` flag (any
`test.`-prefixed tool id, mirroring the existing developer-playground
gate), and renders, runs, and saves through code that was never touched
to add it.

**"Apply to profile" lives outside the framework, not inside it.**
Writing an accepted headline/About/experience result back into a new
`ProfileSnapshot` version is Profile-Hub-specific — no other hub has a
"profile" to write back into. `ToolRunner` only grew a generic
`onApplyToProfile` callback, fired with the tool's own `save_as` and the
accepted text; what "apply" means for a given asset type, the
before/after diff, and the "LinkSavvy never writes to LinkedIn itself"
reminder all live in `apps/web/src/pages/hubs/ApplyToProfileModal.tsx`,
which the Profile Hub page owns. A future hub with its own "apply back"
notion builds its own equivalent rather than teaching the framework
about a second domain object.

## Consequences

- Every tool prompt that wants a `ContextKey`'s value must reference it
  by its flattened `template_var` (`profile_identity`, not
  `profile.identity`) and guard any *optional* key with
  `{% if key is defined %}` — Jinja's `StrictUndefined` raises on a bare
  reference to a key `assemble()` didn't include, which is deliberate
  (a silently-blank block would be worse), but means every new tool's
  prompt needs to get this right by convention, not by a compiler check.
- The registry's `sys.modules` fix means two definition files loaded in
  the same process that happen to derive the same dotted module name
  (only possible today via two test fixtures using an identical relative
  filename under different `tmp_path`s) share a `sys.modules` slot
  serially — safe because registry construction resolves each module's
  schemas synchronously before the next file loads, but worth knowing if
  a future test parallelizes tool-registry construction.
- `free_daily_cap`'s direct-count enforcement doesn't share the generic
  quota table's atomic reserve/release semantics — it's a read-then-act
  check, acceptable for a soft per-tool ceiling but not a hard
  concurrency guarantee the way `check_and_reserve`'s single UPSERT is.
- `docs/adding-a-tool.md` is the maintained reference for the
  conventions this ADR only summarizes (widget conventions, renderer
  output contracts, the `precompute` hook) — update it, not just this
  ADR, when a new tool needs a convention this phase didn't anticipate.
