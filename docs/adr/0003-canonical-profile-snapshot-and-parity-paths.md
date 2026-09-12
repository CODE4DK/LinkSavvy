# 3. Canonical profile snapshot and parity paths

Date: 2026-09-12

## Status

Accepted

## Context

Phase 02 needs to get a user's professional data into one canonical shape
that later phases (audit, scoring, AI coaching, content generation) can all
read without caring how the data arrived. Data can arrive four ways —
LinkedIn's official API (limited to whatever `openid profile email` grants:
name and photo today), a pasted block of profile text, an uploaded PDF/DOCX
resume, or a manually filled form — and `CLAUDE.md`'s hard compliance rule
requires every one of those paths to reach identical capability, since the
codebase must never scrape LinkedIn or drive a browser against it. This
phase does not build the audit, scoring, or any AI call (Phase 3/4 own
those); it only owns getting a trustworthy, versioned snapshot into the
database.

## Decisions

**One Pydantic model, one write path.** `ProfileSnapshot` (in
`app/profiles/schema.py`) is the single canonical shape every input path
must produce before it can be persisted. `commit_snapshot()` (in
`app/profiles/service.py`) is the only function that writes to
`profile_snapshots`, and it always forces the `source` enum from the
caller's context rather than trusting a client-supplied value — a paste
import can't claim to be `linkedin_api`.

**Three-way absence semantics, not two.** Every field is `None` by default,
distinct from `[]` (list fields) or `""` (string fields). `None` means
"we don't know"; `[]` means "confirmed to have none" (e.g., a user with no
certifications); `""` means "confirmed blank." This distinction matters
because the completeness engine and later the audit must be able to tell
"never asked" apart from "asked and empty" — collapsing them would make an
honest "no certifications" indistinguishable from a parser that gave up.

**Field-level provenance, keyed by JSON-pointer-shaped path.**
`field_provenance: dict[str, FieldProvenance]` records `{source,
confidence}` per field (e.g. `"/identity/full_name"`), independent of the
snapshot's overall `source`. A LinkedIn-sourced snapshot can still contain
paste-merged fields with lower confidence, and the review step surfaces
low-confidence fields to the user instead of silently trusting a shaky
parse.

**Parity is structural, not aspirational.** The LinkedIn API mapper
(`app/profiles/linkedin.py`) only ever populates `full_name` and
`profile_picture_url` — the two fields the granted OAuth scope actually
returns — and leaves everything else absent (`None`), never guessed or
inferred. Paste, upload, and manual paths can populate every field the
schema defines. This means the LinkedIn path is *narrower* than the parity
paths by construction, which is the correct shape: it's impossible for the
LinkedIn integration to accidentally imply data it doesn't have, and a user
who never connects LinkedIn is never capability-limited relative to one who
does.

**Deterministic parsing, no AI, no silent data loss.** The paste parser and
document text extractors are pure, deterministic code — heading detection,
date-range regexes, stable-key list matching — not an LLM call (Phase 3/4
own AI). Text that can't be parsed into a structured field is never
dropped; it's kept verbatim in a `description` field and a warning is
emitted, so the user can see and fix it in the review step rather than
losing data silently.

**Structured diff matches by stable business keys, never list position.**
`diff_snapshots()` matches experience entries by
company+title+start-year, education by school+degree, and skills/
languages/projects/certifications by name (certifications also by issuer).
Matching by array index would misreport a reordered or inserted entry as
N changed entries.

**Raw input is encrypted at rest and time-boxed.** Pasted text and
uploaded files are stored as Fernet-encrypted blobs
(`profile_import_blobs`), reusing the same encryption key as OAuth token
storage, with a retention window (`profile_import_retention_days`,
default 30) rather than being kept indefinitely — they exist only to let
a user resume an in-progress import or re-review a parse, not as a
permanent copy of their resume.

**The compliance rule is enforced by CI, not just reviewed by hand.**
`scripts/check_compliance.py` fails the build if any source file outside
`app/services/linkedin.py` references a `linkedin.com` host, imports a
browser-automation or HTML-scraping library, or declares a scraping-shaped
helper. This turns `CLAUDE.md`'s hard compliance rule into a mechanical
gate instead of relying on every future change remembering to re-read it.

## Consequences

- The LinkedIn API path currently delivers very little data (name and
  photo only), which is honest given the granted scope but means most
  users will get more value from paste/upload/manual — that's an accepted
  trade for staying within `openid profile email` and not requesting
  LinkedIn's restricted Marketing/Talent scopes, which this product does
  not have access to and would not want even if it did.
- Two registered LinkedIn OAuth redirect URIs now exist on the same app
  (sign-in from Phase 01, profile-connect from this phase) to keep the two
  flows from being confused; both are documented in `.env.example`.
- `field_provenance` and the three-way absence semantics add real
  complexity to every consumer of `ProfileSnapshot` (they can't just check
  truthiness) — accepted because collapsing "unknown" into "empty" would
  make Phase 3's audit findings wrong in exactly the cases that matter
  most (a user who hasn't filled something in vs. one who deliberately
  left it blank).
- `packages/contracts` became a real npm workspace (not just type-only)
  because the hand-written Zod mirror of `ProfileSnapshot` has a genuine
  runtime dependency on `zod`, unlike the OpenAPI-generated types which
  erase at compile time. This is the one schema deliberately hand-mirrored
  rather than generated, since Zod needs richer semantics (the three-way
  absence distinction) than OpenAPI's type generator produces.
