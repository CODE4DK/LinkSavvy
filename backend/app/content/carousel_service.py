"""Carousel builder: a carousel is stored as a regular `Asset` (type
`carousel`, `body_format` `json`) so it can be re-opened and edited
slide by slide -- the export functions below turn that same structure
into the PDF or PNGs someone actually uploads to LinkedIn as a
document post.
"""

from __future__ import annotations

import io
import uuid
import zipfile

from sqlalchemy.ext.asyncio import AsyncSession

from app.content.carousel_layout import SlideLayout, compute_slide_layout
from app.content.carousel_pdf import render_deck_pdf
from app.content.carousel_png import render_slide_png
from app.errors import ApiError, ErrorCode
from app.models.asset import Asset
from app.models.user import User
from app.schemas.carousels import CarouselData
from app.tools.definition import AssetType


async def create_carousel(db: AsyncSession, *, user: User, title: str, data: CarouselData) -> Asset:
    asset = Asset(
        user_id=user.id,
        type=AssetType.CAROUSEL.value,
        title=title,
        body=data.model_dump_json(),
        body_format="json",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def get_owned_carousel(db: AsyncSession, *, user: User, asset_id: uuid.UUID) -> Asset:
    asset = await db.get(Asset, asset_id)
    if (
        asset is None
        or asset.user_id != user.id
        or asset.deleted_at is not None
        or asset.type != AssetType.CAROUSEL.value
    ):
        raise ApiError(ErrorCode.NOT_FOUND, "no such carousel")
    return asset


async def update_carousel(
    db: AsyncSession, *, user: User, asset_id: uuid.UUID, title: str, data: CarouselData
) -> Asset:
    asset = await get_owned_carousel(db, user=user, asset_id=asset_id)
    asset.title = title
    asset.body = data.model_dump_json()
    await db.commit()
    await db.refresh(asset)
    return asset


def parse_carousel_data(asset: Asset) -> CarouselData:
    return CarouselData.model_validate_json(asset.body)


def _layouts_for(data: CarouselData) -> list[SlideLayout]:
    total = len(data.slides)
    return [
        compute_slide_layout(
            data.template,
            headline=slide.headline,
            body=slide.body,
            slide_number=index,
            total=total,
        )
        for index, slide in enumerate(data.slides, start=1)
    ]


def export_carousel_pdf(data: CarouselData) -> bytes:
    return render_deck_pdf(_layouts_for(data))


def export_carousel_png_zip(data: CarouselData) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, layout in enumerate(_layouts_for(data), start=1):
            archive.writestr(f"slide-{index}.png", render_slide_png(layout))
    return buffer.getvalue()
