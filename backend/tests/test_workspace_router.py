from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.user import User


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_asset(db: AsyncSession, *, user: User, **kwargs: object) -> Asset:
    defaults: dict[str, object] = dict(
        user_id=user.id, type="post", title="A post", body="body text", body_format="text"
    )
    defaults.update(kwargs)
    asset = Asset(**defaults)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def test_assets_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/assets")).status_code == 401
    assert (await client.get("/api/v1/asset-folders")).status_code == 401


async def test_list_patch_and_favourite_an_asset(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    asset = await _create_asset(db_session, user=user, title="Original")

    list_response = await client.get("/api/v1/assets", headers=headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Original"

    patch_response = await client.patch(
        f"/api/v1/assets/{asset.id}",
        headers=headers,
        json={"title": "Renamed", "is_favourite": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Renamed"
    assert patch_response.json()["is_favourite"] is True

    versions_response = await client.get(f"/api/v1/assets/{asset.id}/versions", headers=headers)
    assert len(versions_response.json()) == 1
    assert versions_response.json()[0]["title"] == "Original"


async def test_trash_restore_and_permanent_delete(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    asset = await _create_asset(db_session, user=user)

    delete_response = await client.delete(f"/api/v1/assets/{asset.id}", headers=headers)
    assert delete_response.status_code == 204

    trash_response = await client.get("/api/v1/assets/trash", headers=headers)
    assert len(trash_response.json()) == 1

    restore_response = await client.post(f"/api/v1/assets/{asset.id}/restore", headers=headers)
    assert restore_response.status_code == 200
    assert restore_response.json()["deleted_at"] is None

    await client.delete(f"/api/v1/assets/{asset.id}", headers=headers)
    permanent_response = await client.delete(
        f"/api/v1/assets/{asset.id}", headers=headers, params={"permanent": "true"}
    )
    assert permanent_response.status_code == 204

    get_response = await client.get(f"/api/v1/assets/{asset.id}", headers=headers)
    assert get_response.status_code == 404


async def test_duplicate_asset_endpoint(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    asset = await _create_asset(db_session, user=user, title="Original")

    response = await client.post(f"/api/v1/assets/{asset.id}/duplicate", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Original (copy)"


async def test_export_single_asset_txt(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    asset = await _create_asset(db_session, user=user, title="Exportable")

    response = await client.get(
        f"/api/v1/assets/{asset.id}/export", headers=headers, params={"format": "txt"}
    )
    assert response.status_code == 200
    assert "Exportable" in response.text


async def test_bulk_move_tag_delete_and_export(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    a1 = await _create_asset(db_session, user=user, title="A1")
    a2 = await _create_asset(db_session, user=user, title="A2")

    move_response = await client.post(
        "/api/v1/assets/bulk",
        headers=headers,
        json={"action": "move", "asset_ids": [str(a1.id), str(a2.id)], "folder_id": None},
    )
    assert move_response.status_code == 200
    assert move_response.json()["affected_count"] == 2

    tag_response = await client.post(
        "/api/v1/assets/bulk",
        headers=headers,
        json={"action": "tag", "asset_ids": [str(a1.id)], "tags": ["important"]},
    )
    assert tag_response.json()["affected_count"] == 1

    export_response = await client.post(
        "/api/v1/assets/bulk",
        headers=headers,
        json={"action": "export", "asset_ids": [str(a1.id), str(a2.id)], "format": "txt"},
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "application/zip"

    delete_response = await client.post(
        "/api/v1/assets/bulk",
        headers=headers,
        json={"action": "delete", "asset_ids": [str(a2.id)]},
    )
    assert delete_response.json()["affected_count"] == 1

    list_response = await client.get("/api/v1/assets", headers=headers)
    titles = {item["title"] for item in list_response.json()["items"]}
    assert titles == {"A1"}


async def test_search_via_q_parameter(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    await _create_asset(db_session, user=user, title="Backend reliability post")
    await _create_asset(db_session, user=user, title="Unrelated cooking post")

    response = await client.get("/api/v1/assets", headers=headers, params={"q": "reliability"})
    assert response.status_code == 200
    assert [item["title"] for item in response.json()["items"]] == ["Backend reliability post"]


async def test_folder_crud_via_router(client: AsyncClient, registered_user: dict[str, str]) -> None:
    headers = await _auth_headers(client, registered_user)

    create_response = await client.post(
        "/api/v1/asset-folders", headers=headers, json={"name": "Saved Posts"}
    )
    assert create_response.status_code == 200
    folder_id = create_response.json()["id"]

    list_response = await client.get("/api/v1/asset-folders", headers=headers)
    assert [f["name"] for f in list_response.json()] == ["Saved Posts"]

    rename_response = await client.patch(
        f"/api/v1/asset-folders/{folder_id}", headers=headers, json={"name": "Renamed"}
    )
    assert rename_response.json()["name"] == "Renamed"

    delete_response = await client.delete(f"/api/v1/asset-folders/{folder_id}", headers=headers)
    assert delete_response.status_code == 204


async def test_patch_asset_not_found_returns_404(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.patch(
        f"/api/v1/assets/{uuid.uuid4()}", headers=headers, json={"title": "x"}
    )
    assert response.status_code == 404
