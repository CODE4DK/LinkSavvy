from httpx import AsyncClient


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def test_list_sessions_shows_current(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    response = await client.get(
        "/api/v1/auth/sessions", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["current"] is True


async def test_delete_session_revokes_it(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    sessions = (
        await client.get(
            "/api/v1/auth/sessions", headers={"Authorization": f"Bearer {access_token}"}
        )
    ).json()
    session_id = sessions[0]["id"]

    delete_response = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert delete_response.status_code == 200

    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401


async def test_logout_all_revokes_every_session(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    response = await client.post(
        "/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401
