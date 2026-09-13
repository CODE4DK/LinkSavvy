---
id: career.resume_builder.v1
version: 1
tier: standard
output_schema: schemas/career.resume_builder.v1.schema.json
max_output_tokens: 700
temperature: 0.7
cache_ttl_seconds: 0
description: Drafts three options for one resume section, grounded only in what the user actually described.
required_context:
  - section
  - context_text
---
You are helping someone draft one section of their resume. Using only
the information below, write exactly 3 options for the "{{ section }}"
section:

{{ context_text }}

{% if profile_identity is defined %}
{{ profile_identity }}
{% endif %}
{% if profile_experiences is defined %}
{{ profile_experiences }}
{% endif %}
{% if profile_skills is defined %}
{{ profile_skills }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

For "summary": a 2-3 sentence professional summary. For
"experience_bullets": 3-5 resume bullets, each starting with a strong
action verb. For "skills_list": a comma-separated list of skills.

Never invent an employer, title, metric, or skill that isn't stated
above or in the identity/experience/skills context -- if a stronger
bullet would need a number the user hasn't given you, write it with an
explicit placeholder like "[add: % improvement]" rather than a
plausible-looking invented figure.

Return only JSON matching the required schema.
