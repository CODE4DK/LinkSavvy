"""The Workspace Hub's asset management: list/search/filter with cursor
pagination, patch (rename/retag/move/favourite/edit-in-place with
versioning), a 30-day trash, duplicate, and bulk operations. Builds on
the Phase 5 `Asset`/`AssetFolder` models -- no schema change beyond the
one genuinely new table, `asset_versions` (migration 0015); everything
else here is query and service logic against columns that already
exist.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.asset import Asset
from app.models.asset_version import AssetVersion
from app.models.tool_run import ToolRun
from app.models.user import User
from app.workspace.cursor import decode_cursor, encode_before_id, encode_offset
from app.workspace.search import apply_search

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
TRASH_RETENTION_DAYS = 30

UNSET: Any = object()


@dataclass(frozen=True, slots=True)
class AssetPage:
    items: list[Asset]
    next_cursor: str | None


async def list_assets(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    type: str | None = None,
    folder_id: uuid.UUID | None = None,
    tags: list[str] | None = None,
    favourite: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    source_tool_id: str | None = None,
    q: str | None = None,
    cursor: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> AssetPage:
    limit = min(limit, MAX_LIMIT)
    stmt = select(Asset).where(Asset.user_id == user_id, Asset.deleted_at.is_(None))

    if type is not None:
        stmt = stmt.where(Asset.type == type)
    if folder_id is not None:
        stmt = stmt.where(Asset.folder_id == folder_id)
    if favourite is not None:
        stmt = stmt.where(Asset.is_favourite == favourite)
    if date_from is not None:
        stmt = stmt.where(Asset.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Asset.created_at <= date_to)
    if source_tool_id is not None:
        stmt = stmt.where(
            Asset.source_tool_run_id.in_(
                select(ToolRun.id).where(ToolRun.tool_id == source_tool_id)
            )
        )
    if tags:
        # A JSON column has no portable "array contains" operator across
        # MySQL and SQLite -- filtered in Python below instead, after a
        # single page is fetched. Fine at Workspace's scale (a page is at
        # most MAX_LIMIT rows); see docs/adr/0009.
        pass

    offset = 0
    if q:
        if cursor:
            offset = decode_cursor(cursor).get("offset", 0)
        stmt = apply_search(stmt, db=db, q=q)
        stmt = stmt.offset(offset).limit(limit + 1)
    else:
        if cursor:
            before_id = decode_cursor(cursor).get("before_id")
            if before_id:
                stmt = stmt.where(Asset.id < uuid.UUID(before_id))
        # Ordered (and paginated) by `id`, not `created_at` -- a UUIDv7
        # is itself monotonically time-ordered, already unique, and
        # free of the datetime-format mismatch explained in
        # app.workspace.cursor.encode_before_id.
        stmt = stmt.order_by(Asset.id.desc()).limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    if tags:
        wanted = set(tags)
        rows = [row for row in rows if wanted.issubset(set(row.tags))]

    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor: str | None = None
    if has_more:
        if q:
            next_cursor = encode_offset(offset + limit)
        elif items:
            next_cursor = encode_before_id(items[-1].id)

    return AssetPage(items=items, next_cursor=next_cursor)


async def get_owned_asset(
    db: AsyncSession, *, user_id: uuid.UUID, asset_id: uuid.UUID, include_deleted: bool = False
) -> Asset:
    asset = await db.get(Asset, asset_id)
    if asset is None or asset.user_id != user_id:
        raise ApiError(ErrorCode.NOT_FOUND, "no such asset")
    if asset.deleted_at is not None and not include_deleted:
        raise ApiError(ErrorCode.NOT_FOUND, "no such asset")
    return asset


async def _next_version_number(db: AsyncSession, *, asset_id: uuid.UUID) -> int:
    result = await db.execute(
        select(AssetVersion.version)
        .where(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    return (latest or 0) + 1


async def patch_asset(
    db: AsyncSession,
    *,
    user: User,
    asset_id: uuid.UUID,
    title: str | None = None,
    body: str | None = None,
    tags: list[str] | None = None,
    folder_id: uuid.UUID | None = UNSET,
    is_favourite: bool | None = None,
) -> Asset:
    """`folder_id` left unset means "don't touch"; `folder_id=None`
    explicitly unfiles the asset -- the two need to be distinguishable
    since None is also a valid target value, hence the `UNSET` sentinel
    default rather than `None` itself."""
    asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id)
    if asset.read_only:
        raise ApiError(
            ErrorCode.FORBIDDEN,
            "This asset is read-only because it's beyond your plan's saved-item limit. "
            "Upgrade to pro to edit it again.",
            details={"upgrade_required": True},
        )

    edits_content = title is not None or body is not None
    if edits_content:
        db.add(
            AssetVersion(
                asset_id=asset.id,
                version=await _next_version_number(db, asset_id=asset.id),
                title=asset.title,
                body=asset.body,
                body_format=asset.body_format,
                metadata_=asset.metadata_,
            )
        )

    if title is not None:
        asset.title = title
    if body is not None:
        asset.body = body
    if tags is not None:
        asset.tags = tags
    if folder_id is not UNSET:
        asset.folder_id = folder_id
    if is_favourite is not None:
        asset.is_favourite = is_favourite

    await db.commit()
    await db.refresh(asset)
    return asset


async def list_versions(db: AsyncSession, *, user: User, asset_id: uuid.UUID) -> list[AssetVersion]:
    await get_owned_asset(db, user_id=user.id, asset_id=asset_id, include_deleted=True)
    result = await db.execute(
        select(AssetVersion)
        .where(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version.desc())
    )
    return list(result.scalars().all())


async def soft_delete_asset(db: AsyncSession, *, user: User, asset_id: uuid.UUID) -> Asset:
    asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id)
    asset.deleted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(asset)
    return asset


async def restore_asset(db: AsyncSession, *, user: User, asset_id: uuid.UUID) -> Asset:
    asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id, include_deleted=True)
    if asset.deleted_at is None:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "asset is not in the trash")
    asset.deleted_at = None
    await db.commit()
    await db.refresh(asset)
    return asset


async def permanently_delete_asset(db: AsyncSession, *, user: User, asset_id: uuid.UUID) -> None:
    asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id, include_deleted=True)
    await db.delete(asset)
    await db.commit()


async def list_trash(db: AsyncSession, *, user_id: uuid.UUID) -> list[Asset]:
    cutoff = datetime.now(UTC) - timedelta(days=TRASH_RETENTION_DAYS)
    result = await db.execute(
        select(Asset)
        .where(
            Asset.user_id == user_id,
            Asset.deleted_at.is_not(None),
            Asset.deleted_at >= cutoff,
        )
        .order_by(Asset.deleted_at.desc())
    )
    return list(result.scalars().all())


async def purge_expired_trash(db: AsyncSession) -> int:
    """Hard-deletes anything that has sat in the trash past its 30-day
    retention window. Not currently wired to a scheduler (see
    docs/adr/0009) -- callable directly, or from an ops script/cron."""
    cutoff = datetime.now(UTC) - timedelta(days=TRASH_RETENTION_DAYS)
    result = await db.execute(
        select(Asset).where(Asset.deleted_at.is_not(None), Asset.deleted_at < cutoff)
    )
    expired = list(result.scalars().all())
    for asset in expired:
        await db.delete(asset)
    await db.commit()
    return len(expired)


async def duplicate_asset(db: AsyncSession, *, user: User, asset_id: uuid.UUID) -> Asset:
    original = await get_owned_asset(db, user_id=user.id, asset_id=asset_id)
    copy = Asset(
        user_id=user.id,
        type=original.type,
        title=f"{original.title} (copy)",
        body=original.body,
        body_format=original.body_format,
        metadata_=dict(original.metadata_),
        source_tool_run_id=original.source_tool_run_id,
        tags=list(original.tags),
        is_favourite=False,
        folder_id=original.folder_id,
    )
    db.add(copy)
    await db.commit()
    await db.refresh(copy)
    return copy


async def bulk_move(
    db: AsyncSession, *, user: User, asset_ids: list[uuid.UUID], folder_id: uuid.UUID | None
) -> int:
    count = 0
    for asset_id in asset_ids:
        asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id)
        asset.folder_id = folder_id
        count += 1
    await db.commit()
    return count


async def bulk_tag(
    db: AsyncSession, *, user: User, asset_ids: list[uuid.UUID], tags: list[str]
) -> int:
    count = 0
    for asset_id in asset_ids:
        asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id)
        asset.tags = sorted(set(asset.tags) | set(tags))
        count += 1
    await db.commit()
    return count


async def bulk_delete(db: AsyncSession, *, user: User, asset_ids: list[uuid.UUID]) -> int:
    count = 0
    now = datetime.now(UTC)
    for asset_id in asset_ids:
        asset = await get_owned_asset(db, user_id=user.id, asset_id=asset_id)
        asset.deleted_at = now
        count += 1
    await db.commit()
    return count


async def get_assets_for_export(
    db: AsyncSession, *, user: User, asset_ids: list[uuid.UUID]
) -> list[Asset]:
    return [await get_owned_asset(db, user_id=user.id, asset_id=asset_id) for asset_id in asset_ids]
