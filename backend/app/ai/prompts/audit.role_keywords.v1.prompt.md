---
id: audit.role_keywords.v1
version: 1
tier: fast
output_schema: schemas/audit.role_keywords.v1.schema.json
max_output_tokens: 400
temperature: 0.2
cache_ttl_seconds: 2592000
description: Generates the expected keyword vocabulary and must-have skills for a target job role, shared across several Audit Engine categories.
required_context:
  - target_role
---
List the vocabulary a recruiter or search algorithm would expect to see
on a LinkedIn profile for someone targeting this role:

Target role:
{{ target_role }}

Return two lists:
- keywords: 10 to 20 general terms, tools, and phrases commonly
  associated with this role (used to check keyword coverage in a
  headline and About section).
- must_have_skills: 5 to 10 specific skills someone in this role would
  typically list on LinkedIn.

Base this only on common, well-known conventions for the role -- don't
invent anything obscure or speculative.

Return only JSON matching the required schema.
