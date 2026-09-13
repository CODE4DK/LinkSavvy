# 8. Resume parsing and match scoring

Date: 2026-10-04

## Status

Accepted

## Context

Phase 07 built the Engagement Hub (small, seven tools reusing the Tool
Framework as-is) and the Career Hub's résumé pipeline (the bulk of the
phase): a canonical `ResumeDocument`, a parser that has to cope with
real-world two-column résumé layouts pdfplumber's default text
extraction scrambles, an AI-assisted "resolve what didn't parse
cleanly" step bounded to at most one gateway call per résumé, a
résumé↔JD match score whose percentage has to be checkable by hand, and
a Career Hub UI wiring all of it together. This ADR records the
decisions specific to that pipeline; the Tool Framework itself needed
no changes beyond two new, generic, reusable primitives.

## Decisions

**`ToolDefinition.postprocess` and `ToolDefinition.counts_as_outreach`
are the only two framework additions this phase needed, and both are
now used by two unrelated hubs.** `postprocess` (`(output, raw_input)
-> output`, run after a successful gateway call, before persisting)
was designed for Engagement Hub's personalisation/spam-tone flags
(`app/engagement/guardrails.py`), then reused unchanged for Career
Hub's `resume_analyzer` (merging deterministic findings ahead of the
AI's own), `ats_optimizer` (adding findings that are *only*
deterministic — the AI's own schema never contains them), and
`resume_jd_match` (deriving the generic `table` renderer's
`columns`/`rows` from the structured `matched`/`missing`/`transferable`
data, so the AI never has to know about that shape). `counts_as_outreach`
drives both the cross-tool daily soft cap and the frontend's
review-gate checkbox; Engagement Recommendations is the one Engagement
tool that opts out, since it's advice about outreach, not outreach
itself.

**The résumé parser is deterministic-first, with the AI gateway called
at most once per parse, on the whole batch of what didn't parse.**
`app/career/parsers/layout.py` reads a PDF's words with real x/y
positions (`pdfplumber.extract_words`) and looks for a genuine vertical
gap between two column bands — a gap under 3% of the page width, or one
outside the page's middle 20–80%, or one where either side has fewer
than 8 words, is treated as ordinary ragged-right text, not a column
boundary. Only when a real gap is found does it reorder into left-
column-then-right-column reading order; otherwise it falls back to
plain top-to-bottom line ordering. This is the same class of bug the
generic profile-upload extractor (`app.profiles.parsers.documents.
extract_pdf_text`) doesn't attempt to fix, because Phase 2 never needed
it — LinkedIn "copy profile text" isn't laid out in columns.
`app/career/parsers/segment.py` then does heading detection (a fixed
vocabulary, plus an ALL-CAPS-only heuristic for an unrecognised
heading — title-case was tried and rejected: ordinary content like a
school name or a two-word job title false-positived as a section
break far too often) and regex-based date/bullet parsing. Whatever it
can't confidently classify — an experience entry with no parseable
date range, or a whole section under a heading it doesn't recognise —
becomes an `AmbiguousSegment`, and every ambiguous segment across the
résumé is batched into one prompt for `app/career/parsers/resolve.py`
to classify (never one call per segment). A résumé with nothing
ambiguous makes zero AI calls to parse.

**Per-field provenance mirrors `ProfileSnapshot`'s pattern exactly, with
one more source value.** `ResumeFieldProvenance.source` is
`deterministic_parse | ai_resolved | user_edited | built |
imported_from_profile` — the same shape as Phase 2's `FieldProvenance`,
extended with `ai_resolved` so a field the one-shot resolver produced
can be told apart from one the regex pass was confident about, without
needing a separate confidence-score convention.

**Résumé↔JD Match's percentage is reconstructible because the AI
returns the arithmetic, not just the answer.** Five components (hard
requirements 0.35, preferred requirements 0.15, keyword coverage 0.2,
seniority fit 0.15, domain fit 0.15) each carry their own `weight`,
`score`, and `contribution` (`weight * score`); `overall_match` is the
rounded sum of every `contribution`. The schema doesn't *enforce* that
arithmetic (Pydantic can't cross-validate one field against a
computation over three others without a model validator this phase
didn't add, since the prompt instruction plus a golden test checking
the fixture's own arithmetic was judged sufficient for what's still a
qualitative AI judgement, not a deterministic calculation); a
regenerate can, in principle, return numbers that don't quite add up.
What *is* enforced deterministically is the frontend and the generic
`table` renderer always being able to show the components, never just
the headline number.

**ATS Optimization's structural findings are 100% deterministic; the
AI's own output schema physically cannot contain them.**
`app/career/ats_checks.py` runs headings/special-characters/layout/
file-naming/missing-keyword checks against the resume text and
whatever the Career Hub already knows about the upload (e.g. whether
`app/career/parsers/layout.py` found a two-column layout) — this can't
see a PDF's actual embedded fonts, images, or table structures, since
by the time this tool runs the résumé is already reduced to text; that
class of check is deferred, noted here rather than silently dropped.
The AI's `Output` model has exactly one field, `keyword_suggestions` —
there is no `findings` field for it to populate even if a future prompt
edit tried to; `postprocess` is what adds `findings`, entirely from
`app/career/ats_checks.py`, after the gateway call returns.

**Two pieces of B1's spec became deliberate, disclosed simplifications
given this phase's scope, not oversights:**
- The Career Hub's résumé review step shows the parsed draft as an
  editable JSON textarea (validated client-side against the same Zod
  `resumeDocumentSchema` mirror the résumé pipeline defines), not a
  field-by-field form. It satisfies "always show the parsed result for
  user correction before committing" literally, but a future phase
  should replace it with real per-field inputs (mirroring
  `apps/web/src/pages/onboarding/StepReview.tsx`'s pattern for
  `ProfileSnapshot`) before this becomes anyone's primary résumé
  workflow.
- Resume Builder's AI tool drafts one section at a time
  (summary/experience-bullets/skills-list, three variants); the
  three-ATS-safe-template picker and live preview promised by the
  spec are the deterministic `app/career/export.py` PDF/DOCX renderers
  (proven by a round-trip test that re-parses the exported file through
  this phase's own parser) plus the Career Hub's résumé panel, not a
  separate in-browser live-preview surface. A dedicated visual template
  switcher is deferred.

**`resumes.original_file_ref` reuses `ProfileImportBlob` rather than a
new blob table.** It's already exactly "encrypted-at-rest storage for
raw upload bytes, a stand-in for real object storage" (see ADR 0003);
inventing a second, career-specific blob table for the identical
storage shape would be the kind of unneeded abstraction CLAUDE.md warns
against.

**A résumé export also creates a Workspace `Asset`, but the binary
file itself is never stored as one.** `Asset.body` is text-only
(`text | markdown | json`) with no binary/blob format — matching the
existing carousel-PDF-export precedent (a streamed download, not a
saved binary), each PDF/DOCX export streams the file directly to the
browser *and* separately writes an `Asset` (`type=resume`,
`body_format=json`, the parsed `ResumeDocument`) so the export is
visible in the Workspace Hub. The two are deliberately decoupled: the
Asset records that a résumé of this shape was exported, not the exact
bytes of that one PDF or DOCX.

## Consequences

- Two new generic `ToolDefinition` hooks now serve four different
  purposes across two hubs without the framework knowing about any of
  them by name — the intended shape of "data, not code."
- The one-gateway-call-per-parse constraint means a résumé with a
  genuinely unusual structure (no recognisable headings at all) still
  makes only one AI call, batching everything ambiguous together,
  rather than degrading gracefully into many small calls.
- The JSON-textarea review step and the single-section resume builder
  are known, disclosed gaps against the full spec's "live preview" and
  "field-by-field correction" language — tracked here rather than
  quietly narrowed.
- ATS Optimization cannot check anything only visible in a document's
  original binary structure (embedded fonts, real tables, images,
  headers/footers) once the pipeline has reduced it to text; a future
  phase wanting those checks needs to inspect the original upload
  bytes directly, before text extraction discards that structure.
