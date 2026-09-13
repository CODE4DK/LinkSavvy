from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.asset_service import create_asset, mark_posted
from app.errors import ApiError
from app.models.user import User
from app.tools.definition import AssetType


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"asset-{uuid.uuid4()}@example.com", full_name="Asset Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_asset_persists_without_a_tool_run(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await create_asset(
        db_session, user=user, type=AssetType.POST, title="Draft", body="Some post text"
    )
    assert asset.type == "post"
    assert asset.title == "Draft"
    assert asset.body == "Some post text"
    assert asset.source_tool_run_id is None
    assert asset.metadata_ == {}


async def test_mark_posted_records_the_linkedin_url_and_timestamp(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    asset = await create_asset(
        db_session, user=user, type=AssetType.POST, title="Draft", body="Some post text"
    )
    updated = await mark_posted(
        db_session,
        user=user,
        asset_id=asset.id,
        linkedin_url="https://www.linkedin.com/feed/update/urn:li:activity:123",
    )
    assert updated.metadata_["posted"] is True
    assert (
        updated.metadata_["linkedin_url"]
        == "https://www.linkedin.com/feed/update/urn:li:activity:123"
    )
    assert updated.metadata_["posted_at"]


async def test_mark_posted_rejects_another_users_asset(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    asset = await create_asset(
        db_session, user=owner, type=AssetType.POST, title="Draft", body="text"
    )
    with pytest.raises(ApiError):
        await mark_posted(db_session, user=other, asset_id=asset.id, linkedin_url=None)


async def test_mark_posted_rejects_an_unknown_asset(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    with pytest.raises(ApiError):
        await mark_posted(db_session, user=user, asset_id=uuid.uuid4(), linkedin_url=None)
