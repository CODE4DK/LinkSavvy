from __future__ import annotations

from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_coach_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/growth/coach/session")).status_code == 401
    response = await client.post("/api/v1/growth/coach/messages", json={"text": "hi"})
    assert response.status_code == 401


async def test_coach_session_starts_empty_then_grows_with_messages(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)

    session_response = await client.get("/api/v1/growth/coach/session", headers=headers)
    assert session_response.status_code == 200
    session_body = session_response.json()
    assert session_body["messages"] == []
    assert session_body["goal_id"] is None

    message_response = await client.post(
        "/api/v1/growth/coach/messages", headers=headers, json={"text": "Hi coach"}
    )
    assert message_response.status_code == 200
    reply = message_response.json()
    assert reply["role"] == "assistant"
    assert reply["metadata"]["phase"] == "interviewing"

    session_response_again = await client.get("/api/v1/growth/coach/session", headers=headers)
    messages = session_response_again.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Hi coach"


async def test_coach_message_requires_non_empty_text(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/growth/coach/messages", headers=headers, json={"text": ""}
    )
    assert response.status_code == 422
