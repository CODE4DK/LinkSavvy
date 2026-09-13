"""User-created folders for the Workspace Hub's left rail. Nesting is
`AssetFolder.parent_id` (already on the model since Phase 5) -- this
module is the CRUD the model never got a router for.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.asset import Asset, AssetFolder
from app.models.user import User


async def list_folders(db: AsyncSession, *, user_id: uuid.UUID) -> list[AssetFolder]:
    result = await db.execute(
        select(AssetFolder).where(AssetFolder.user_id == user_id).order_by(AssetFolder.name.asc())
    )
    return list(result.scalars().all())


async def _get_owned_folder(
    db: AsyncSession, *, user_id: uuid.UUID, folder_id: uuid.UUID
) -> AssetFolder:
    folder = await db.get(AssetFolder, folder_id)
    if folder is None or folder.user_id != user_id:
        raise ApiError(ErrorCode.NOT_FOUND, "no such folder")
    return folder


async def create_folder(
    db: AsyncSession, *, user: User, name: str, parent_id: uuid.UUID | None
) -> AssetFolder:
    if parent_id is not None:
        await _get_owned_folder(db, user_id=user.id, folder_id=parent_id)
    folder = AssetFolder(user_id=user.id, name=name, parent_id=parent_id)
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


async def rename_folder(
    db: AsyncSession, *, user: User, folder_id: uuid.UUID, name: str
) -> AssetFolder:
    folder = await _get_owned_folder(db, user_id=user.id, folder_id=folder_id)
    folder.name = name
    await db.commit()
    await db.refresh(folder)
    return folder


async def move_folder(
    db: AsyncSession, *, user: User, folder_id: uuid.UUID, parent_id: uuid.UUID | None
) -> AssetFolder:
    folder = await _get_owned_folder(db, user_id=user.id, folder_id=folder_id)
    if parent_id is not None:
        if parent_id == folder_id:
            raise ApiError(ErrorCode.VALIDATION_FAILED, "a folder cannot be its own parent")
        await _get_owned_folder(db, user_id=user.id, folder_id=parent_id)
    folder.parent_id = parent_id
    await db.commit()
    await db.refresh(folder)
    return folder


async def delete_folder(db: AsyncSession, *, user: User, folder_id: uuid.UUID) -> None:
    """Deletes the folder itself. Assets inside it, and any subfolders,
    are not deleted -- they're explicitly unfiled/reparented to NULL
    here in application code rather than left to the FKs' own
    `ondelete=SET NULL`, since that only fires when the database itself
    enforces foreign keys (SQLite, used by the test suite, does not
    unless a session explicitly turns the pragma on) -- see docs/adr/0009."""
    folder = await _get_owned_folder(db, user_id=user.id, folder_id=folder_id)

    asset_result = await db.execute(select(Asset).where(Asset.folder_id == folder_id))
    for asset in asset_result.scalars().all():
        asset.folder_id = None

    child_result = await db.execute(select(AssetFolder).where(AssetFolder.parent_id == folder_id))
    for child in child_result.scalars().all():
        child.parent_id = None

    await db.delete(folder)
    await db.commit()


async def count_assets_in_folder(
    db: AsyncSession, *, user_id: uuid.UUID, folder_id: uuid.UUID
) -> int:
    result = await db.execute(
        select(Asset.id).where(
            Asset.user_id == user_id, Asset.folder_id == folder_id, Asset.deleted_at.is_(None)
        )
    )
    return len(result.all())
