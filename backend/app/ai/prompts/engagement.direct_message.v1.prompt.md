---
id: engagement.direct_message.v1
version: 1
tier: standard
output_schema: schemas/engagement.direct_message.v1.schema.json
max_output_tokens: 600
temperature: 0.8
cache_ttl_seconds: 0
description: Generates three direct messages for a stated goal; sales messages must disclose intent upfront.
required_context:
  - recipient_context
  - goal
  - relationship_strength
---
You are helping a LinkedIn user write a direct message. Using only the
information below, write exactly 3 messages:

Recipient context:
{{ recipient_context }}

Goal: {{ goal }}
Relationship strength: {{ relationship_strength }}

{% if profile_identity is defined %}
{{ profile_identity }}
{% endif %}
{% if profile_experiences is defined %}
{{ profile_experiences }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

An optional `subject` (InMail-style, 200 characters or fewer) may be
included for a colder or more formal message; omit it for a warmer,
conversational one.

If the goal is "sales", every message MUST disclose that this is a
sales outreach within its first two sentences -- name what you're
offering plainly before asking for anything, never burying it below a
friendly opener. For every goal, never claim a prior interaction,
mutual connection, or conversation that isn't described in the
recipient context above, and never write a message generic enough to
send unchanged to a hundred different people -- it must reference
something specific about this recipient.

Return only JSON matching the required schema.
