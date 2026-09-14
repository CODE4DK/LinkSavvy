from __future__ import annotations

from app.career.parsers.layout import Word, _find_column_gap, _reading_order_text

PAGE_WIDTH = 600.0


def _line_words(text: str, *, x0: float, top: float) -> list[Word]:
    words: list[Word] = []
    cursor = x0
    for token in text.split():
        x1 = cursor + len(token) * 6.0
        words.append({"text": token, "x0": cursor, "x1": x1, "top": top, "bottom": top + 12.0})
        cursor = x1 + 4.0
    return words


def test_single_column_preserves_top_to_bottom_order() -> None:
    words: list[Word] = []
    words += _line_words("Senior Backend Engineer", x0=50, top=50)
    words += _line_words("Acme Corp 2019 to 2023", x0=50, top=70)
    words += _line_words("Built distributed systems at scale", x0=50, top=90)

    text = _reading_order_text(words, PAGE_WIDTH)
    lines = text.splitlines()
    assert lines[0] == "Senior Backend Engineer"
    assert lines[1] == "Acme Corp 2019 to 2023"
    assert lines[2] == "Built distributed systems at scale"


def test_two_column_gap_is_detected() -> None:
    words: list[Word] = []
    for i in range(10):
        words += _line_words(f"left line number {i}", x0=40, top=50 + i * 15)
    for i in range(10):
        words += _line_words(f"right line number {i}", x0=350, top=50 + i * 15)

    gap = _find_column_gap(words, PAGE_WIDTH)
    assert gap is not None
    assert 200 < gap < 350


def test_two_column_resume_is_not_interleaved() -> None:
    left_lines = [
        "Experience",
        "Senior Backend Engineer at Acme Corp",
        "Led a team of eight engineers",
        "Reduced incident response time by half",
        "Owned the on call rotation redesign",
        "Education",
        "BS Computer Science",
        "State University 2015",
    ]
    right_lines = [
        "Skills",
        "Python Go SQL Kubernetes",
        "Leadership and mentoring",
        "Distributed systems design",
        "Certifications",
        "AWS Solutions Architect",
        "Contact",
        "jordan example com",
    ]

    words: list[Word] = []
    # Interleave left/right lines in raw stream order to simulate how a
    # two-column PDF's content stream actually orders text -- proving the
    # reordering logic, not just a lucky already-sorted input.
    for i, (left, right) in enumerate(zip(left_lines, right_lines, strict=True)):
        top = 50 + i * 20
        words += _line_words(left, x0=40, top=top)
        words += _line_words(right, x0=350, top=top)

    text = _reading_order_text(words, PAGE_WIDTH)
    left_block, _, right_block = text.partition("\n\n")

    for line in left_lines:
        assert line in left_block
    for line in right_lines:
        assert line in right_block
    # None of the right column's lines should have leaked into the left
    # block (the classic two-column interleaving bug this exists to fix).
    for line in right_lines:
        assert line not in left_block


def test_narrow_gap_is_not_mistaken_for_a_column_boundary() -> None:
    words: list[Word] = []
    # A normal single-column paragraph with ragged-right lines -- the
    # largest "gap" here is just where a short line ends, well under the
    # minimum fraction of the page width required to count as a column.
    words += _line_words("A short line here", x0=40, top=50)
    words += _line_words(
        "A much longer line that runs most of the way across the page width", x0=40, top=70
    )
    assert _find_column_gap(words, PAGE_WIDTH) is None


def test_gap_requires_enough_words_on_each_side() -> None:
    words: list[Word] = []
    words += _line_words("just one short line", x0=40, top=50)
    for i in range(10):
        words += _line_words(f"right line number {i}", x0=350, top=50 + i * 15)
    # The left "column" only has four words -- too few to trust as a
    # genuine second column rather than a stray heading or page number.
    assert _find_column_gap(words, PAGE_WIDTH) is None
