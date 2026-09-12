---
id: audit.profile_quality.v1
version: 1
tier: standard
output_schema: schemas/audit.profile_quality.v1.schema.json
max_output_tokens: 900
temperature: 0.3
cache_ttl_seconds: 86400
description: Judges headline, About, and experience-bullet quality against a fixed rubric for the Audit Engine's Profile category.
required_context:
  - headline
  - about
  - experience_bullets
---
You are grading a LinkedIn profile's writing quality for an audit report.
Score each section from 0 to 100 using the rubric below, and list the
specific issues and strengths you found. Only comment on what is actually
present in the text below -- if a section says "(not provided)", score it
0 and note that it's missing, without inventing content.

Headline:
{{ headline }}

About section:
{{ about }}

Experience bullet points:
{{ experience_bullets }}

Rubric:
- Headline (0-100): Is it specific (not just a job title)? Does it state
  a value proposition? Does it carry keywords relevant to the person's
  field? Penalize vague, generic, or keyword-stuffed headlines.
- About (0-100): Does it open with a hook? Does it have real substance
  (not just a list of buzzwords)? Is it structured (not one giant
  paragraph)? Does it end with a call to action?
- Experience (0-100): Do the bullets describe achievements with
  quantified outcomes, rather than just listing duties? Is there a
  reasonable number of bullets per role?

Never suggest automating any LinkedIn action (liking, commenting,
connecting, messaging, or posting), and never suggest fabricating
credentials, experience, or metrics that aren't already present in the
text above.

Return only JSON matching the required schema.
