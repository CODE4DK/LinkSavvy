"""Renders one slide's `SlideLayout` to a PNG, using only Pillow's own
bundled scalable default font -- no external font file to bundle or go
missing. See carousel_layout.py for the shared layout data this reads.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

from app.content.carousel_layout import SLIDE_HEIGHT, SLIDE_WIDTH, SlideLayout

_MARGIN = 90
_HEADLINE_SIZE = 64
_BODY_SIZE = 40
_FOOTER_SIZE = 28
_ACCENT_BAR_HEIGHT = 16


def _wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.BaseImageFont, max_width: int
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
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def render_slide_png(layout: SlideLayout) -> bytes:
    image = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), layout.background)
    draw = ImageDraw.Draw(image)

    top = _MARGIN
    if layout.accent_color and layout.template == "clean":
        draw.rectangle([(0, 0), (SLIDE_WIDTH, _ACCENT_BAR_HEIGHT)], fill=layout.accent_color)
        top += _ACCENT_BAR_HEIGHT
    elif layout.accent_color and layout.template == "minimal":
        draw.line(
            [(_MARGIN, top + 140), (SLIDE_WIDTH - _MARGIN, top + 140)],
            fill=layout.accent_color,
            width=3,
        )

    headline_font = ImageFont.load_default(size=_HEADLINE_SIZE)
    body_font = ImageFont.load_default(size=_BODY_SIZE)
    footer_font = ImageFont.load_default(size=_FOOTER_SIZE)

    max_width = SLIDE_WIDTH - 2 * _MARGIN
    y = top

    for line in _wrap_text(draw, layout.headline, headline_font, max_width):
        draw.text((_MARGIN, y), line, font=headline_font, fill=layout.headline_color)
        y += _HEADLINE_SIZE + 12

    y += 40
    for line in _wrap_text(draw, layout.body, body_font, max_width):
        draw.text((_MARGIN, y), line, font=body_font, fill=layout.body_color)
        y += _BODY_SIZE + 10

    draw.text(
        (_MARGIN, SLIDE_HEIGHT - _MARGIN),
        layout.footer,
        font=footer_font,
        fill=layout.body_color,
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
