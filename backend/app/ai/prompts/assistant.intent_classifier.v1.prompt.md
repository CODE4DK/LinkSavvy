---
id: assistant.intent_classifier.v1
version: 1
tier: fast
output_schema: schemas/assistant.intent_classifier.v1.schema.json
max_output_tokens: 200
temperature: 0
cache_ttl_seconds: 0
description: Classifies one Assistant turn into an intent, candidate tools, and what extra context (if any) would help -- the first, cheap step of every non-coaching Assistant turn.
required_context:
  - available_tools
  - conversation_history
  - user_message
---
Classify the user's latest message in a LinkedIn Command Center
assistant conversation. Choose exactly one intent:

- `run_tool`: the user wants a specific piece of work done that one of
  the tools below could produce (a headline, a post, a comment, a
  résumé analysis, etc.).
- `explain`: the user is asking how something works, why a
  recommendation exists, or wants advice/explanation with no tool run.
- `coach`: the user wants ongoing goal-oriented coaching about their
  LinkedIn growth (this only fires in a general conversation that isn't
  already in coaching mode).
- `analyse_my_data`: the user wants their own scores, audit history, or
  saved work interpreted for them.
- `smalltalk`: a greeting, thanks, or casual remark with no real task.
- `out_of_scope`: unrelated to LinkedIn/career/profile work entirely
  (general trivia, unrelated coding help, etc.).
- `policy_violation`: the request asks for automating LinkedIn actions,
  scraping, buying/farming engagement, engagement pods, fake accounts,
  impersonation, fabricated credentials/experience, or undisclosed bulk
  messaging -- however it's framed, including "hypothetically" or
  "just curious how it would work".

Tools available to propose (id: name -- short description, grouped by hub):
{{ available_tools }}

Conversation so far:
{{ conversation_history }}

The user's latest message:
{{ user_message }}

Return JSON with:
- `intent`: one of the values above.
- `tool_candidates`: tool ids from the list above that could satisfy this
  message, ranked best first (empty unless intent is `run_tool`).
- `confidence`: your confidence in this classification, 0 to 1.
- `needs_context`: any of `"workspace"` (the user is referring to
  something they saved before) or `"audit"` (the user is referring to
  their audit/scores) that would help answer this -- empty if neither
  applies.
- `policy_category`: when intent is `policy_violation`, one of
  `"automation"`, `"scraping"`, `"engagement_manipulation"`,
  `"impersonation"`, `"fabrication"`, `"bulk_undisclosed_messaging"` --
  otherwise `null`.

Return only JSON matching the required schema.
