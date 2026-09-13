"""The Workspace Hub's asset management surface: list/search/filter,
patch, trash/restore, duplicate, bulk operations, version history, and
export. See app/workspace/{assets,folders,export}.py for the domain
logic. Mounted at the same `/api/v1/assets` prefix as
app.routers.content_assets (Phase 6's direct-create + mark-posted
endpoints) -- no path collides.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.asset import Asset, AssetFolder
from app.models.asset_version import AssetVersion
from app.models.user import User
from app.schemas.workspace import (
    AssetFolderCreateRequest,
    AssetFolderResponse,
    AssetFolderUpdateRequest,
    AssetListResponse,
    AssetPatchRequest,
    AssetVersionResponse,
    BulkActionRequest,
    BulkActionResponse,
    WorkspaceAssetResponse,
)
from app.workspace import assets as assets_service
from app.workspace import export as export_service
from app.workspace import folders as folders_service

router = APIRouter(prefix="/api/v1/assets", tags=["workspace"])
folders_router = APIRouter(prefix="/api/v1/asset-folders", tags=["workspace"])

_EXPORT_MEDIA_TYPES = {
    "txt": "text/plain",
    "md": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _to_response(asset: Asset) -> WorkspaceAssetResponse:
    return WorkspaceAssetResponse(
        id=str(asset.id),
        type=asset.type,
        title=asset.title,
        body=asset.body,
        body_format=asset.body_format,
        metadata=asset.metadata_,
        source_tool_run_id=str(asset.source_tool_run_id) if asset.source_tool_run_id else None,
        tags=asset.tags,
        is_favourite=asset.is_favourite,
        folder_id=str(asset.folder_id) if asset.folder_id else None,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        deleted_at=asset.deleted_at,
    )


def _version_to_response(version: AssetVersion) -> AssetVersionResponse:
    return AssetVersionResponse(
        version=version.version,
        title=version.title,
        body=version.body,
        body_format=version.body_format,
        created_at=version.created_at,
    )


def _folder_to_response(folder: AssetFolder) -> AssetFolderResponse:
    return AssetFolderResponse(
        id=str(folder.id),
        name=folder.name,
        parent_id=str(folder.parent_id) if folder.parent_id else None,
    )


@router.get("", response_model=AssetListResponse)
async def list_assets_endpoint(
    type: str | None = Query(default=None),
    folder_id: uuid.UUID | None = Query(default=None),
    tags: list[str] | None = Query(default=None),
    favourite: bool | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    source_tool_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=assets_service.DEFAULT_LIMIT, ge=1, le=assets_service.MAX_LIMIT),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetListResponse:
    page = await assets_service.list_assets(
        db,
        user_id=user.id,
        type=type,
        folder_id=folder_id,
        tags=tags,
        favourite=favourite,
        date_from=datetime.combine(date_from, time.min) if date_from else None,
        date_to=datetime.combine(date_to, time.max) if date_to else None,
        source_tool_id=source_tool_id,
        q=q,
        cursor=cursor,
        limit=limit,
    )
    return AssetListResponse(
        items=[_to_response(a) for a in page.items], next_cursor=page.next_cursor
    )


@router.get("/trash", response_model=list[WorkspaceAssetResponse])
async def list_trash_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceAssetResponse]:
    trashed = await assets_service.list_trash(db, user_id=user.id)
    return [_to_response(a) for a in trashed]


@router.get("/{asset_id}", response_model=WorkspaceAssetResponse)
async def get_asset_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceAssetResponse:
    asset = await assets_service.get_owned_asset(db, user_id=user.id, asset_id=asset_id)
    return _to_response(asset)


@router.patch("/{asset_id}", response_model=WorkspaceAssetResponse)
async def patch_asset_endpoint(
    asset_id: uuid.UUID,
    payload: AssetPatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceAssetResponse:
    folder_id: uuid.UUID | None
    if payload.unfile:
        folder_id = None
    elif payload.folder_id is not None:
        folder_id = uuid.UUID(payload.folder_id)
    else:
        folder_id = assets_service.UNSET

    asset = await assets_service.patch_asset(
        db,
        user=user,
        asset_id=asset_id,
        title=payload.title,
        body=payload.body,
        tags=payload.tags,
        folder_id=folder_id,
        is_favourite=payload.is_favourite,
    )
    return _to_response(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset_endpoint(
    asset_id: uuid.UUID,
    permanent: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if permanent:
        await assets_service.permanently_delete_asset(db, user=user, asset_id=asset_id)
    else:
        await assets_service.soft_delete_asset(db, user=user, asset_id=asset_id)


@router.post("/{asset_id}/restore", response_model=WorkspaceAssetResponse)
async def restore_asset_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceAssetResponse:
    asset = await assets_service.restore_asset(db, user=user, asset_id=asset_id)
    return _to_response(asset)


@router.post("/{asset_id}/duplicate", response_model=WorkspaceAssetResponse)
async def duplicate_asset_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceAssetResponse:
    copy = await assets_service.duplicate_asset(db, user=user, asset_id=asset_id)
    return _to_response(copy)


@router.get("/{asset_id}/versions", response_model=list[AssetVersionResponse])
async def list_versions_endpoint(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AssetVersionResponse]:
    versions = await assets_service.list_versions(db, user=user, asset_id=asset_id)
    return [_version_to_response(v) for v in versions]


@router.get("/{asset_id}/export")
async def export_asset_endpoint(
    asset_id: uuid.UUID,
    format: str = Query(default="txt", pattern="^(txt|md|pdf|docx)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    asset = await assets_service.get_owned_asset(db, user_id=user.id, asset_id=asset_id)
    content = export_service.export_asset(asset, fmt=format)
    return Response(
        content=content,
        media_type=_EXPORT_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{asset.title}.{format}"'},
    )


@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_action_endpoint(
    payload: BulkActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BulkActionResponse | Response:
    asset_ids = [uuid.UUID(a) for a in payload.asset_ids]

    if payload.action == "move":
        folder_id = uuid.UUID(payload.folder_id) if payload.folder_id else None
        count = await assets_service.bulk_move(
            db, user=user, asset_ids=asset_ids, folder_id=folder_id
        )
        return BulkActionResponse(affected_count=count)

    if payload.action == "tag":
        if not payload.tags:
            raise ApiError(ErrorCode.VALIDATION_FAILED, "tags are required for a tag action")
        count = await assets_service.bulk_tag(db, user=user, asset_ids=asset_ids, tags=payload.tags)
        return BulkActionResponse(affected_count=count)

    if payload.action == "delete":
        count = await assets_service.bulk_delete(db, user=user, asset_ids=asset_ids)
        return BulkActionResponse(affected_count=count)

    # export
    selected = await assets_service.get_assets_for_export(db, user=user, asset_ids=asset_ids)
    zip_bytes = export_service.export_assets_zip(selected, fmt=payload.format)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="workspace-export.zip"'},
    )


@folders_router.get("", response_model=list[AssetFolderResponse])
async def list_folders_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AssetFolderResponse]:
    folders = await folders_service.list_folders(db, user_id=user.id)
    return [_folder_to_response(f) for f in folders]


@folders_router.post("", response_model=AssetFolderResponse)
async def create_folder_endpoint(
    payload: AssetFolderCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetFolderResponse:
    parent_id = uuid.UUID(payload.parent_id) if payload.parent_id else None
    folder = await folders_service.create_folder(
        db, user=user, name=payload.name, parent_id=parent_id
    )
    return _folder_to_response(folder)


@folders_router.patch("/{folder_id}", response_model=AssetFolderResponse)
async def update_folder_endpoint(
    folder_id: uuid.UUID,
    payload: AssetFolderUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetFolderResponse:
    folder = None
    if payload.name is not None:
        folder = await folders_service.rename_folder(
            db, user=user, folder_id=folder_id, name=payload.name
        )
    if payload.unfile:
        folder = await folders_service.move_folder(
            db, user=user, folder_id=folder_id, parent_id=None
        )
    elif payload.parent_id is not None:
        folder = await folders_service.move_folder(
            db, user=user, folder_id=folder_id, parent_id=uuid.UUID(payload.parent_id)
        )
    if folder is None:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "no changes given")
    return _folder_to_response(folder)


@folders_router.delete("/{folder_id}", status_code=204)
async def delete_folder_endpoint(
    folder_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await folders_service.delete_folder(db, user=user, folder_id=folder_id)
