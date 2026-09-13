from __future__ import annotations

from httpx import AsyncClient


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    token = await _access_token(client, creds)
    return {"Authorization": f"Bearer {token}"}


async def test_create_asset_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/assets", json={"title": "x", "body": "y"})
    assert response.status_code == 401


async def test_create_asset_defaults_to_post_type(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/assets",
        headers=headers,
        json={"title": "My draft", "body": "Some post text"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "post"
    assert body["title"] == "My draft"
    assert body["metadata"] == {}


async def test_mark_posted_updates_metadata(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post(
        "/api/v1/assets",
        headers=headers,
        json={"title": "My draft", "body": "Some post text"},
    )
    asset_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/assets/{asset_id}/mark-posted",
        headers=headers,
        json={"linkedin_url": "https://www.linkedin.com/feed/update/urn:li:activity:123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["posted"] is True
    assert (
        body["metadata"]["linkedin_url"]
        == "https://www.linkedin.com/feed/update/urn:li:activity:123"
    )


async def test_mark_posted_404s_for_unknown_asset(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/assets/00000000-0000-0000-0000-000000000000/mark-posted",
        headers=headers,
        json={},
    )
    assert response.status_code == 404
