from httpx import AsyncClient


async def test_register_sends_verification_email(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "correct-horse-99",
            "full_name": "New Person",
        },
    )
    assert response.status_code == 200
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "new@example.com"


async def test_register_rejects_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short1", "full_name": "Weak"},
    )
    assert response.status_code == 422


async def test_register_does_not_reveal_existing_email(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    payload = {
        "email": "dupe@example.com",
        "password": "correct-horse-99",
        "full_name": "Dupe",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    # Only the first registration actually sends mail.
    assert len(sent_emails) == 1


async def test_verify_email_activates_account(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify@example.com",
            "password": "correct-horse-99",
            "full_name": "Verify Me",
        },
    )
    token = sent_emails[0]["token"]

    response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 200

    # Single-use: replaying the token fails.
    replay = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert replay.status_code == 404
    assert replay.json()["error"]["code"] == "NOT_FOUND"


async def test_verify_email_rejects_unknown_token(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/verify-email", json={"token": "does-not-exist"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_resend_verification_is_generic_for_unknown_email(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    response = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 200
    assert len(sent_emails) == 0
