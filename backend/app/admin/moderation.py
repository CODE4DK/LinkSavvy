"""The moderation queue: content the output policy blocked, or a user
reported, waiting for an admin to review and action."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.moderation_flag import ModerationFlag
from app.services.audit import record_audit_event

_EXCERPT_MAX_LENGTH = 500


async def flag_ai_policy_violation(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    target_type: str,
    target_id: str,
    reason: str,
    content: str,
) -> None:
    """Called from app/assistant/orchestrator.py the moment `check_output`
    catches a violation -- the flag lands in the queue even though the
    orchestrator already substituted a safe reply, so a pattern of
    attempted violations is visible to an admin even when no single one
    ever reached the user."""
    flag = ModerationFlag(
        user_id=user_id,
        source="ai_policy",
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        excerpt=content[:_EXCERPT_MAX_LENGTH],
    )
    db.add(flag)
    await db.flush()


async def report_content(
    db: AsyncSession,
    *,
    reporter_user_id: uuid.UUID,
    target_type: str,
    target_id: str,
    reason: str,
    excerpt: str,
) -> ModerationFlag:
    flag = ModerationFlag(
        user_id=reporter_user_id,
        source="user_report",
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        excerpt=excerpt[:_EXCERPT_MAX_LENGTH],
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return flag


async def list_flags(
    db: AsyncSession, *, status: str | None = None, limit: int = 50
) -> list[ModerationFlag]:
    query = select(ModerationFlag)
    if status:
        query = query.where(ModerationFlag.status == status)
    query = query.order_by(ModerationFlag.created_at.desc()).limit(limit)
    return list((await db.execute(query)).scalars().all())


async def review_flag(
    db: AsyncSession,
    *,
    admin_id: uuid.UUID,
    flag_id: uuid.UUID,
    status: str,
    note: str | None,
) -> ModerationFlag:
    flag = await db.get(ModerationFlag, flag_id)
    if flag is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such moderation flag")
    flag.status = status
    flag.reviewed_by = admin_id
    flag.reviewed_at = datetime.now(UTC)
    flag.review_note = note
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.moderation.review",
        target_type=flag.target_type,
        target_id=flag.target_id,
        metadata={"flag_id": str(flag.id), "status": status},
    )
    await db.commit()
    await db.refresh(flag)
    return flag


async def queue_depth(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(ModerationFlag).where(ModerationFlag.status == "pending")
    )
    return int(result.scalar_one())
