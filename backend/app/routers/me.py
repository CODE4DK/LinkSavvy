from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.jobs.queue import enqueue
from app.models.data_export import DataExport
from app.models.user import User
from app.privacy.export_job import EXPORT_JOB_TYPE
from app.schemas.auth import DeleteAccountRequest, MessageResponse
from app.schemas.privacy import ExportJobResponse
from app.schemas.user import MeResponse, UpdateProfileRequest, UserPublic
from app.security.crypto import decrypt_bytes
from app.security.passwords import verify_password
from app.services import sessions as session_service
from app.services.audit import record_audit_event
from app.services.feature_flags import resolve_flags_for_user

router = APIRouter(prefix="/api/v1", tags=["me"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MeResponse:
    flags = await resolve_flags_for_user(db, user_id=user.id)
    return MeResponse(user=UserPublic.from_model(user), feature_flags=flags)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.locale is not None:
        user.locale = payload.locale
    if payload.timezone is not None:
        user.timezone = payload.timezone
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="user.update_profile",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()
    return UserPublic.from_model(user)


@router.delete("/me", response_model=MessageResponse)
async def delete_me(
    payload: DeleteAccountRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    if user.password_hash is not None and (
        not payload.current_password
        or not verify_password(payload.current_password, user.password_hash)
    ):
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "Current password is incorrect")

    user.status = "deleted"
    user.deleted_at = datetime.now(UTC)
    await session_service.revoke_all_for_user(db, user_id=user.id)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="user.delete_account",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()

    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return MessageResponse(message="Account deleted.")


@router.post("/me/export", response_model=ExportJobResponse)
async def request_data_export(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ExportJobResponse:
    job = await enqueue(db, job_type=EXPORT_JOB_TYPE, payload={}, user_id=user.id)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="user.request_data_export",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()
    return ExportJobResponse(job_id=str(job.id))


@router.get("/me/export/{export_id}")
async def download_data_export(
    export_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    export = await db.get(DataExport, export_id)
    if export is None or export.user_id != user.id:
        raise ApiError(ErrorCode.NOT_FOUND, "no such export")
    if export.expires_at <= datetime.now(UTC):
        raise ApiError(ErrorCode.NOT_FOUND, "this export link has expired")

    zip_bytes = decrypt_bytes(export.encrypted_zip)
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=linksavvy-export.zip"},
    )
