---
id: test.echo.v1
version: 1
tier: fast
output_schema: schemas/test.echo.v1.schema.json
max_output_tokens: 200
temperature: 0
cache_ttl_seconds: 0
description: Development-only tool proving the Tool Framework needs no bespoke frontend or router code for a new tool. Echoes its input back verbatim.
required_context:
  - user_supplied_text
---
Echo the text below back exactly as written -- no changes, no
commentary, nothing added.

{{ user_supplied_text }}
{% if regeneration_nudge %}
{{ regeneration_nudge }}
{% endif %}

Return only JSON matching the required schema, with the echoed text as
the single section's `body`.
