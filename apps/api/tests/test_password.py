from httpx import AsyncClient


async def test_forgot_password_is_generic_for_unknown_email(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}
    )
    assert response.status_code == 200
    assert len(sent_emails) == 0


async def test_reset_password_with_valid_token_then_forces_relogin(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[dict[str, str]]
) -> None:
    await client.post("/api/v1/auth/login", json=registered_user)

    await client.post("/api/v1/auth/forgot-password", json={"email": registered_user["email"]})
    reset_token = next(e["token"] for e in sent_emails if e["kind"] == "reset")

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "brand-new-pass-42"},
    )
    assert reset_response.status_code == 200

    # Old sessions were revoked by the reset.
    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401

    # Old password no longer works; new one does.
    old_login = await client.post("/api/v1/auth/login", json=registered_user)
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "brand-new-pass-42"},
    )
    assert new_login.status_code == 200


async def test_reset_password_rejects_reused_token(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[dict[str, str]]
) -> None:
    await client.post("/api/v1/auth/forgot-password", json={"email": registered_user["email"]})
    reset_token = next(e["token"] for e in sent_emails if e["kind"] == "reset")
    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "brand-new-pass-42"},
    )
    replay = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "another-pass-43"},
    )
    assert replay.status_code == 404


async def test_change_password_requires_current_password(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/login", json=registered_user)
    access_token = login.json()["access_token"]

    bad = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrong", "new_password": "new-pass-super-42"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert bad.status_code == 401

    good = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": registered_user["password"],
            "new_password": "new-pass-super-42",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert good.status_code == 200

    relogin = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "new-pass-super-42"},
    )
    assert relogin.status_code == 200
