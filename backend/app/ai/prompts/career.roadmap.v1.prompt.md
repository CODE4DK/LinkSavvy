---
id: career.roadmap.v1
version: 1
tier: standard
output_schema: schemas/career.roadmap.v1.schema.json
max_output_tokens: 1400
temperature: 0.6
cache_ttl_seconds: 0
description: Phased milestones from a current role to a target role, each phase tied back to a LinkSavvy tool.
required_context:
  - current_role
  - target_role
  - time_horizon
---
Current role: {{ current_role }}

{{ target_role }}

Time horizon: {{ time_horizon }}
Constraints: {{ constraints }}

{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Break the path from the current role to the target role into 2 to 5
phases across the time horizon given. Each phase needs a `heading`
(e.g. "Phase 1: Build foundational skills (months 1-3)"), a one-line
`body` summarising the phase, and at least 4 `bullets` covering: a
skill to build, a piece of evidence to create (a project, a
certification, a measurable result), a person or community to learn
from, and a concrete LinkedIn action for that phase -- naming which
LinkSavvy tool it maps to (e.g. "Use the Resume <-> JD Match tool to
check readiness for target-role postings" or "Use Engagement
Recommendations to find the right communities to join").

Never invent a credential, employer, or metric the user hasn't
described -- if a bullet would be stronger with a specific number the
user hasn't given you, mark it with `flagged: true` and a
`flag_reason` explaining what input is needed, rather than inventing a
plausible-looking one.

Return only JSON matching the required schema.
