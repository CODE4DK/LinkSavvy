from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError
from app.models.asset import Asset
from app.models.user import User
from app.workspace import folders as service


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"folders-{uuid.uuid4()}@example.com", full_name="Folder Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_list_rename_and_delete_folder(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    folder = await service.create_folder(db_session, user=user, name="Saved Posts", parent_id=None)

    listed = await service.list_folders(db_session, user_id=user.id)
    assert [f.name for f in listed] == ["Saved Posts"]

    renamed = await service.rename_folder(
        db_session, user=user, folder_id=folder.id, name="Renamed"
    )
    assert renamed.name == "Renamed"

    await service.delete_folder(db_session, user=user, folder_id=folder.id)
    assert await service.list_folders(db_session, user_id=user.id) == []


async def test_nested_folders_and_move(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    parent = await service.create_folder(db_session, user=user, name="Parent", parent_id=None)
    child = await service.create_folder(db_session, user=user, name="Child", parent_id=parent.id)
    assert child.parent_id == parent.id

    other_parent = await service.create_folder(db_session, user=user, name="Other", parent_id=None)
    moved = await service.move_folder(
        db_session, user=user, folder_id=child.id, parent_id=other_parent.id
    )
    assert moved.parent_id == other_parent.id

    unfiled = await service.move_folder(db_session, user=user, folder_id=child.id, parent_id=None)
    assert unfiled.parent_id is None


async def test_folder_cannot_be_its_own_parent(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    folder = await service.create_folder(db_session, user=user, name="F", parent_id=None)
    try:
        await service.move_folder(db_session, user=user, folder_id=folder.id, parent_id=folder.id)
        raise AssertionError("expected a validation error")
    except ApiError:
        pass


async def test_deleting_a_folder_unfiles_its_assets(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    folder = await service.create_folder(db_session, user=user, name="F", parent_id=None)
    asset = Asset(
        user_id=user.id,
        type="post",
        title="A",
        body="b",
        body_format="text",
        folder_id=folder.id,
    )
    db_session.add(asset)
    await db_session.commit()

    await service.delete_folder(db_session, user=user, folder_id=folder.id)

    await db_session.refresh(asset)
    assert asset.folder_id is None


async def test_deleting_a_folder_reparents_its_subfolders_to_the_root(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    parent = await service.create_folder(db_session, user=user, name="Parent", parent_id=None)
    child = await service.create_folder(db_session, user=user, name="Child", parent_id=parent.id)

    await service.delete_folder(db_session, user=user, folder_id=parent.id)

    await db_session.refresh(child)
    assert child.parent_id is None


async def test_cross_user_folder_access_is_denied(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session)
    other = await _create_user(db_session)
    folder = await service.create_folder(db_session, user=owner, name="Mine", parent_id=None)

    try:
        await service.rename_folder(db_session, user=other, folder_id=folder.id, name="Hijack")
        raise AssertionError("expected NOT_FOUND")
    except ApiError:
        pass
