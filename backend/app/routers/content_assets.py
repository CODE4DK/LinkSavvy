"""Direct asset creation and the Composer's "I posted this" record --
see app/content/asset_service.py. Distinct from
`POST /api/v1/tools/runs/{run_id}/save`, which saves a specific tool
run's output; these endpoints don't require one.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.asset_service import create_asset, mark_posted
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.content_assets import CreateAssetRequest, MarkPostedRequest
from app.schemas.tools import AssetResponse
from app.tools.presenters import to_asset_response

router = APIRouter(prefix="/api/v1/assets", tags=["content"])


@router.post("", response_model=AssetResponse)
async def create_asset_endpoint(
    payload: CreateAssetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    asset = await create_asset(
        db,
        user=user,
        type=payload.type,
        title=payload.title,
        body=payload.body,
        folder_id=payload.folder_id,
    )
    return to_asset_response(asset)


@router.post("/{asset_id}/mark-posted", response_model=AssetResponse)
async def mark_asset_posted(
    asset_id: uuid.UUID,
    payload: MarkPostedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    asset = await mark_posted(db, user=user, asset_id=asset_id, linkedin_url=payload.linkedin_url)
    return to_asset_response(asset)
