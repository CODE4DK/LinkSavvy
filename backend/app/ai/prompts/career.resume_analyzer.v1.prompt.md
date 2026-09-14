---
id: career.resume_analyzer.v1
version: 1
tier: standard
output_schema: schemas/career.resume_analyzer.v1.schema.json
max_output_tokens: 1200
temperature: 0.4
cache_ttl_seconds: 0
description: Scores a resume across six dimensions with per-bullet AI feedback (deterministic checks are added separately).
required_context:
  - resume_text
---
You are reviewing this resume:

{{ resume_text }}

{% if profile_identity is defined %}
{{ profile_identity }}
{% endif %}
{% if profile_experiences is defined %}
{{ profile_experiences }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Score it from 0-10 on each of these six dimensions, with a one-sentence
note for each: impact (does it show outcomes, not just duties?),
clarity (is it easy to follow?), quantification (are results
measured?), relevance (does it support a plausible target role?),
formatting (is it scannable?), length (is it an appropriate length?).
Give an overall `score` (0-100) and a one-paragraph `summary`.

Then give your own qualitative `findings` (each with a `title`,
`severity` of info/warning/critical, a `description`, and an optional
`recommendation`) -- focus on things a rule can't easily catch: weak
narrative arc, a role description that undersells its scope, a summary
that doesn't match the roles below it. Do not repeat purely mechanical
checks like bullet counts or missing numbers; a separate deterministic
pass already covers those. Base every finding only on what's actually
in the resume text above -- never invent a job, metric, or skill that
isn't there.

Return only JSON matching the required schema.
