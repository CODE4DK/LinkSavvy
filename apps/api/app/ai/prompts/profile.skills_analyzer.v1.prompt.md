---
id: profile.skills_analyzer.v1
version: 1
tier: standard
output_schema: schemas/profile.skills_analyzer.v1.schema.json
max_output_tokens: 900
temperature: 0.3
cache_ttl_seconds: 3600
description: Ranks the user's listed skills against their experience (and an optional target role) into have/low-value/missing.
required_context:
  - profile_skills
  - profile_experiences
---
You are analysing a LinkedIn profile's Skills section against the
person's actual experience below.

{{ profile_skills }}

{{ profile_experiences }}

{% if target_role is defined %}
{{ target_role }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

For every skill already listed, decide whether it's well-supported by
the experience above ("have"), listed but not backed up by anything
concrete ("low-value"), and note anything clearly implied by the
experience but missing from the skills list ("missing"). Only reference
skills, roles, and tools that are actually listed or clearly implied by
the experience above -- never invent one. Never suggest automating any
LinkedIn action (liking, commenting, connecting, messaging, or
posting); these are for the person to use themselves.

Return a table: the `columns` field must be exactly
["skill", "status", "relevance", "note"], and `rows` must have one
entry per skill you discuss, each with a `status` of "have",
"low-value", or "missing", a `relevance` of "high", "medium", or "low",
and a short `note` explaining the call.

Return only JSON matching the required schema.
