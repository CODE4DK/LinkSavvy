---
id: profile.keyword_optimizer.v1
version: 1
tier: standard
output_schema: schemas/profile.keyword_optimizer.v1.schema.json
max_output_tokens: 900
temperature: 0.3
cache_ttl_seconds: 3600
description: Prioritised search keywords a LinkedIn profile should surface, whether each is already present, and where to place it.
required_context:
  - profile_identity
  - profile_experiences
  - profile_skills
---
You are optimising a LinkedIn profile for search. Using only the
information below, identify the keywords recruiters and search would
use to find this person.

{{ profile_identity }}

{{ profile_experiences }}

{{ profile_skills }}

{% if target_role is defined %}
{{ target_role }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Only suggest keywords grounded in the experience, skills, or target
role above -- never invent a technology, credential, or specialty the
person hasn't shown. Never suggest automating any LinkedIn action
(liking, commenting, connecting, messaging, or posting); these are for
the person to use themselves.

Return a table: the `columns` field must be exactly
["keyword", "priority", "coverage", "placement"], and `rows` must have
one entry per keyword, each with a `priority` of "high", "medium", or
"low", a `coverage` of "present" (already appears somewhere on the
profile) or "missing", and a `placement` naming where to add it
(e.g. "headline", "About section", "most recent experience bullet").

Return only JSON matching the required schema.
