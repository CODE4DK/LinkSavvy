---
id: audit.engagement_opportunities.v1
version: 1
tier: standard
output_schema: schemas/audit.engagement_opportunities.v1.schema.json
max_output_tokens: 500
temperature: 0.7
cache_ttl_seconds: 604800
description: Suggests concrete, manual networking and engagement opportunities for the Audit Engine's Engagement category.
required_context:
  - headline
  - industry
  - target_role
---
Suggest 2 to 4 concrete ways this person could manually grow their
LinkedIn network and engagement, based on who they are:

Headline:
{{ headline }}

Industry:
{{ industry }}

Target role:
{{ target_role }}

Each suggestion must be something the person does themselves by hand --
never suggest automation, bots, scripts, or any tool that likes,
comments, connects, messages, or posts on their behalf. Good examples:
commenting thoughtfully on posts from specific kinds of people, joining
and participating in relevant LinkedIn groups, sharing a specific type of
update. Be concrete and specific to this person's field, not generic
advice that would apply to anyone.

Return only JSON matching the required schema.
