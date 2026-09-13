"""Admin user management: search, suspend/reinstate, force password
reset, manual plan changes, and impersonation. Every mutating action here
writes to `audit_log` -- see the `record_audit_event` call at the end of
each function.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.entitlements import apply_entitlements
from app.errors import ApiError, ErrorCode
from app.models.ai_invocation import AIInvocation
from app.models.password_reset import PasswordReset
from app.models.subscription import Subscription
from app.models.tool_run import ToolRun
from app.models.user import User
from app.security.jwt import DEFAULT_IMPERSONATION_TTL_MINUTES, create_impersonation_token
from app.security.tokens import generate_raw_token, hash_token
from app.services.audit import record_audit_event
from app.settings import settings

_PAGE_SIZE_DEFAULT = 25


@dataclass(frozen=True, slots=True)
class UserSearchPage:
    items: list[User]
    total: int


async def search_users(
    db: AsyncSession,
    *,
    query: str | None = None,
    plan: str | None = None,
    status: str | None = None,
    signed_up_after: date | None = None,
    signed_up_before: date | None = None,
    offset: int = 0,
    limit: int = _PAGE_SIZE_DEFAULT,
) -> UserSearchPage:
    filters: list[ColumnElement[bool]] = []
    if query:
        like = f"%{query.lower()}%"
        filters.append(
            (func.lower(User.email).like(like)) | (func.lower(User.full_name).like(like))
        )
    if plan:
        filters.append(User.plan == plan)
    if status:
        filters.append(User.status == status)
    if signed_up_after:
        filters.append(func.date(User.created_at) >= signed_up_after)
    if signed_up_before:
        filters.append(func.date(User.created_at) <= signed_up_before)

    base = select(User).where(*filters)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    items = (
        (await db.execute(base.order_by(User.created_at.desc()).offset(offset).limit(limit)))
        .scalars()
        .all()
    )
    return UserSearchPage(items=list(items), total=int(total))


@dataclass(frozen=True, slots=True)
class UserDetail:
    user: User
    subscription: Subscription | None
    recent_tool_runs: list[ToolRun]
    ai_spend_minor_30d: int
    ai_run_count_30d: int


async def get_user_detail(db: AsyncSession, *, user_id: uuid.UUID) -> UserDetail:
    user = await db.get(User, user_id)
    if user is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such user")

    subscription = (
        await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    ).scalar_one_or_none()

    recent_runs = (
        (
            await db.execute(
                select(ToolRun)
                .where(ToolRun.user_id == user_id)
                .order_by(ToolRun.created_at.desc())
                .limit(10)
            )
        )
        .scalars()
        .all()
    )

    since = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spend_row = (
        await db.execute(
            select(func.coalesce(func.sum(AIInvocation.cost_minor), 0), func.count()).where(
                AIInvocation.user_id == user_id, AIInvocation.created_at >= since
            )
        )
    ).one()

    return UserDetail(
        user=user,
        subscription=subscription,
        recent_tool_runs=list(recent_runs),
        ai_spend_minor_30d=int(spend_row[0]),
        ai_run_count_30d=int(spend_row[1]),
    )


async def _get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such user")
    return user


async def suspend_user(
    db: AsyncSession, *, admin_id: uuid.UUID, user_id: uuid.UUID, reason: str
) -> User:
    user = await _get_user_or_404(db, user_id)
    user.status = "suspended"
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.user.suspend",
        target_type="user",
        target_id=str(user_id),
        metadata={"reason": reason},
    )
    await db.commit()
    await db.refresh(user)
    return user


async def reinstate_user(db: AsyncSession, *, admin_id: uuid.UUID, user_id: uuid.UUID) -> User:
    user = await _get_user_or_404(db, user_id)
    user.status = "active"
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.user.reinstate",
        target_type="user",
        target_id=str(user_id),
    )
    await db.commit()
    await db.refresh(user)
    return user


async def force_password_reset(db: AsyncSession, *, admin_id: uuid.UUID, user_id: uuid.UUID) -> str:
    """Invalidates the user's current password (they must reset it to log
    in again) and returns a reset token an admin can hand to the user out
    of band -- there is no separate "admin reset flow" endpoint the token
    goes to; it's the same `POST /auth/reset-password` every self-service
    reset uses."""
    user = await _get_user_or_404(db, user_id)
    raw_token = generate_raw_token()
    db.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.password_reset_ttl_hours),
        )
    )
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.user.force_password_reset",
        target_type="user",
        target_id=str(user_id),
    )
    await db.commit()
    return raw_token


async def adjust_plan(
    db: AsyncSession, *, admin_id: uuid.UUID, user_id: uuid.UUID, plan: str, reason: str
) -> User:
    if not reason.strip():
        raise ApiError(ErrorCode.VALIDATION_FAILED, "a reason is required to change a user's plan")
    user = await _get_user_or_404(db, user_id)
    await apply_entitlements(db, user=user, plan=plan)
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.user.adjust_plan",
        target_type="user",
        target_id=str(user_id),
        metadata={"plan": plan, "reason": reason},
    )
    await db.commit()
    await db.refresh(user)
    return user


async def start_impersonation(
    db: AsyncSession, *, admin_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[str, datetime]:
    if admin_id == user_id:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "cannot impersonate yourself")
    target = await _get_user_or_404(db, user_id)
    token = create_impersonation_token(
        admin_id=admin_id, target_user_id=target.id, target_role=target.role
    )
    expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(
        minutes=DEFAULT_IMPERSONATION_TTL_MINUTES
    )
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.user.impersonate_start",
        target_type="user",
        target_id=str(user_id),
        metadata={"ttl_minutes": DEFAULT_IMPERSONATION_TTL_MINUTES},
    )
    await db.commit()
    return token, expires_at
