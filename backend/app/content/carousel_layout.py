"""Pure layout data for a carousel slide -- shared by the PDF exporter
(reportlab) and the PNG exporter (Pillow) so the two outputs can never
visually drift apart: both draw exactly the same computed colours and
text, just through different drawing APIs.

Canvas size is fixed at 1080x1350 (a 4:5 ratio), LinkedIn's own
recommended size for a document-post carousel.

Colours are the app's real design tokens (frontend/src/styles/tokens.css,
light theme), converted from HSL to hex by hand since Python has no way
to read a CSS custom property -- if tokens.css's palette changes, these
need updating to match, the same kind of drift risk as the LinkedIn
preview's fold constant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

# From frontend/src/styles/tokens.css (:root, light theme).
COLOR_BG = "#FFFFFF"
COLOR_FG = "#0F1729"
COLOR_FG_MUTED = "#566376"
COLOR_PRIMARY = "#0A5ADB"
COLOR_PRIMARY_FOREGROUND = "#FFFFFF"
COLOR_ACCENT = "#7C3BED"
COLOR_BORDER = "#DCDFE4"

LayoutTemplate = Literal["clean", "bold", "minimal"]
TEMPLATES: tuple[LayoutTemplate, ...] = ("clean", "bold", "minimal")


@dataclass(frozen=True, slots=True)
class SlideLayout:
    template: LayoutTemplate
    background: str
    headline_color: str
    body_color: str
    accent_color: str | None
    headline: str
    body: str
    footer: str


def compute_slide_layout(
    template: LayoutTemplate, *, headline: str, body: str, slide_number: int, total: int
) -> SlideLayout:
    footer = f"{slide_number} / {total}"
    if template == "bold":
        return SlideLayout(
            template=template,
            background=COLOR_PRIMARY,
            headline_color=COLOR_PRIMARY_FOREGROUND,
            body_color=COLOR_PRIMARY_FOREGROUND,
            accent_color=None,
            headline=headline,
            body=body,
            footer=footer,
        )
    if template == "minimal":
        return SlideLayout(
            template=template,
            background=COLOR_BG,
            headline_color=COLOR_FG,
            body_color=COLOR_FG_MUTED,
            accent_color=COLOR_BORDER,
            headline=headline,
            body=body,
            footer=footer,
        )
    # "clean" (the default): white background, a primary-coloured accent
    # bar, dark headline.
    return SlideLayout(
        template="clean",
        background=COLOR_BG,
        headline_color=COLOR_FG,
        body_color=COLOR_FG_MUTED,
        accent_color=COLOR_ACCENT,
        headline=headline,
        body=body,
        footer=footer,
    )
