from httpx import AsyncClient


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def test_update_profile(client: AsyncClient, registered_user: dict[str, str]) -> None:
    access_token = await _access_token(client, registered_user)
    response = await client.patch(
        "/api/v1/me",
        json={"full_name": "New Name", "timezone": "America/New_York"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "New Name"
    assert body["timezone"] == "America/New_York"


async def test_update_profile_rejects_unknown_timezone(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    response = await client.patch(
        "/api/v1/me",
        json={"timezone": "Not/A_Zone"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422


async def test_delete_account_requires_correct_password(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    bad = await client.request(
        "DELETE",
        "/api/v1/me",
        json={"current_password": "wrong"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert bad.status_code == 401

    good = await client.request(
        "DELETE",
        "/api/v1/me",
        json={"current_password": registered_user["password"]},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert good.status_code == 200

    relogin = await client.post("/api/v1/auth/login", json=registered_user)
    assert relogin.status_code == 403
    assert relogin.json()["error"]["code"] == "FORBIDDEN"
