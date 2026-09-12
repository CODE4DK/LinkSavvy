from httpx import AsyncClient


async def test_login_succeeds_and_sets_refresh_cookie(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    response = await client.post("/api/v1/auth/login", json=registered_user)
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == registered_user["email"]
    assert "refresh_token" in response.cookies


async def test_login_rejects_wrong_password(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "wrong-password-1"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_blocks_unverified_email(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "unverified@example.com",
            "password": "correct-horse-99",
            "full_name": "Unverified",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "correct-horse-99"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


async def test_login_rate_limits_after_repeated_failures(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    bad = {"email": registered_user["email"], "password": "wrong-password-1"}
    last = None
    for _ in range(15):
        last = await client.post("/api/v1/auth/login", json=bad)
    assert last is not None
    assert last.status_code == 429
    assert last.json()["error"]["code"] == "RATE_LIMITED"


async def test_me_requires_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


async def test_me_returns_user_and_flags(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/login", json=registered_user)
    access_token = login.json()["access_token"]

    response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == registered_user["email"]
    assert "hub.profile" in body["feature_flags"]
