---
id: career.cover_letter.v1
version: 1
tier: standard
output_schema: schemas/career.cover_letter.v1.schema.json
max_output_tokens: 900
temperature: 0.7
cache_ttl_seconds: 0
description: Writes a cover letter citing only real resume experience, plus a shorter email version.
required_context:
  - resume_text
  - job_description_text
  - tone
  - length
---
Resume:
{{ resume_text }}

Job description:
{{ job_description_text }}

Tone: {{ tone }}
Length: {{ length }}
Emphasise: {{ emphasize }}

{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Write two sections. First, `heading: "Cover Letter"`, `body`: a full
cover letter matching the requested tone and length, addressing why
this candidate fits this specific role. Second, `heading: "Email
version"`, `body`: a much shorter version (3-5 sentences) suitable for
pasting directly into an email body.

Every claim about the candidate's experience must be traceable to the
resume text above -- never invent an employer, title, metric, or skill
that isn't there. If the job description asks for something the resume
doesn't show, don't claim it; either omit it or note genuine
transferable experience instead.

Return only JSON matching the required schema.
