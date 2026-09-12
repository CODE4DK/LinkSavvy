"""Resolve which feature flags are on for a given user."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature_flag import FeatureFlag, UserFeatureFlag

HUB_FLAG_KEYS = [
    "hub.profile",
    "hub.content",
    "hub.engagement",
    "hub.career",
    "hub.growth",
    "hub.workspace",
]
ALL_DEFAULT_FLAG_KEYS = [*HUB_FLAG_KEYS, "assistant", "audit"]


def _bucket_percent(user_id: uuid.UUID, key: str) -> int:
    digest = hashlib.sha256(f"{user_id}:{key}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


async def resolve_flags_for_user(db: AsyncSession, *, user_id: uuid.UUID) -> dict[str, bool]:
    flags = (await db.execute(select(FeatureFlag))).scalars().all()
    overrides = {
        row.flag_id: row.enabled
        for row in (
            await db.execute(select(UserFeatureFlag).where(UserFeatureFlag.user_id == user_id))
        )
        .scalars()
        .all()
    }

    resolved: dict[str, bool] = {}
    for flag in flags:
        if flag.id in overrides:
            resolved[flag.key] = overrides[flag.id]
            continue
        if flag.enabled_globally:
            resolved[flag.key] = True
            continue
        resolved[flag.key] = _bucket_percent(user_id, flag.key) < flag.rollout_percent
    return resolved
