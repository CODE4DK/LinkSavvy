from __future__ import annotations

import io

import pdfplumber
import pytest
from PIL import Image

from app.content.carousel_layout import TEMPLATES, LayoutTemplate, compute_slide_layout
from app.content.carousel_pdf import render_deck_pdf
from app.content.carousel_png import render_slide_png


@pytest.mark.parametrize("template", TEMPLATES)
def test_compute_slide_layout_for_every_template(template: LayoutTemplate) -> None:
    layout = compute_slide_layout(
        template, headline="Headline", body="Body text here.", slide_number=1, total=3
    )
    assert layout.headline == "Headline"
    assert layout.body == "Body text here."
    assert layout.footer == "1 / 3"


def test_render_slide_png_produces_a_valid_image() -> None:
    layout = compute_slide_layout(
        "clean", headline="A headline", body="Some body text.", slide_number=1, total=1
    )
    png_bytes = render_slide_png(layout)
    image = Image.open(io.BytesIO(png_bytes))
    assert image.size == (1080, 1350)


def test_render_deck_pdf_has_one_page_per_slide_with_selectable_text() -> None:
    layouts = [
        compute_slide_layout(
            "bold", headline=f"Slide {i}", body=f"Body {i}", slide_number=i, total=3
        )
        for i in range(1, 4)
    ]
    pdf_bytes = render_deck_pdf(layouts)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        assert len(pdf.pages) == 3
        text = pdf.pages[1].extract_text()
        assert "Slide 2" in text
        assert "Body 2" in text
