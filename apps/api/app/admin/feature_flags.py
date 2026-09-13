"""Admin CRUD over feature flags -- global toggle, rollout percentage,
and per-user overrides. Reads/writes the same `feature_flags` /
`user_feature_flags` tables app.services.feature_flags.resolve_flags_for_user
already resolves against; this module only adds the admin-facing writes.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.feature_flag import FeatureFlag, UserFeatureFlag
from app.services.audit import record_audit_event


async def list_flags(db: AsyncSession) -> list[FeatureFlag]:
    return list((await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))).scalars().all())


async def _get_flag_or_404(db: AsyncSession, key: str) -> FeatureFlag:
    flag = (
        await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    ).scalar_one_or_none()
    if flag is None:
        raise ApiError(ErrorCode.NOT_FOUND, f"no such feature flag: {key}")
    return flag


async def set_global(
    db: AsyncSession, *, admin_id: uuid.UUID, key: str, enabled_globally: bool
) -> FeatureFlag:
    flag = await _get_flag_or_404(db, key)
    flag.enabled_globally = enabled_globally
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.feature_flag.set_global",
        target_type="feature_flag",
        target_id=key,
        metadata={"enabled_globally": enabled_globally},
    )
    await db.commit()
    await db.refresh(flag)
    return flag


async def set_rollout(
    db: AsyncSession, *, admin_id: uuid.UUID, key: str, rollout_percent: int
) -> FeatureFlag:
    if not 0 <= rollout_percent <= 100:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "rollout_percent must be between 0 and 100")
    flag = await _get_flag_or_404(db, key)
    flag.rollout_percent = rollout_percent
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.feature_flag.set_rollout",
        target_type="feature_flag",
        target_id=key,
        metadata={"rollout_percent": rollout_percent},
    )
    await db.commit()
    await db.refresh(flag)
    return flag


async def set_user_override(
    db: AsyncSession, *, admin_id: uuid.UUID, key: str, user_id: uuid.UUID, enabled: bool | None
) -> None:
    """`enabled=None` clears the override, falling back to the global
    setting/rollout for that user again."""
    flag = await _get_flag_or_404(db, key)
    existing = (
        await db.execute(
            select(UserFeatureFlag).where(
                UserFeatureFlag.user_id == user_id, UserFeatureFlag.flag_id == flag.id
            )
        )
    ).scalar_one_or_none()

    if enabled is None:
        if existing is not None:
            await db.delete(existing)
    elif existing is not None:
        existing.enabled = enabled
    else:
        db.add(UserFeatureFlag(user_id=user_id, flag_id=flag.id, enabled=enabled))

    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.feature_flag.set_user_override",
        target_type="feature_flag",
        target_id=key,
        metadata={"user_id": str(user_id), "enabled": enabled},
    )
    await db.commit()
