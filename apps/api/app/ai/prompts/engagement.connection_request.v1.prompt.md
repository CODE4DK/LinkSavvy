---
id: engagement.connection_request.v1
version: 1
tier: standard
output_schema: schemas/engagement.connection_request.v1.schema.json
max_output_tokens: 400
temperature: 0.8
cache_ttl_seconds: 0
description: Generates three connection request notes, each within LinkedIn's 300-character limit.
required_context:
  - who_they_are
---
You are helping a LinkedIn user write a connection request note.
LinkedIn hard-caps connection notes at 300 characters -- every note you
write MUST be 300 characters or fewer, no exceptions. Using only the
information below, write exactly 3 notes:

Who they are:
{{ who_they_are }}

How they know them / why reaching out: {{ how_you_know_them }}
Their goal: {{ goal }}

{% if profile_identity is defined %}
{{ profile_identity }}
{% endif %}
{% if profile_experiences is defined %}
{{ profile_experiences }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Each note must reference something specific about this person from the
information above -- never a note generic enough to send to anyone.
Never claim a prior conversation, meeting, or interaction that isn't
described above. Never write a note that could be sent unchanged to a
hundred different people. Count characters as you write -- a note over
300 characters will be rejected outright, not shortened for you.

Return only JSON matching the required schema.
