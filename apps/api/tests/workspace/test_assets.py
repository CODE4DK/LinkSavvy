from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError
from app.models.asset import Asset
from app.models.tool_run import ToolRun
from app.models.user import User
from app.workspace import assets as service


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"workspace-{uuid.uuid4()}@example.com", full_name="Workspace Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_asset(
    db: AsyncSession,
    *,
    user: User,
    title: str = "A post",
    body: str = "Some body text",
    type: str = "post",
    tags: list[str] | None = None,
    is_favourite: bool = False,
    folder_id: uuid.UUID | None = None,
    source_tool_run_id: uuid.UUID | None = None,
) -> Asset:
    asset = Asset(
        user_id=user.id,
        type=type,
        title=title,
        body=body,
        body_format="text",
        tags=tags or [],
        is_favourite=is_favourite,
        folder_id=folder_id,
        source_tool_run_id=source_tool_run_id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def test_list_assets_excludes_deleted(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    kept = await _create_asset(db_session, user=user, title="Kept")
    deleted = await _create_asset(db_session, user=user, title="Deleted")
    deleted.deleted_at = datetime.now(UTC)
    await db_session.commit()

    page = await service.list_assets(db_session, user_id=user.id)
    ids = {a.id for a in page.items}
    assert kept.id in ids
    assert deleted.id not in ids


async def test_list_assets_filters_by_type_and_favourite(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _create_asset(db_session, user=user, type="post", is_favourite=True, title="Fav post")
    await _create_asset(db_session, user=user, type="post", is_favourite=False, title="Plain post")
    await _create_asset(db_session, user=user, type="resume", is_favourite=True, title="Fav resume")

    page = await service.list_assets(db_session, user_id=user.id, type="post", favourite=True)
    assert [a.title for a in page.items] == ["Fav post"]


async def test_list_assets_filters_by_tags_requires_all(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _create_asset(db_session, user=user, title="Both", tags=["a", "b"])
    await _create_asset(db_session, user=user, title="OnlyA", tags=["a"])

    page = await service.list_assets(db_session, user_id=user.id, tags=["a", "b"])
    assert [a.title for a in page.items] == ["Both"]


async def test_list_assets_filters_by_source_tool_id(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    run = ToolRun(
        user_id=user.id,
        tool_id="profile.headline_optimizer",
        prompt_id="profile.headline_optimizer.v1",
        prompt_version=1,
        input={},
        output={},
        context_keys=[],
        status="succeeded",
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    await _create_asset(db_session, user=user, title="From tool", source_tool_run_id=run.id)
    await _create_asset(db_session, user=user, title="Manual")

    page = await service.list_assets(
        db_session, user_id=user.id, source_tool_id="profile.headline_optimizer"
    )
    assert [a.title for a in page.items] == ["From tool"]


async def test_list_assets_cursor_pagination(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    for i in range(5):
        await _create_asset(db_session, user=user, title=f"Post {i}")

    first_page = await service.list_assets(db_session, user_id=user.id, limit=2)
    assert len(first_page.items) == 2
    assert first_page.next_cursor is not None

    second_page = await service.list_assets(
        db_session, user_id=user.id, limit=2, cursor=first_page.next_cursor
    )
    assert len(second_page.items) == 2
    first_ids = {a.id for a in first_page.items}
    second_ids = {a.id for a in second_page.items}
    assert first_ids.isdisjoint(second_ids)


async def test_search_finds_matching_assets_via_like_fallback(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _create_asset(db_session, user=user, title="Backend reliability post", body="on-call")
    await _create_asset(db_session, user=user, title="Unrelated", body="cooking recipes")

    page = await service.list_assets(db_session, user_id=user.id, q="reliability")
    assert [a.title for a in page.items] == ["Backend reliability post"]


async def test_patch_asset_rename_creates_a_version(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user=user, title="Original", body="Original body")

    updated = await service.patch_asset(
        db_session, user=user, asset_id=asset.id, title="Renamed", body="New body"
    )
    assert updated.title == "Renamed"
    assert updated.body == "New body"

    versions = await service.list_versions(db_session, user=user, asset_id=asset.id)
    assert len(versions) == 1
    assert versions[0].title == "Original"
    assert versions[0].body == "Original body"
    assert versions[0].version == 1


async def test_patch_asset_tags_and_favourite_do_not_version(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user=user)

    await service.patch_asset(
        db_session, user=user, asset_id=asset.id, tags=["x"], is_favourite=True
    )
    versions = await service.list_versions(db_session, user=user, asset_id=asset.id)
    assert versions == []


async def test_patch_asset_folder_move_and_unfile(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user=user)
    folder_id = uuid.uuid4()

    unchanged = await service.patch_asset(db_session, user=user, asset_id=asset.id, title="Same")
    assert unchanged.folder_id is None

    moved = await service.patch_asset(db_session, user=user, asset_id=asset.id, folder_id=folder_id)
    assert moved.folder_id == folder_id

    unfiled = await service.patch_asset(db_session, user=user, asset_id=asset.id, folder_id=None)
    assert unfiled.folder_id is None


async def test_soft_delete_restore_and_permanent_delete(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user=user)

    deleted = await service.soft_delete_asset(db_session, user=user, asset_id=asset.id)
    assert deleted.deleted_at is not None

    trashed = await service.list_trash(db_session, user_id=user.id)
    assert [a.id for a in trashed] == [asset.id]

    restored = await service.restore_asset(db_session, user=user, asset_id=asset.id)
    assert restored.deleted_at is None

    await service.soft_delete_asset(db_session, user=user, asset_id=asset.id)
    await service.permanently_delete_asset(db_session, user=user, asset_id=asset.id)
    try:
        await service.get_owned_asset(
            db_session, user_id=user.id, asset_id=asset.id, include_deleted=True
        )
        raise AssertionError("expected NOT_FOUND")
    except ApiError:
        pass


async def test_trash_excludes_items_past_the_retention_window(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user=user)
    asset.deleted_at = datetime.now(UTC) - timedelta(days=31)
    await db_session.commit()

    trashed = await service.list_trash(db_session, user_id=user.id)
    assert trashed == []


async def test_purge_expired_trash_hard_deletes_old_items(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    old = await _create_asset(db_session, user=user, title="Old")
    old.deleted_at = datetime.now(UTC) - timedelta(days=31)
    recent = await _create_asset(db_session, user=user, title="Recent")
    recent.deleted_at = datetime.now(UTC) - timedelta(days=5)
    await db_session.commit()

    purged = await service.purge_expired_trash(db_session)
    assert purged == 1

    remaining = await db_session.get(Asset, recent.id)
    assert remaining is not None
    assert await db_session.get(Asset, old.id) is None


async def test_duplicate_asset(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user=user, title="Original", tags=["a"])

    copy = await service.duplicate_asset(db_session, user=user, asset_id=asset.id)
    assert copy.id != asset.id
    assert copy.title == "Original (copy)"
    assert copy.tags == ["a"]
    assert copy.is_favourite is False


async def test_bulk_move_tag_and_delete(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    a1 = await _create_asset(db_session, user=user, title="A1")
    a2 = await _create_asset(db_session, user=user, title="A2")
    folder_id = uuid.uuid4()

    moved = await service.bulk_move(
        db_session, user=user, asset_ids=[a1.id, a2.id], folder_id=folder_id
    )
    assert moved == 2

    tagged = await service.bulk_tag(db_session, user=user, asset_ids=[a1.id, a2.id], tags=["bulk"])
    assert tagged == 2

    deleted = await service.bulk_delete(db_session, user=user, asset_ids=[a1.id])
    assert deleted == 1

    await db_session.refresh(a1)
    await db_session.refresh(a2)
    assert a1.deleted_at is not None
    assert a2.deleted_at is None
    assert a1.folder_id == folder_id
    assert "bulk" in a2.tags


async def test_cross_user_access_is_denied(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    asset = await _create_asset(db_session, user=owner)

    try:
        await service.get_owned_asset(db_session, user_id=other.id, asset_id=asset.id)
        raise AssertionError("expected NOT_FOUND")
    except ApiError:
        pass
