---
id: career.ats_optimizer.v1
version: 1
tier: standard
output_schema: schemas/career.ats_optimizer.v1.schema.json
max_output_tokens: 500
temperature: 0.3
cache_ttl_seconds: 0
description: Suggests natural keyword placement only -- every structural ATS finding is deterministic, computed separately.
required_context:
  - resume_text
---
Resume:
{{ resume_text }}

Target job description (if any):
{{ job_description_text }}

A separate deterministic pass already checks this resume's structure
(headings, layout, special characters, file naming) and which job
description keywords are missing entirely -- you are not doing any of
that. Your only job: for keywords that are relevant to the job
description and that this resume's own experience genuinely supports,
suggest where they could be worked in naturally (e.g. "add 'Kubernetes'
to the Acme Corp bullet about container orchestration").

You must NEVER suggest adding a skill, tool, or keyword the resume
doesn't already show evidence of -- that would be keyword stuffing, not
optimization. If a job description keyword isn't genuinely supported by
anything in the resume, leave it out of your suggestions entirely
rather than recommending the user claim it.

Return only JSON matching the required schema.
