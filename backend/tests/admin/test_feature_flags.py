from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import feature_flags as admin_flags
from app.errors import ApiError
from app.models.user import User
from app.services.feature_flags import resolve_flags_for_user


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(email=f"flag-test-{uuid.uuid4()}@example.com", full_name="Flag Tester", **kwargs)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_set_global_toggles_flag_for_everyone(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    user = await _create_user(db_session)

    flag = await admin_flags.set_global(
        db_session, admin_id=admin.id, key="hub.profile", enabled_globally=True
    )
    assert flag.enabled_globally is True

    resolved = await resolve_flags_for_user(db_session, user_id=user.id)
    assert resolved["hub.profile"] is True


async def test_set_rollout_validates_range(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    try:
        await admin_flags.set_rollout(
            db_session, admin_id=admin.id, key="hub.profile", rollout_percent=150
        )
        raise AssertionError("expected ApiError")
    except ApiError as exc:
        assert exc.code.value == "VALIDATION_FAILED"


async def test_user_override_wins_over_global_setting(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    user = await _create_user(db_session)

    await admin_flags.set_global(
        db_session, admin_id=admin.id, key="hub.profile", enabled_globally=False
    )
    await admin_flags.set_user_override(
        db_session, admin_id=admin.id, key="hub.profile", user_id=user.id, enabled=True
    )

    resolved = await resolve_flags_for_user(db_session, user_id=user.id)
    assert resolved["hub.profile"] is True


async def test_clearing_user_override_falls_back_to_global(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    user = await _create_user(db_session)

    await admin_flags.set_global(
        db_session, admin_id=admin.id, key="hub.profile", enabled_globally=False
    )
    await admin_flags.set_user_override(
        db_session, admin_id=admin.id, key="hub.profile", user_id=user.id, enabled=True
    )
    await admin_flags.set_user_override(
        db_session, admin_id=admin.id, key="hub.profile", user_id=user.id, enabled=None
    )

    resolved = await resolve_flags_for_user(db_session, user_id=user.id)
    assert resolved["hub.profile"] is False
