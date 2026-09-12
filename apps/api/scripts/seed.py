"""Seed local/dev data: hub feature flags plus an admin and a demo user.

Idempotent — safe to run repeatedly against the same database.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.feature_flag import FeatureFlag
from app.models.user import User
from app.security.passwords import hash_password
from app.services.feature_flags import ALL_DEFAULT_FLAG_KEYS

ADMIN_EMAIL = "admin@linksavvy.dev"
ADMIN_PASSWORD = "AdminPass123!"
DEMO_EMAIL = "demo@linksavvy.dev"
DEMO_PASSWORD = "DemoPass123!"


async def _ensure_flag(db: AsyncSession, key: str) -> None:
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    if result.scalar_one_or_none() is not None:
        return
    db.add(
        FeatureFlag(
            key=key,
            enabled_globally=False,
            rollout_percent=0,
            description=f"Auto-seeded flag for {key}",
        )
    )


async def _ensure_user(
    db: AsyncSession, *, email: str, password: str, full_name: str, role: str
) -> None:
    result = await db.execute(select(User).where(User.email_normalized == email.lower()))
    if result.scalar_one_or_none() is not None:
        return
    db.add(
        User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            email_verified_at=datetime.now(UTC),
        )
    )


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        for key in ALL_DEFAULT_FLAG_KEYS:
            await _ensure_flag(db, key)
        await _ensure_user(
            db,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            full_name="LinkSavvy Admin",
            role="admin",
        )
        await _ensure_user(
            db,
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
            full_name="Demo User",
            role="user",
        )
        await db.commit()

    print("Seeded feature flags plus admin/demo users:")
    print(f"  admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  demo:  {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
