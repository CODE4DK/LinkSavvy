---
id: career.resume_segment_resolver.v1
version: 1
tier: standard
output_schema: schemas/career.resume_segment_resolver.v1.schema.json
max_output_tokens: 1200
temperature: 0.2
cache_ttl_seconds: 0
description: Resolves resume segments the deterministic parser could not confidently classify, in one batched call.
required_context:
  - segments
---
A deterministic resume parser has already extracted everything it
could confidently structure. The segments below are what it could
NOT confidently classify -- each is either an experience entry with no
parseable date range, or text under a heading the parser didn't
recognise. Your job is only to classify and structure these segments;
never touch anything the parser already handled.

{{ segments }}

For each segment, decide whether it's an experience entry (a job) or a
custom section (anything else -- volunteer work, awards mixed with
narrative, publications, hobbies relevant to the field, etc.), and
return it under the matching list, always including its `segment_id`
unchanged so it can be matched back up.

For an experience entry: fill in only the fields the text actually
supports -- leave a field null/empty rather than guessing. Never invent
a company, title, date, or metric that isn't stated in the segment's
own text.

For a custom section: use the segment's own heading guess (or a
cleaned-up version of it) as `heading`, and turn its content into
`bullets` -- one bullet per distinct point, not one giant bullet.

If a segment's content is too sparse or ambiguous to classify at all,
put it under custom_sections with whatever heading it had rather than
dropping it or forcing it into experience.

Return only JSON matching the required schema.
