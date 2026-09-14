from __future__ import annotations

import io
import uuid
import zipfile

import pdfplumber
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.carousel_service import (
    create_carousel,
    export_carousel_pdf,
    export_carousel_png_zip,
    get_owned_carousel,
    parse_carousel_data,
    update_carousel,
)
from app.errors import ApiError
from app.models.user import User
from app.schemas.carousels import CarouselClosing, CarouselCover, CarouselData, CarouselSlide


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"carousel-{uuid.uuid4()}@example.com", full_name="Carousel Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _sample_data(template: str = "clean") -> CarouselData:
    return CarouselData(
        template=template,  # type: ignore[arg-type]
        cover=CarouselCover(headline="Cover headline", subhead="Cover subhead"),
        slides=[
            CarouselSlide(headline="Slide one", body="Body one", visual_note="note one"),
            CarouselSlide(headline="Slide two", body="Body two", visual_note="note two"),
        ],
        closing=CarouselClosing(cta="Closing CTA"),
        caption="A caption",
    )


async def test_create_carousel_persists_structure(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await create_carousel(db_session, user=user, title="My carousel", data=_sample_data())
    assert asset.type == "carousel"
    assert asset.body_format == "json"

    parsed = parse_carousel_data(asset)
    assert len(parsed.slides) == 2
    assert parsed.cover.headline == "Cover headline"


async def test_update_carousel_replaces_structure(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await create_carousel(db_session, user=user, title="Draft", data=_sample_data())

    updated_data = _sample_data()
    updated_data.slides.append(
        CarouselSlide(headline="Slide three", body="Body three", visual_note="")
    )
    updated = await update_carousel(
        db_session, user=user, asset_id=asset.id, title="Final title", data=updated_data
    )
    assert updated.title == "Final title"
    assert len(parse_carousel_data(updated).slides) == 3


async def test_get_owned_carousel_rejects_another_users_asset(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    asset = await create_carousel(db_session, user=owner, title="Draft", data=_sample_data())
    with pytest.raises(ApiError):
        await get_owned_carousel(db_session, user=other, asset_id=asset.id)


def test_export_carousel_pdf_has_one_page_per_slide() -> None:
    pdf_bytes = export_carousel_pdf(_sample_data())
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        assert len(pdf.pages) == 2


def test_export_carousel_png_zip_has_one_entry_per_slide() -> None:
    zip_bytes = export_carousel_png_zip(_sample_data())
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        assert archive.namelist() == ["slide-1.png", "slide-2.png"]
