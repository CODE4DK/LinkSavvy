"""Direct asset creation for the Composer: a user can draft a post from
scratch, or start from a content tool's result, without every asset
having to trace back to a `ToolRun` the way Phase 5's "Save to
Workspace" did. `mark_posted` is the Composer's lightweight "I posted
this" -- it never posts anything itself (CLAUDE.md's hard compliance
rule), it only records that the person did, with the LinkedIn URL they
paste in as their own record.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.asset import Asset
from app.models.user import User
from app.tools.definition import AssetType


async def create_asset(
    db: AsyncSession,
    *,
    user: User,
    type: AssetType,
    title: str,
    body: str,
    body_format: str = "text",
    folder_id: uuid.UUID | None = None,
) -> Asset:
    asset = Asset(
        user_id=user.id,
        type=type.value,
        title=title,
        body=body,
        body_format=body_format,
        folder_id=folder_id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def _get_owned_asset(db: AsyncSession, *, asset_id: uuid.UUID, user: User) -> Asset:
    asset = await db.get(Asset, asset_id)
    if asset is None or asset.user_id != user.id or asset.deleted_at is not None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such asset")
    return asset


async def mark_posted(
    db: AsyncSession, *, user: User, asset_id: uuid.UUID, linkedin_url: str | None
) -> Asset:
    asset = await _get_owned_asset(db, asset_id=asset_id, user=user)
    asset.metadata_ = {
        **asset.metadata_,
        "posted": True,
        "posted_at": datetime.now(UTC).isoformat(),
        "linkedin_url": linkedin_url,
    }
    await db.commit()
    await db.refresh(asset)
    return asset
