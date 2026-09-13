# 7. Content preview fidelity and carousel export

Date: 2026-09-27

## Status

Accepted

## Context

Phase 06 needs two things LinkedIn doesn't hand us a spec for: a
Composer preview that looks enough like the real LinkedIn post
renderer to be useful (truncation fold, hashtag/mention styling,
mobile/desktop width) without ever touching linkedin.com to check —
CLAUDE.md's hard compliance rule forbids scraping or driving a headless
browser against LinkedIn, so there is no "read the real DOM" option
even for a read-only preview — and a carousel exporter that produces
both a PDF suitable for a LinkedIn document post (selectable text) and
a set of PNGs, from the same slide data a browser-based editor lets the
user reorder and rewrite.

## Decisions

**The LinkedIn preview is an observed approximation, not a
reverse-engineered spec, and says so.** `apps/web/src/content/
linkedin-preview-config.ts` holds three constants —
`LINKEDIN_POST_CHAR_LIMIT` (3,000, LinkedIn's real published limit),
`LINKEDIN_WARNING_THRESHOLD` (2,800), and `LINKEDIN_FOLD_CHAR_LIMIT`
(210, an observed "see more" cut point) — each commented as a value
that can drift as LinkedIn changes its own rendering, deliberately
extracted into one file rather than inlined in `LinkedInPreview.tsx` so
a future re-measurement is a one-line change. Hashtags and @-mentions
are detected with a plain regex (`#[\w-]+|@[\w.-]+`) and styled as
links; there is no real mention resolution (LinkedIn mentions encode a
profile URN we have no way to look up without an API scope this app
doesn't request), so an `@word` in plain text renders identically to a
resolved mention — an acceptable approximation for a drafting aid, not
a claim of pixel-perfect fidelity.

**Formatting helpers are honest about their real cost.** LinkedIn has
no native bold/italic for post text. The optional Unicode-styling
helper (`unicode-style.ts`) substitutes Mathematical Alphanumeric
Symbols that merely *look* styled — a different character than the
letter it replaces — and the Composer shows an explicit modal warning
that this hurts screen-reader accessibility before applying it, never
silently. This was a deliberate choice not to hide the tradeoff behind
a convenient-looking "Bold" button.

**reportlab over WeasyPrint for the carousel PDF, because of the
dependency footprint, not the API.** Both were named as acceptable
choices. WeasyPrint renders HTML/CSS through Cairo/Pango/GDK-Pixbuf —
system-level native libraries that aren't reliably available (or
installable without root) in every environment this app runs in,
including this sandbox. reportlab is a pip-installable Python package
with no system dependency, draws directly via a `canvas.Canvas` API
well suited to the carousel's simple, fixed layout (a headline, a body,
an accent bar, a footer — never arbitrary HTML), and produces real
drawn glyphs via `drawString`, which is what makes the exported text
selectable and copyable rather than a rasterized image — verified in
`tests/content/test_carousel_layout.py` by extracting text back out of
a generated PDF with `pdfplumber` and asserting the actual words are
there.

**PDF and PNG export share one layout module so they can't visually
drift apart.** `app/content/carousel_layout.py`'s `compute_slide_layout`
is pure data — background/text colours (the app's real design tokens
from `apps/web/src/styles/tokens.css`, hand-converted from HSL to hex
since Python can't read a CSS custom property), wrapped text, footer —
with no drawing calls in it. `carousel_pdf.py` (reportlab) and
`carousel_png.py` (Pillow) each interpret the same `SlideLayout` value
through their own APIs; a third export format would add a third
interpreter, never a second copy of the layout math. PNG rendering uses
only Pillow's own bundled scalable default font
(`ImageFont.load_default(size=N)`) rather than bundling a font file, so
there's no font asset to go missing or need a licence check.

**The carousel's canvas is 1080x1350 in both formats, with no unit
conversion between them.** LinkedIn's own recommended document-post
size is 1080x1350 pixels (a 4:5 ratio); the PDF's page size is set to
the same 1080x1350 in points rather than converting to a physical page
size like Letter or A4, since this is a digital asset meant for upload,
never printed to a specific real-world dimension. That decision is what
lets `compute_slide_layout`'s margins and positions mean the same thing
in both renderers without a DPI-based scale factor anywhere.

## Consequences

- If LinkedIn changes its actual fold position, mention rendering, or
  post character limit, the fix is re-measuring and updating
  `linkedin-preview-config.ts` — there is no automated way to detect
  drift, since the hard compliance rule rules out the obvious approach
  (loading a real LinkedIn post and diffing).
- `apps/web/src/styles/tokens.css`'s light-theme palette and
  `carousel_layout.py`'s hard-coded hex constants can drift out of sync
  if the design tokens change without a corresponding update here —
  there's no build-time link between a CSS custom property and a Python
  string literal.
- Three layout templates (clean/bold/minimal) cover today's carousel
  builder; a fourth template is a new `LayoutTemplate` branch in
  `compute_slide_layout` plus matching cases in both `carousel_pdf.py`
  and `carousel_png.py` — the shared-layout-module decision means those
  two additions can't fall out of sync with each other, but they are
  still two separate code changes, not one.
- The PNG export's text wrapping and the PDF export's text wrapping are
  independently implemented (`_wrap_text` in each module) against their
  own font-measurement APIs (`ImageDraw.textlength` vs.
  `canvas.stringWidth`), since Pillow and reportlab have no common
  metrics interface — the two will not always break lines at exactly
  the same word if a font substitution ever changes either library's
  default metrics, though both draw from the same `SlideLayout` text.
