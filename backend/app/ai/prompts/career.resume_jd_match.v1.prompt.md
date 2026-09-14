---
id: career.resume_jd_match.v1
version: 1
tier: standard
output_schema: schemas/career.resume_jd_match.v1.schema.json
max_output_tokens: 1400
temperature: 0.3
cache_ttl_seconds: 0
description: Scores how well a resume matches a job description, as five weighted, reconstructible components.
required_context:
  - resume_text
  - job_description_text
---
Resume:
{{ resume_text }}

Job description:
{{ job_description_text }}

{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Score the match across exactly these five components, each with a
`weight` (the five weights must sum to 1.0) and a `score` (0-100):
hard_requirements (weight 0.35), preferred_requirements (weight 0.15),
keyword_coverage (weight 0.2), seniority_fit (weight 0.15), domain_fit
(weight 0.15). For each component's `contribution`, compute
`weight * score` exactly. Set `overall_match` to the sum of all five
contributions, rounded to the nearest integer -- the arithmetic must
be reconstructible from the numbers you return, not just asserted.

List `matched`: requirements the resume genuinely satisfies, each with
`evidence` quoting or closely paraphrasing the resume. List `missing`:
requirements the resume doesn't show, each marked `learnable` (true if
it's a skill picked up on the job) or false (a hard blocker, like a
required certification or clearance). List `transferable`: experience
that maps to a requirement but is worded differently in the resume,
naming the actual resume experience it corresponds to.

Never claim the resume shows something it doesn't -- only cite
evidence that's actually present in the resume text above.

Return only JSON matching the required schema.
