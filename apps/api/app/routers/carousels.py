"""The carousel builder: save/update a carousel's re-editable
structure, and export it as a PDF (one file, all slides, selectable
text) or a ZIP of per-slide PNGs. See app/content/carousel_service.py.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.carousel_service import (
    create_carousel,
    export_carousel_pdf,
    export_carousel_png_zip,
    get_owned_carousel,
    parse_carousel_data,
    update_carousel,
)
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.carousels import CarouselData, CarouselResponse, SaveCarouselRequest

router = APIRouter(prefix="/api/v1/carousels", tags=["content"])


def _to_response(asset_id: uuid.UUID, title: str, data_json: str) -> CarouselResponse:
    return CarouselResponse(
        id=str(asset_id), title=title, data=CarouselData.model_validate_json(data_json)
    )


@router.post("", response_model=CarouselResponse)
async def create_carousel_endpoint(
    payload: SaveCarouselRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarouselResponse:
    asset = await create_carousel(db, user=user, title=payload.title, data=payload.data)
    return _to_response(asset.id, asset.title, asset.body)


@router.get("/{asset_id}", response_model=CarouselResponse)
async def get_carousel_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarouselResponse:
    asset = await get_owned_carousel(db, user=user, asset_id=asset_id)
    return _to_response(asset.id, asset.title, asset.body)


@router.put("/{asset_id}", response_model=CarouselResponse)
async def update_carousel_endpoint(
    asset_id: uuid.UUID,
    payload: SaveCarouselRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarouselResponse:
    asset = await update_carousel(
        db, user=user, asset_id=asset_id, title=payload.title, data=payload.data
    )
    return _to_response(asset.id, asset.title, asset.body)


@router.post("/{asset_id}/export/pdf")
async def export_carousel_pdf_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    asset = await get_owned_carousel(db, user=user, asset_id=asset_id)
    pdf_bytes = export_carousel_pdf(parse_carousel_data(asset))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{asset.title}.pdf"'},
    )


@router.post("/{asset_id}/export/png")
async def export_carousel_png_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    asset = await get_owned_carousel(db, user=user, asset_id=asset_id)
    zip_bytes = export_carousel_png_zip(parse_carousel_data(asset))
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{asset.title}-slides.zip"'},
    )
