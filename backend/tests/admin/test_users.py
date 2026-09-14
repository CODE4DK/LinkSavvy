from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import users as admin_users
from app.errors import ApiError
from app.models.audit_log import AuditLog
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.security.jwt import IMPERSONATION_TOKEN_TYPE


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(email=f"admin-test-{uuid.uuid4()}@example.com", full_name="Admin Target", **kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_search_users_filters_by_plan(db_session: AsyncSession) -> None:
    await _create_user(db_session, plan="free")
    await _create_user(db_session, plan="pro")

    page = await admin_users.search_users(db_session, plan="pro")
    assert page.total == 1
    assert all(u.plan == "pro" for u in page.items)


async def test_search_users_query_matches_email(db_session: AsyncSession) -> None:
    target = await _create_user(db_session)
    page = await admin_users.search_users(db_session, query=target.email.split("@")[0])
    assert any(u.id == target.id for u in page.items)


async def test_suspend_and_reinstate_writes_audit_log(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    target = await _create_user(db_session)

    suspended = await admin_users.suspend_user(
        db_session, admin_id=admin.id, user_id=target.id, reason="abuse report"
    )
    assert suspended.status == "suspended"

    logs = (
        (await db_session.execute(select(AuditLog).where(AuditLog.action == "admin.user.suspend")))
        .scalars()
        .all()
    )
    assert len(logs) == 1
    assert logs[0].actor_user_id == admin.id
    assert logs[0].target_id == str(target.id)

    reinstated = await admin_users.reinstate_user(db_session, admin_id=admin.id, user_id=target.id)
    assert reinstated.status == "active"


async def test_force_password_reset_clears_password_and_creates_reset_row(
    db_session: AsyncSession,
) -> None:
    admin = await _create_user(db_session, role="admin")
    target = await _create_user(db_session, password_hash="some-hash")

    token = await admin_users.force_password_reset(db_session, admin_id=admin.id, user_id=target.id)
    assert token

    resets = (
        (await db_session.execute(select(PasswordReset).where(PasswordReset.user_id == target.id)))
        .scalars()
        .all()
    )
    assert len(resets) == 1


async def test_adjust_plan_requires_a_reason(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    target = await _create_user(db_session)
    try:
        await admin_users.adjust_plan(
            db_session, admin_id=admin.id, user_id=target.id, plan="pro", reason="   "
        )
        raise AssertionError("expected ApiError")
    except ApiError as exc:
        assert exc.code.value == "VALIDATION_FAILED"


async def test_adjust_plan_applies_entitlements(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    target = await _create_user(db_session)
    updated = await admin_users.adjust_plan(
        db_session, admin_id=admin.id, user_id=target.id, plan="pro", reason="goodwill upgrade"
    )
    assert updated.plan == "pro"


async def test_start_impersonation_issues_a_read_only_scoped_token(
    db_session: AsyncSession,
) -> None:
    admin = await _create_user(db_session, role="admin")
    target = await _create_user(db_session)

    token, expires_at = await admin_users.start_impersonation(
        db_session, admin_id=admin.id, user_id=target.id
    )
    assert token
    assert expires_at is not None

    import jwt as pyjwt

    from app.settings import settings

    payload = pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert payload["type"] == IMPERSONATION_TOKEN_TYPE
    assert payload["sub"] == str(target.id)
    assert payload["impersonator_id"] == str(admin.id)


async def test_cannot_impersonate_yourself(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    try:
        await admin_users.start_impersonation(db_session, admin_id=admin.id, user_id=admin.id)
        raise AssertionError("expected ApiError")
    except ApiError as exc:
        assert exc.code.value == "VALIDATION_FAILED"
