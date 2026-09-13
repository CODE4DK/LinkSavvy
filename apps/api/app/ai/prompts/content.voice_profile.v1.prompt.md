---
id: content.voice_profile.v1
version: 1
tier: standard
output_schema: schemas/content.voice_profile.v1.schema.json
max_output_tokens: 700
temperature: 0.4
cache_ttl_seconds: 0
description: Derives a writing-voice descriptor from a user's own past posts and their measured style signals.
required_context:
  - style_signals
  - samples
---
You are analyzing a LinkedIn writer's own past posts to describe their
voice -- not to judge it, just to describe it accurately so future
drafts can sound like them.

Measured style signals:
{{ style_signals }}

Their actual posts:
{{ samples }}

Describe this writer's voice using only patterns actually demonstrated
in the posts above -- never invent a trait, theme, or habit that isn't
shown. Give: 3 to 6 tone adjectives, up to 5 recurring themes they
write about, up to 4 signature structural habits (e.g. "opens with a
question", "always ends with a one-line takeaway"), up to 6 vocabulary
or phrasing preferences, and up to 4 things this writer clearly never
does (e.g. "never uses emoji", "never writes in third person"). Leave
a list empty rather than padding it with something not actually
observed.

Return only JSON matching the required schema.
