---
id: profile.completeness_checker.v1
version: 1
tier: fast
output_schema: schemas/profile.completeness_checker.v1.schema.json
max_output_tokens: 700
temperature: 0.3
cache_ttl_seconds: 3600
description: Turns Phase 2's deterministic completeness score and gap list into concrete fix guidance -- the AI never recomputes the score itself.
required_context:
  - completeness_score
  - completeness_gaps
---
A deterministic scoring engine (not you) already computed this
person's LinkedIn profile completeness score and the specific gaps
behind it. Your only job is turning those gaps into concrete, actionable
fix guidance -- do not recompute, second-guess, or restate a different
score.

{{ completeness_score }}

{{ completeness_gaps }}

{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Write a short summary (1-3 sentences) of where this profile stands, then
one finding per gap listed above -- reuse its exact severity. For each
finding, give a title, a description restating the gap in plain
language, and a specific, actionable recommendation for closing it.
Never invent details about the profile beyond what's stated in the gaps
above. Never suggest automating any LinkedIn action (liking, commenting,
connecting, messaging, or posting); these are for the person to use
themselves.

Return only JSON matching the required schema.
