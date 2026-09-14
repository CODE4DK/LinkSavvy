"""Refresh-token session lifecycle: issue, rotate, detect reuse, revoke."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.refresh_token import RefreshToken
from app.security.tokens import generate_raw_token, hash_token
from app.settings import settings


async def issue_refresh_token(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    user_agent: str | None,
    ip_hash: str | None,
    family_id: uuid.UUID | None = None,
) -> tuple[str, RefreshToken]:
    raw_token = generate_raw_token()
    now = datetime.now(UTC)
    row = RefreshToken(
        user_id=user_id,
        family_id=family_id or uuid.uuid4(),
        token_hash=hash_token(raw_token),
        issued_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
        user_agent=user_agent,
        ip_hash=ip_hash,
    )
    db.add(row)
    await db.flush()
    return raw_token, row


async def rotate_refresh_token(
    db: AsyncSession,
    *,
    raw_token: str,
    user_agent: str | None,
    ip_hash: str | None,
) -> tuple[str, RefreshToken]:
    token_hash = hash_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    existing = result.scalar_one_or_none()
    if existing is None:
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "Unknown refresh token")

    now = datetime.now(UTC)

    if existing.revoked_at is not None:
        # This exact token was already rotated away (or explicitly revoked)
        # and is being presented again — treat as theft and burn the family.
        await revoke_family(db, family_id=existing.family_id)
        raise ApiError(
            ErrorCode.TOKEN_REUSED,
            "Refresh token reuse detected; all sessions in this family were revoked",
        )

    if existing.expires_at < now:
        raise ApiError(ErrorCode.TOKEN_EXPIRED, "Refresh token has expired")

    new_raw, new_row = await issue_refresh_token(
        db,
        user_id=existing.user_id,
        user_agent=user_agent,
        ip_hash=ip_hash,
        family_id=existing.family_id,
    )
    existing.revoked_at = now
    existing.replaced_by = new_row.id
    await db.flush()
    return new_raw, new_row


async def revoke_family(db: AsyncSession, *, family_id: uuid.UUID) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None)
        )
    )
    now = datetime.now(UTC)
    for row in result.scalars().all():
        row.revoked_at = now
    await db.flush()


async def revoke_token_by_hash(db: AsyncSession, *, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    row = result.scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        await db.flush()


async def revoke_all_for_user(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    )
    now = datetime.now(UTC)
    for row in result.scalars().all():
        row.revoked_at = now
    await db.flush()


async def list_active_sessions(db: AsyncSession, *, user_id: uuid.UUID) -> list[RefreshToken]:
    now = datetime.now(UTC)
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.issued_at.desc())
    )
    return list(result.scalars().all())


async def revoke_session(db: AsyncSession, *, user_id: uuid.UUID, session_id: uuid.UUID) -> bool:
    row = await db.get(RefreshToken, session_id)
    if row is None or row.user_id != user_id or row.revoked_at is not None:
        return False
    row.revoked_at = datetime.now(UTC)
    await db.flush()
    return True
