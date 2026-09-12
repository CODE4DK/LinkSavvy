---
id: meta.classify_intent.v1
version: 1
tier: fast
output_schema: schemas/meta.classify_intent.v1.schema.json
max_output_tokens: 100
temperature: 0.0
cache_ttl_seconds: 0
description: Classifies which LinkSavvy capability a free-text user message is asking for.
required_context:
  - message
---
Classify which capability the user's message below is asking for.
Respond with exactly one intent from this closed set: rewrite_headline,
summarize_profile, draft_post, analyze_resume, other.

Message:
{{ message }}

Return only JSON matching the required schema: the chosen intent and a
confidence score between 0 and 1.
