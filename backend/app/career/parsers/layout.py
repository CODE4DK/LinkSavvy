"""Layout-aware PDF text extraction for resumes.

The generic profile-upload extractor (`app.profiles.parsers.documents.
extract_pdf_text`) reads each page as one text stream in whatever order
the PDF's content stream happens to list characters -- for a single-
column resume that's fine, but for a two-column one it interleaves the
columns line by line, scrambling the result. This module instead reads
each page's words with their real x/y positions (pdfplumber's
`extract_words`), looks for a genuine vertical gap between two column
bands, and -- only when one is found -- emits the left column's lines
in full before the right column's, which is what a human reader
actually does with a two-column resume.

`_reading_order_text` is a pure function over plain word dicts
(`{text, x0, x1, top, bottom}`) specifically so the column-detection
logic can be unit-tested without needing to generate real PDF bytes.
"""

from __future__ import annotations

import io
from typing import TypedDict

import pdfplumber

from app.profiles.parsers.documents import UnsupportedDocumentError

# A gap narrower than this fraction of the page width is just normal
# ragged-right text, not a real column boundary.
_MIN_GAP_FRACTION = 0.03
# The gap must fall inside this middle band of the page -- a gap near
# either edge is just a margin, not a split between two columns.
_GAP_SEARCH_START_FRACTION = 0.2
_GAP_SEARCH_END_FRACTION = 0.8
# Each side needs a meaningful number of words before we trust that a
# gap is a real column split rather than a stray short line.
_MIN_WORDS_PER_COLUMN = 8
_BUCKET_COUNT = 200


class Word(TypedDict):
    text: str
    x0: float
    x1: float
    top: float
    bottom: float


def _find_column_gap(words: list[Word], page_width: float) -> float | None:
    if page_width <= 0 or len(words) < _MIN_WORDS_PER_COLUMN * 2:
        return None

    bucket_width = page_width / _BUCKET_COUNT
    covered = [False] * _BUCKET_COUNT
    for word in words:
        start = max(0, int(word["x0"] / bucket_width))
        end = min(_BUCKET_COUNT - 1, int(word["x1"] / bucket_width))
        for bucket in range(start, end + 1):
            covered[bucket] = True

    search_start = int(_GAP_SEARCH_START_FRACTION * _BUCKET_COUNT)
    search_end = int(_GAP_SEARCH_END_FRACTION * _BUCKET_COUNT)
    min_gap_buckets = max(1, int(_MIN_GAP_FRACTION * _BUCKET_COUNT))

    best_gap: tuple[int, int] | None = None
    run_start: int | None = None
    for bucket in range(search_start, search_end + 1):
        if not covered[bucket]:
            if run_start is None:
                run_start = bucket
        else:
            if run_start is not None:
                run_length = bucket - run_start
                if run_length >= min_gap_buckets and (
                    best_gap is None or run_length > (best_gap[1] - best_gap[0])
                ):
                    best_gap = (run_start, bucket)
                run_start = None
    if run_start is not None:
        run_length = search_end + 1 - run_start
        if run_length >= min_gap_buckets and (
            best_gap is None or run_length > (best_gap[1] - best_gap[0])
        ):
            best_gap = (run_start, search_end + 1)

    if best_gap is None:
        return None

    gap_x = (best_gap[0] + best_gap[1]) / 2 * bucket_width
    left_count = sum(1 for w in words if w["x1"] <= gap_x)
    right_count = sum(1 for w in words if w["x0"] >= gap_x)
    if left_count < _MIN_WORDS_PER_COLUMN or right_count < _MIN_WORDS_PER_COLUMN:
        return None
    return gap_x


def _lines_from_words(words: list[Word], *, line_tolerance: float = 3.0) -> str:
    if not words:
        return ""
    ordered = sorted(words, key=lambda w: (w["top"], w["x0"]))
    lines: list[list[Word]] = []
    for word in ordered:
        if lines and abs(word["top"] - lines[-1][-1]["top"]) <= line_tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])
    rendered = []
    for line in lines:
        line.sort(key=lambda w: w["x0"])
        rendered.append(" ".join(w["text"] for w in line))
    return "\n".join(rendered)


def _reading_order_text(words: list[Word], page_width: float) -> str:
    """The pure column-detection/reordering logic, over plain word dicts
    -- see the module docstring for why this is split out from the
    pdfplumber-specific extraction below."""
    if not words:
        return ""
    gap_x = _find_column_gap(words, page_width)
    if gap_x is None:
        return _lines_from_words(words)

    left = [w for w in words if w["x1"] <= gap_x]
    right = [w for w in words if w["x0"] >= gap_x]
    straddling = [w for w in words if w["x1"] > gap_x and w["x0"] < gap_x]
    left.extend(straddling)  # a word spanning the gap almost certainly belongs left
    return f"{_lines_from_words(left)}\n\n{_lines_from_words(right)}"


def extract_resume_pdf_text(data: bytes) -> str:
    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as exc:
        raise UnsupportedDocumentError(
            "This PDF couldn't be read -- it may be corrupted. Please try the paste "
            "option instead."
        ) from exc

    try:
        pages_text = []
        for page in pdf.pages:
            raw_words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            words: list[Word] = [
                {
                    "text": w["text"],
                    "x0": w["x0"],
                    "x1": w["x1"],
                    "top": w["top"],
                    "bottom": w["bottom"],
                }
                for w in raw_words
            ]
            pages_text.append(_reading_order_text(words, page.width))
    finally:
        pdf.close()

    text = "\n\n".join(pages_text)
    if not text.strip():
        raise UnsupportedDocumentError(
            "We couldn't find any text in this PDF -- it may be a scanned image. "
            "Please try the paste option instead."
        )
    return text
