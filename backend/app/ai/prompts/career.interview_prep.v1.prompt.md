---
id: career.interview_prep.v1
version: 1
tier: standard
output_schema: schemas/career.interview_prep.v1.schema.json
max_output_tokens: 1400
temperature: 0.6
cache_ttl_seconds: 0
description: Likely interview questions with STAR scaffolds from the candidate's own experience, plus questions to ask.
required_context:
  - job_description_text
  - interview_type
---
Job description:
{{ job_description_text }}

Interview type: {{ interview_type }}
Seniority: {{ seniority }}

Candidate's resume (for STAR scaffolds):
{{ resume_text }}

{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Generate 5 to 9 messages with `role: "interviewer"`, each `text`
covering one likely question for a {{ interview_type }} interview at
this seniority: the question itself, one sentence on what the
interviewer is really assessing, a STAR (Situation/Task/Action/Result)
scaffold drawn from the candidate's actual resume experience above
(never an invented example), and one or two likely follow-up
questions. Then add exactly one final message with `role: "candidate"`
listing 3-5 good questions this candidate should ask the interviewer,
specific to this role and company rather than generic ones.

If the resume doesn't contain a good example for a given question,
say so in the STAR scaffold rather than inventing one.

Return only JSON matching the required schema.
