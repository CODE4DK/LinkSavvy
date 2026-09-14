---
id: engagement.follow_up.v1
version: 1
tier: standard
output_schema: schemas/engagement.follow_up.v1.schema.json
max_output_tokens: 500
temperature: 0.8
cache_ttl_seconds: 0
description: Generates three no-guilt follow-up messages, each with a graceful exit line.
required_context:
  - prior_context
  - time_since_last_contact
---
You are helping a LinkedIn user follow up after a gap in contact.
Using only the information below, write exactly 3 follow-up messages:

What happened before:
{{ prior_context }}

Time since last contact: {{ time_since_last_contact }}
What this follow-up is about: {{ purpose }}

{% if profile_identity is defined %}
{{ profile_identity }}
{% endif %}
{% if profile_experiences is defined %}
{{ profile_experiences }}
{% endif %}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Every message must carry a no-guilt tone -- never apologize for the
gap, never say "sorry it's been so long" or "I know you're busy but",
and never imply the recipient owes a reply. Each message needs its own
`exit_line`: a specific, graceful way to end the message that makes it
easy for the recipient to not respond without it feeling like a
rejection (e.g. offering a no-pressure out, not just "no worries
either way" repeated verbatim). Reference the prior context specifically
-- never invent a call, meeting, or promise that isn't described above.

Return only JSON matching the required schema.
