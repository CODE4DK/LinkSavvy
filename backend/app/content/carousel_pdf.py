"""Renders a full slide deck to a single PDF -- one page per slide, at
1080x1350 points (matching the PNG export's pixel dimensions 1:1, so
the two share carousel_layout.py's positions without any unit
conversion). reportlab draws real glyphs with `drawString`, so the
resulting text is selectable and copyable, unlike a PNG or a
rasterized PDF -- the requirement that ruled out a screenshot-based
approach (see docs/adr/0007).
"""

from __future__ import annotations

import io

from reportlab.pdfgen import canvas

from app.content.carousel_layout import SLIDE_HEIGHT, SLIDE_WIDTH, SlideLayout

_MARGIN = 90
_HEADLINE_SIZE = 44
_BODY_SIZE = 26
_FOOTER_SIZE = 16
_ACCENT_BAR_HEIGHT = 16
_HEADLINE_FONT = "Helvetica-Bold"
_BODY_FONT = "Helvetica"


def _wrap_text(
    pdf: canvas.Canvas, text: str, font: str, size: float, max_width: float
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if pdf.stringWidth(candidate, font, size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _draw_slide(pdf: canvas.Canvas, layout: SlideLayout) -> None:
    pdf.setFillColor(layout.background)
    pdf.rect(0, 0, SLIDE_WIDTH, SLIDE_HEIGHT, fill=1, stroke=0)

    # reportlab's origin is bottom-left; everything below is expressed
    # in "distance from the top" and converted at the point of drawing.
    top = _MARGIN
    if layout.accent_color and layout.template == "clean":
        pdf.setFillColor(layout.accent_color)
        pdf.rect(
            0, SLIDE_HEIGHT - _ACCENT_BAR_HEIGHT, SLIDE_WIDTH, _ACCENT_BAR_HEIGHT, fill=1, stroke=0
        )
        top += _ACCENT_BAR_HEIGHT
    elif layout.accent_color and layout.template == "minimal":
        pdf.setStrokeColor(layout.accent_color)
        pdf.setLineWidth(2)
        rule_y = SLIDE_HEIGHT - (top + 140)
        pdf.line(_MARGIN, rule_y, SLIDE_WIDTH - _MARGIN, rule_y)

    max_width = SLIDE_WIDTH - 2 * _MARGIN
    y = top

    pdf.setFillColor(layout.headline_color)
    for line in _wrap_text(pdf, layout.headline, _HEADLINE_FONT, _HEADLINE_SIZE, max_width):
        pdf.setFont(_HEADLINE_FONT, _HEADLINE_SIZE)
        pdf.drawString(_MARGIN, SLIDE_HEIGHT - y - _HEADLINE_SIZE, line)
        y += _HEADLINE_SIZE + 12

    y += 40
    pdf.setFillColor(layout.body_color)
    for line in _wrap_text(pdf, layout.body, _BODY_FONT, _BODY_SIZE, max_width):
        pdf.setFont(_BODY_FONT, _BODY_SIZE)
        pdf.drawString(_MARGIN, SLIDE_HEIGHT - y - _BODY_SIZE, line)
        y += _BODY_SIZE + 10

    pdf.setFillColor(layout.body_color)
    pdf.setFont(_BODY_FONT, _FOOTER_SIZE)
    pdf.drawString(_MARGIN, _MARGIN - _FOOTER_SIZE, layout.footer)


def render_deck_pdf(layouts: list[SlideLayout]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(SLIDE_WIDTH, SLIDE_HEIGHT))
    for layout in layouts:
        _draw_slide(pdf, layout)
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()
