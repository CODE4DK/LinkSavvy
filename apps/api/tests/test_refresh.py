from httpx import AsyncClient

from tests.conftest import csrf_headers


async def test_refresh_rotates_token_and_issues_new_access_token(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/login", json=registered_user)
    old_cookie = login.cookies["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", headers=csrf_headers(client))
    assert response.status_code == 200
    assert response.json()["access_token"]
    new_cookie = response.cookies["refresh_token"]
    assert new_cookie != old_cookie


async def test_refresh_without_cookie_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_refresh_rejects_a_forged_request_missing_the_csrf_header(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    await client.post("/api/v1/auth/login", json=registered_user)
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_reused_refresh_token_revokes_family(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/login", json=registered_user)
    original_cookie = login.cookies["refresh_token"]

    first_refresh = await client.post("/api/v1/auth/refresh", headers=csrf_headers(client))
    assert first_refresh.status_code == 200

    # Replay the *original* (already-rotated-away) cookie — this is theft.
    client.cookies.set("refresh_token", original_cookie)
    reused = await client.post("/api/v1/auth/refresh", headers=csrf_headers(client))
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "TOKEN_REUSED"

    # The whole family is now burned, including the token from the first
    # (legitimate) rotation.
    client.cookies.set("refresh_token", first_refresh.cookies["refresh_token"])
    blocked = await client.post("/api/v1/auth/refresh", headers=csrf_headers(client))
    assert blocked.status_code == 401
