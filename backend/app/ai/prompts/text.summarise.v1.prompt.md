---
id: text.summarise.v1
version: 1
tier: fast
output_schema: text
max_output_tokens: 300
temperature: 0.5
cache_ttl_seconds: 3600
description: Summarizes a block of text in two or three plain-language sentences.
required_context:
  - text
---
Summarize the text below in two or three plain-language sentences.
Only use information present in the text -- don't add anything that
isn't there, and don't suggest automating any action on LinkedIn.

Text:
{{ text }}
