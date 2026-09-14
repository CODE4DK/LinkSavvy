"""Shared fixtures for the Profile Hub tools' golden tests: a real user
with a committed, richly-populated ProfileSnapshot (so every ContextKey
these tools declare has something real to serialize), reusing the exact
same fixture data Phase 4's category-audit tests are grounded in."""

from __future__ import annotations

import uuid

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot

from ...audit.categories.conftest import rich_snapshot

__all__ = ["rich_snapshot"]


@pytest_asyncio.fixture
async def profile_user(db_session: AsyncSession) -> User:
    user = User(email=f"tools-def-{uuid.uuid4()}@example.com", full_name="Tools Tester")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def rich_profile_user(db_session: AsyncSession, profile_user: User) -> User:
    """`profile_user`, with `rich_snapshot()` (Jamie Rivera, Senior Backend
    Engineer at Acme Corp) committed as their active snapshot."""
    await commit_snapshot(
        db_session, user=profile_user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()
    return profile_user
