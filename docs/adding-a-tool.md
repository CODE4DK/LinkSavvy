# Adding a tool

A hub tool (Profile Hub's seven, and every tool a later hub adds) is
data, not code. Adding one means adding a definition file and a prompt —
never touching the router, the context assembler, or `<ToolRunner>`. If
you find yourself needing to touch any of those three for a "normal"
tool, the framework is missing a convention; add the convention (see
`docs/adr/0006-tool-framework.md`) rather than special-casing your tool.

This doc is the practical checklist and reference; the ADR explains why
the framework is shaped this way.

## The five files a tool needs

Using `profile.headline_optimizer` as the worked example throughout:

1. **A definition file** —
   `apps/api/app/tools/definitions/<hub>/<name>.py`. Must define a
   module-level `DEFINITION: ToolDefinition` (see below).
2. **A prompt** —
   `apps/api/app/ai/prompts/<prompt_id>.prompt.md`, following the same
   YAML-frontmatter format every other prompt uses (see
   `app/ai/prompts/loader.py`).
3. **An output schema file** —
   `apps/api/app/ai/prompts/schemas/<prompt_id>.schema.json`. This
   **must** equal `definition.output_schema.model_json_schema()` byte
   for byte — the registry checks this at startup and refuses to boot
   if it doesn't match. Don't hand-write it: generate it from the model
   so it can't drift (see "Generating the schema file" below).
4. **A fake-provider fixture** —
   `apps/api/app/ai/providers/fake_fixtures/<prompt_id>.json`, so the
   whole test suite (which never makes a real network call) has
   something to return for your prompt. Shape: `{"response": <your
   schema's shape>, "tokens_out": <int>}`.
5. **A golden test** — asserting the tool runs end to end against the
   fake fixture, and that it never fabricates something not present in
   the test's `ProfileSnapshot` fixture (see
   `tests/tools/definitions/test_profile_tools.py` for the pattern).

## The definition file

```python
from pydantic import BaseModel, ConfigDict, Field
from app.tools.context import ContextKey
from app.tools.definition import AssetType, Hub, Plan, ResultRenderer, ToolDefinition


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rejects an unexpected field the model invents


class _Input(_StrictModel):
    target_role: str = Field(default="", title="Target role")


class _Variant(_StrictModel):
    text: str = Field(max_length=220)
    rationale: str


class _Output(_StrictModel):
    variants: list[_Variant] = Field(min_length=5, max_length=5)


DEFINITION = ToolDefinition(
    id="profile.headline_optimizer",       # also the URL path segment: /profile/{id}
    hub=Hub.PROFILE,
    name="Headline Optimizer",
    short_description="Five LinkedIn headline variants grounded in your real experience.",
    input_schema=_Input,
    output_schema=_Output,
    prompt_id="profile.headline_optimizer.v1",
    required_context=[ContextKey.PROFILE_IDENTITY, ContextKey.PROFILE_EXPERIENCES],
    optional_context=[ContextKey.TARGET_ROLE],
    result_renderer=ResultRenderer.VARIANTS,
    save_as=AssetType.HEADLINE,             # or None if this tool's result isn't saveable
    min_plan=Plan.FREE,                     # default; set Plan.PRO to gate a tool
    free_daily_cap=None,                    # a stricter per-tool daily cap beyond the pooled quota
    supports_streaming=False,               # true to stream token-by-token in ToolRunner
)
```

Always set `model_config = ConfigDict(extra="forbid")` on every model —
it's what makes the JSON Schema genuinely strict (`additionalProperties:
false`), so the gateway's schema validation actually rejects a response
that invents an extra field.

### `required_context` / `optional_context`

Pick from the closed `ContextKey` enum (`app/tools/context.py`):
`PROFILE_IDENTITY`, `PROFILE_HEADLINE`, `PROFILE_ABOUT`,
`PROFILE_EXPERIENCES`, `PROFILE_SKILLS`, `PROFILE_FULL`,
`AUDIT_LATEST_FINDINGS`, `TARGET_ROLE`, `VOICE_PROFILE`,
`RECENT_ASSETS`, `USER_SUPPLIED_TEXT`. A required key that has nothing
to serialize makes the whole run fail with a typed `ContextUnavailable`
naming what's missing and how to fix it — put a key in `optional_context`
if the tool should still work without it.

`TARGET_ROLE` and `USER_SUPPLIED_TEXT` are populated from the tool's own
input schema: name a field `target_role` or `user_supplied_text` and, if
non-blank, it flows into context automatically (see
`app/tools/service.py`'s `_EXTRA_CONTEXT_FIELDS`) — no other wiring
needed.

### Context your tool needs that isn't a `ContextKey`

If a tool needs context from a deterministic source that isn't profile
data (Phase 2's `compute_completeness`, say), don't stretch the
`ContextKey` enum — give the definition a `precompute` hook instead:

```python
async def _precompute(user: User, db: AsyncSession) -> dict[str, str]:
    result = compute_completeness(...)
    return {"completeness_score": f"## Completeness score\n{result.score}/100"}

DEFINITION = ToolDefinition(..., precompute=_precompute)
```

Its returned dict is merged into the assembled context after
`assemble()` runs (see `profile.completeness_checker`'s definition for
the full pattern, including raising `ContextUnavailable` itself when its
own precondition — an active snapshot — is missing).

## The prompt

Same format as every other prompt (`id`, `version`, `tier`,
`output_schema`, `max_output_tokens`, `temperature`, `cache_ttl_seconds`,
`description`, `required_context`). Two rules specific to tools:

- **`required_context` here is a list of flat template-variable names**,
  not `ContextKey` values — a `ContextKey` like `PROFILE_IDENTITY`
  becomes `profile_identity` (dots become underscores; see
  `ContextKey.template_var`). List here whatever your definition's own
  `required_context` maps to, plus any `precompute`-provided keys.
- **Guard every *optional* variable** with
  `{% if profile_skills is defined %}` — the sandboxed Jinja environment
  raises on a bare reference to a variable `assemble()` didn't include,
  and `is defined` is the one construct that doesn't trigger that raise.
  `regeneration_nudge` is the one exception: it's always present (an
  empty string when unused), so reference it directly with
  `{% if regeneration_nudge %}`.

Every tool prompt should also end with the same two constraints every
existing one carries: never fabricate a detail not present in the
context, and never suggest automating a LinkedIn action (liking,
commenting, connecting, messaging, posting) — those are for the person
to do themselves, per this codebase's hard compliance rule.

## Generating the schema file

Don't hand-write `schemas/<prompt_id>.schema.json`. From
`apps/api`, with your definition module written:

```bash
uv run python3 -c "
import json
from app.tools.definitions.profile import headline_optimizer as mod
schema = mod._Output.model_json_schema()
open('app/ai/prompts/schemas/profile.headline_optimizer.v1.schema.json', 'w').write(
    json.dumps(schema, indent=2) + '\n'
)
"
```

Then validate your fixture against it before running anything:

```bash
uv run python3 -c "
import json
from jsonschema.validators import Draft202012Validator
schema = json.load(open('app/ai/prompts/schemas/profile.headline_optimizer.v1.schema.json'))
fixture = json.load(open('app/ai/providers/fake_fixtures/profile.headline_optimizer.v1.json'))
Draft202012Validator(schema).validate(fixture['response'])
print('OK')
"
```

After adding or changing a prompt, regenerate the lockfile in the same
commit: `uv run python -m app.ai.prompts.lockfile --write`.

## The result renderer contract

`result_renderer` on the definition picks which of six generic frontend
views (`apps/web/src/tools/renderers.tsx`) shows the output. Your
prompt's output schema **must** conform to the shape the chosen renderer
expects — there's no per-tool frontend code to adapt a mismatched shape:

| Renderer | Expected output shape |
| --- | --- |
| `variants` | `{ variants: [{ ...any fields... }] }` — the longest string field in each variant is shown as its primary text; every other scalar field renders as a small label. |
| `document` | `{ sections: [{ heading?, body?, bullets?: [{ text, flagged?, flag_reason? }] }] }` — a flagged bullet (e.g. "needs a real metric") renders with a warning badge. |
| `analysis` | `{ summary?, score?, findings: [{ title, severity?: "info"\|"warning"\|"critical", description?, recommendation? }] }` |
| `table` | `{ columns: string[], rows: [{ ...one key per column... }] }` — tell the model in the prompt exactly what `columns` must be. |
| `calendar` | `{ days: [{ date, items: [{ title, time?, kind? }] }] }` |
| `thread` | `{ messages: [{ author?, role?, text, timestamp? }] }` |

## Input widgets

`apps/web/src/tools/schema-form.ts` maps a JSON Schema property to a
form widget purely from that field's own schema shape — no tool ever
needs bespoke form code:

| To get this widget | Shape your Pydantic field this way |
| --- | --- |
| Single-line text | Plain `str` |
| Multi-line text | `str` with `Field(json_schema_extra={"format": "textarea"})` |
| Single-select | `Literal[...]` or an enum |
| Multi-select | `list[str]` where the item type is an enum |
| Number | `int` / `float` |
| Checkbox | `bool` |
| Profile-section picker | `Field(json_schema_extra={"format": "profile_section", "x-profile-section-kind": "experience"})` — currently only `"experience"` has an option-list mapping in `schema-form.ts`; add a new kind there if you need another. |
| Pre-filled from the user's profile | Add `"x-default-source": "headline"` (or `"about"`, `"full_name"`) to a string field's `json_schema_extra` — the form fills it from the user's active `ProfileSnapshot` if one exists. |

A field named exactly `target_role` or `user_supplied_text` is both a
normal form field *and* the way that value reaches your prompt (see
above) — no extra wiring needed on either side.

## Gating a tool behind admin + a feature flag

If a tool is dev-only (not meant for real users yet), prefix its id with
`test.` — `app/tools/service.py`'s `_HIDDEN_TOOL_PREFIX` check hides any
such tool from `GET /api/v1/tools` and turns a direct run attempt into a
404 for everyone except an admin with the `dev.playground` flag on. See
`app/tools/definitions/dev/echo.py` for the reference example.

## Checklist

- [ ] Definition file with `model_config = ConfigDict(extra="forbid")`
      on every model
- [ ] Prompt file, `required_context` matching flat template-var names,
      every optional variable guarded with `is defined`
- [ ] Schema file generated from the model, not hand-written
- [ ] Fixture validated against the schema
- [ ] `prompts.lock.json` regenerated
- [ ] Golden test: runs successfully, output shape asserted, no
      fabricated detail beyond the test snapshot's real data
- [ ] `uv run ruff check . && uv run black --check . && uv run mypy app
      scripts tests alembic/env.py && uv run pytest -q` all green
- [ ] `python3 scripts/check_compliance.py` still passes
