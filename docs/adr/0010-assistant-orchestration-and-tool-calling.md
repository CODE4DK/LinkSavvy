# 10. Assistant orchestration and tool calling

Date: 2026-11-22

## Status

Accepted

## Context

Phase 09 builds the AI Assistant: a conversational surface that must use
the roughly thirty tool definitions the Phase 5 registry already has
rather than reimplementing their behaviour in a prompt, propose tool
runs without ever executing one unconfirmed, absorb the Phase 8 Growth
Coach into one shared conversation store, and enforce a policy that
refuses automation/scraping/manipulation requests with a compliant
alternative attached every time. This ADR records the orchestration
design, the migration renumbering, the honesty and safety mechanisms,
and the scope decisions this phase narrowed deliberately.

## Decisions

**Migration is 0016, not the spec's assumed 0011.** 0001-0015 were
already in use by the time this phase started (the same renumbering-
in-place disclosure every phase since Phase 08 has made). `conversations`
and `messages` are the one shared store; this migration also drops
`coach_sessions`/`coach_messages`, since the Growth Coach absorption
below repoints that module at the same two tables instead of its own.

**Editing a message branches; nothing is ever destroyed.**
`messages.parent_message_id` is a self-referential pointer. Editing a
user message creates a new sibling under the *original's own parent*
(never a child of the message being edited), and retrying an assistant
reply does the same at the assistant's turn. `get_thread()` walks
parent pointers from a leaf back to the root to produce one linear
conversation; with no `leaf_message_id` given it defaults to the most
recently created leaf (a message nothing else lists as its parent), so
the newest branch is what renders by default and an older one is only
ever shown by explicitly asking for it. Both `list_messages()`'s
ordering and `get_thread()`'s leaf selection sort by `id` (a UUIDv7),
not `created_at` -- SQLite's `CURRENT_TIMESTAMP` server default only
has second precision, so two messages appended within the same second
tie under `created_at` and can come back in either order. This is the
same class of bug ADR 0009 already fixed once for asset cursor
pagination, caught here by a dedicated branching test before it ever
shipped.

**The orchestrator classifies intent once, cheaply, before doing
anything else.** `app/assistant/orchestrator.py`'s `_classify_intent`
is a single fast-tier gateway call (`assistant.intent_classifier.v1`)
returning `{intent, tool_candidates, confidence, needs_context,
policy_category}`. A `mode="tool"` conversation (created with a pinned
`tool_id`) skips classification entirely and treats every message as
`run_tool` against that one tool -- there is no ambiguity to resolve
when the user already picked a tool from a hub page's "Ask AI" entry
point.

**Three of the seven intents never reach a second gateway call.**
`policy_violation`, `out_of_scope`, and `coach` all resolve to a fixed,
canned reply -- policy refusals and the out-of-scope redirect for the
reasons in the policy section below (a guaranteed compliant-path
message beats hoping a second model call phrases it correctly every
time), and `coach` because a general conversation that drifts toward
"I want ongoing coaching" should point the user at the real Growth
Coach (which has its own real score history pre-loaded) rather than
attempt a shallow imitation of coaching inline. Only `smalltalk`,
`explain`, `run_tool`, and `analyse_my_data` call `assistant.reply.v1`,
on `fast`/`standard`/`standard`/`advanced` tiers respectively --
`advanced` is this codebase's three-tier system's answer to the spec's
"deep" tier for coaching and analysis; the Growth Coach itself already
runs on `standard` per its own Phase 8 design, unchanged here.

**Context assembly reuses `app.tools.context.assemble()` outright, with
a bigger budget and three new keys.** `AUDIT_SUMMARY` (a one-line score
summary, deliberately not the full findings list `AUDIT_LATEST_FINDINGS`
gives a tool prompt -- the assistant's ambient context should stay
light), `GROWTH_GOAL`, and `RECENT_ASSET_TITLES` (titles only, ten
rather than a tool's five, still never a body) were added to the
existing `ContextKey` enum rather than inventing a parallel context
system for the assistant; `goal_summary()` was promoted out of
`app.growth.coach` into `app.growth.goals` so both the assistant's
context assembler and the absorbed coach describe "the user's active
goal" identically instead of two summaries that could drift apart.
Every one of these keys is optional, never required -- a fresh user
with no audit, goal, or saved assets yet still gets a working
conversation, exactly as `assemble()` already handles for tools.

**The "what I can see" toggle lives on the conversation, not the
user.** `Conversation.context_snapshot` stores `excluded_context_keys`;
`assemble_context_for_conversation()` filters `ALL_CONTEXT_KEYS` by it
before calling the shared assembler. A toggle set in one conversation
doesn't leak into another -- reasonable, since what's relevant to
disclose can differ turn by turn and thread by thread, and a global
per-user setting would either surprise a new conversation by silently
hiding context or force the user to re-decide everything, every time,
before they've said anything.

**Assistant-side read functions are deterministic Python calls, not a
live function-calling loop against the model.** `app/assistant/reads.py`
(`get_my_profile_summary`, `get_latest_audit`, `get_my_scores`,
`search_my_workspace`, `list_available_tools`) are called procedurally
by the orchestrator based on intent and the classifier's own
`needs_context` hint (currently just `"workspace"`, triggering
`search_my_workspace`) -- never invoked by the model itself mid-generation.
This matches the rest of the codebase's deterministic-first,
AI-only-where-it-adds-value shape (ADR 0009's weekly recommendation
engine is the same pattern) and sidesteps building a real tool-calling
loop the fake-provider test infrastructure this environment always
runs against doesn't support anyway.

**A read call is recorded as a `role="tool"` Message, not an
`AIInvocation`.** The spec says "every read call is recorded in
`ai_invocations`," but `AIInvocation` is specifically the gateway's own
metering ledger -- one row per real LLM call, with mandatory
`prompt_id`/`tokens`/`cost_minor`/`provider` fields a plain DB read has
none of. Recording a zero-cost, no-prompt read there would corrupt what
that table means for cost dashboards and invalid-output-rate queries.
`messages.role` already has a `'tool'` value for exactly this kind of
turn, so a `search_my_workspace` call appends a `role="tool"` message
into the transcript instead -- visible in context, auditable, and where
a UI would actually want to render it, without polluting the metering
table. A confirmed tool run *is* recorded in both `tool_runs` and
`ai_invocations`, exactly as the spec asks, because
`confirm_and_run_tool` calls the same `app.tools.service.run_tool()`
every hub page calls -- nothing new there.

**A tool is proposed, never run, until the user confirms.**
`assistant.reply.v1`'s `proposed_tool` (tool id, reasoning, best-effort
`prefilled_input`) is re-validated against the classifier's own
`tool_candidates` before being shown -- a model proposing an id outside
that vetted list is silently dropped rather than trusted. Confirmation
goes through `POST /conversations/{id}/confirm-tool`, which calls
`app.tools.service.run_tool()` directly; the frontend's
`ToolProposalCard` reuses `ToolRunnerForm` for the editable inputs and
`ResultView`/`extractSaveableText` for the result, exactly the
components the hub pages themselves use -- no proposal-specific form or
result-rendering logic exists anywhere.

**Streaming mirrors `app.tools.service`'s own two-function shape rather
than trying to force one code path to do both.** `handle_message`
(non-streaming) and `stream_message` (SSE) share `_build_reply_context`
and `_finalize_reply` for the parts that don't differ, but each calls
the gateway differently -- intent classification stays non-streaming in
both (cheap, and its result decides which prompt/tier runs next before
any bytes go out), and only the reply-generation call actually streams
deltas for `smalltalk`/`explain`/`run_tool`/`analyse_my_data`; the
three canned-response intents and `coach` mode send their fixed or
already-generated text as a single `message` frame rather than a fake
per-character stream. This is the same amount of duplication
`_run_and_persist`/`_stream_and_persist` already accept in
`app.tools.service` -- an established, not a new, pattern.

**Policy is deterministic and pattern-based, checked before the
gateway is ever called.** `app/assistant/policy.py` mirrors
`app.ai.safety.output_policy`'s shape exactly (regex-based, free,
auditable) across six categories -- automation, scraping, engagement
manipulation, impersonation, fabrication, bulk undisclosed messaging --
each bundled with a fixed, ready-to-show compliant alternative. This
runs first, before intent classification, so an obviously dangerous
request never even reaches the gateway; the classifier's own semantic
judgement (`policy_category` on a `policy_violation` intent) is the
second line of defense for phrasing the regexes miss. Two real regex
gaps ("automatically messages" as a verb inflection the automation
pattern didn't match, and "crawl my connections' contact emails" where
the scraping pattern required its noun immediately after the verb) were
caught by the 22-prompt adversarial test suite before this ever shipped
-- including hypothetical framings ("purely as a thought experiment...")
and prompt-injection wrappers around a dangerous request, which the
regexes catch regardless of the wrapper since they match the request
itself, not the framing around it. A lighter, non-blocking output-side
check (`check_output`) catches the model claiming to have taken a
LinkedIn action itself, or stating a metric as fact without a hedge
word nearby -- the orchestrator replaces the reply text outright on an
action-claim violation rather than trying to surgically edit a
sentence out of a generated string.

**The Growth Coach is absorbed by repointing its storage, not by
rewriting its behaviour.** `app.growth.coach` still owns its own
prompt (`growth.coach.v1`), its own honesty mechanism against real
score history (Phase 8, ADR 0009), and its own 5-question interview
cap -- only `get_or_create_session`/`send_message` changed, to operate
on `Conversation(mode="coach")`/`Message` instead of the now-dropped
`coach_sessions`/`coach_messages`. `/hubs/growth/coach` keeps its own
route and its own frontend page, which renders the shared `ChatView`
component in `mode="coach"` pointed at a conversation id it manages
locally (deliberately not `AssistantContext`'s shared state -- the
coach thread is a distinct conversation from the general Assistant's,
and letting the page overwrite the shared "active conversation" would
mean opening the Growth Coach silently hijacks whatever the dockable
side panel had open). `growth.coach.py`'s own conversation-history
formatting was unified with the general assistant's via
`app.assistant.summarize.conversation_history_text(messages,
assistant_label="Coach")` -- one truncation/digest implementation,
parametrized only for which label a surface uses in its own transcript.

**Conversation history caps growth with a deterministic digest, not a
second AI summarization call.** `app/assistant/summarize.py` keeps the
most recent 20 turns verbatim and collapses anything older into one
line naming the count and the earliest few user messages' topics. An
AI-generated rolling summary was considered and rejected: it would cost
a real gateway call on every single turn once a conversation runs long,
precisely the cost growth this function exists to bound.

**Per-message "save to Workspace" narrowed to conversation-level
save.** The spec lists "save to Workspace" as a message action, but
Workspace's `Asset` model has a shape for a tool run
(`source_tool_run_id`) and a shape for a whole conversation transcript
(`type="conversation"`, already defined in Phase 05), not for an
arbitrary single chat message distinct from either. A tool-run message
already gets its own Save button via `ToolProposalCard` (the same one
a hub page's result gets); a plain text reply's "save" surfaced instead
as one header-level "Save conversation" button in `ChatView`, writing
the active thread's transcript as a `conversation` asset. This is a
disclosed scope narrowing given the real data-model constraint, not an
oversight.

**`assistant_messages` quota is enforced once per user-sent message,
in `_with_assistant_quota`, wrapping every entrypoint
(`handle_message`, `retry_message`, `edit_and_branch`,
`stream_message`) identically** -- including the Growth Coach's own
convenience alias endpoint (`POST /growth/coach/messages`), which
routes through `orchestrator.handle_message` specifically so it isn't a
quota-free backdoor into the same underlying gateway usage. This is
independent of the gateway's own `ai_runs` quota, which still meters
every individual `gateway.run()` call (classification and reply alike)
exactly as it always has.

**Per-conversation cost is a query, not a new stored aggregate.**
`Message.ai_invocation_id` already links an assistant reply to the
`AIInvocation` row that metered it (`cost_minor`, `tokens_in/out`,
`model`). A future Phase 10 admin dashboard can sum cost per
conversation via that join; this phase doesn't pre-build that query or
add a denormalized running total to `Conversation`; doing so before
Phase 10's actual dashboard needs are known would be exactly the
premature optimization CLAUDE.md warns against.

## Consequences

- Editing, retrying, and branching all share one `get_thread()`
  resolution mechanism and one `id`-based ordering fix; a UI showing
  "this reply has a sibling" only ever needs the flat message list, not
  a second endpoint.
- Every dangerous-intent adversarial prompt in the 22-case test suite
  is refused deterministically, with zero dependency on what a real or
  fake model happens to say that turn -- the same reliability the
  gateway's own `check_output_policy` already has for tool prompts.
- A read call's audit trail lives in the conversation transcript
  (`role="tool"` messages), not in the AI cost-metering table; a future
  phase wanting to report "how many workspace searches happened this
  month" queries messages, not invocations.
- Streaming genuinely streams only for the four intents that call the
  gateway at all; the three canned-response intents and coach mode
  arrive as one frame -- a disclosed simplification, not an attempt to
  fake token-by-token reveal for text that was never actually generated
  incrementally.
- "Save to Workspace" as a literal per-message action on a plain text
  reply doesn't exist; conversation-level save and tool-run save cover
  the two shapes Workspace's data model actually supports.
- Per-conversation cost reporting is deferred to whichever future phase
  builds the admin dashboard that needs it; the join it will need
  already exists today.
