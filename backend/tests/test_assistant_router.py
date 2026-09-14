from __future__ import annotations

from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_assistant_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/assistant/conversations")).status_code == 401
    assert (await client.post("/api/v1/assistant/conversations", json={})).status_code == 401


async def test_create_list_and_get_conversation(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)

    create_response = await client.post(
        "/api/v1/assistant/conversations", headers=headers, json={"mode": "auto"}
    )
    assert create_response.status_code == 200
    conversation = create_response.json()
    assert conversation["mode"] == "auto"
    assert conversation["message_count"] == 0

    list_response = await client.get("/api/v1/assistant/conversations", headers=headers)
    assert any(c["id"] == conversation["id"] for c in list_response.json())

    detail_response = await client.get(
        f"/api/v1/assistant/conversations/{conversation['id']}", headers=headers
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["messages"] == []


async def test_tool_mode_conversation_requires_a_tool_id(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/assistant/conversations", headers=headers, json={"mode": "tool"}
    )
    assert response.status_code == 422


async def test_sending_a_message_produces_an_assistant_reply_and_auto_titles(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    conversation = (
        await client.post("/api/v1/assistant/conversations", headers=headers, json={})
    ).json()

    response = await client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"text": "How can I improve my profile?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"]["role"] == "assistant"
    assert body["quota"]["metric"] == "assistant_messages"
    assert body["quota"]["used"] == 1

    conversation_again = (
        await client.get(f"/api/v1/assistant/conversations/{conversation['id']}", headers=headers)
    ).json()
    assert conversation_again["conversation"]["title"] == "How can I improve my profile?"
    assert len(conversation_again["messages"]) == 2


async def test_sending_an_empty_message_is_rejected(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    conversation = (
        await client.post("/api/v1/assistant/conversations", headers=headers, json={})
    ).json()
    response = await client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"text": ""},
    )
    assert response.status_code == 422


async def test_rename_archive_and_delete_conversation(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    conversation = (
        await client.post("/api/v1/assistant/conversations", headers=headers, json={})
    ).json()
    conversation_id = conversation["id"]

    renamed = await client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/rename",
        headers=headers,
        json={"title": "My renamed thread"},
    )
    assert renamed.json()["title"] == "My renamed thread"

    archived = await client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/archive",
        headers=headers,
        json={"archived": True},
    )
    assert archived.json()["is_archived"] is True

    not_in_default_list = await client.get("/api/v1/assistant/conversations", headers=headers)
    assert all(c["id"] != conversation_id for c in not_in_default_list.json())

    in_full_list = await client.get(
        "/api/v1/assistant/conversations", headers=headers, params={"include_archived": True}
    )
    assert any(c["id"] == conversation_id for c in in_full_list.json())

    delete_response = await client.delete(
        f"/api/v1/assistant/conversations/{conversation_id}", headers=headers
    )
    assert delete_response.status_code == 204

    get_after_delete = await client.get(
        f"/api/v1/assistant/conversations/{conversation_id}", headers=headers
    )
    assert get_after_delete.status_code == 404


async def test_context_settings_default_to_nothing_excluded_and_can_be_toggled(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    conversation = (
        await client.post("/api/v1/assistant/conversations", headers=headers, json={})
    ).json()
    conversation_id = conversation["id"]

    settings = await client.get(
        f"/api/v1/assistant/conversations/{conversation_id}/context", headers=headers
    )
    assert settings.status_code == 200
    items = settings.json()["items"]
    assert len(items) >= 5
    assert all(item["excluded"] is False for item in items)

    key_to_exclude = items[0]["key"]
    updated = await client.patch(
        f"/api/v1/assistant/conversations/{conversation_id}/context",
        headers=headers,
        json={"excluded_context_keys": [key_to_exclude]},
    )
    assert updated.status_code == 200
    updated_items = {item["key"]: item["excluded"] for item in updated.json()["items"]}
    assert updated_items[key_to_exclude] is True


async def test_save_conversation_creates_a_workspace_asset(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    conversation = (
        await client.post("/api/v1/assistant/conversations", headers=headers, json={})
    ).json()
    await client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"text": "Help me plan my week"},
    )

    saved = await client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/save",
        headers=headers,
        json={},
    )
    assert saved.status_code == 200
    assert saved.json()["asset_id"] is not None


async def test_rate_message_endpoint(client: AsyncClient, registered_user: dict[str, str]) -> None:
    headers = await _auth_headers(client, registered_user)
    conversation = (
        await client.post("/api/v1/assistant/conversations", headers=headers, json={})
    ).json()
    send_response = (
        await client.post(
            f"/api/v1/assistant/conversations/{conversation['id']}/messages",
            headers=headers,
            json={"text": "Hi there"},
        )
    ).json()
    message_id = send_response["message"]["id"]

    rated = await client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages/{message_id}/rate",
        headers=headers,
        json={"rating": "down"},
    )
    assert rated.status_code == 200
    assert rated.json()["tool_call"]["rating"] == "down"


async def test_suggested_prompts_endpoint_returns_a_fallback_for_a_fresh_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/assistant/suggested-prompts", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["prompts"]) > 0
