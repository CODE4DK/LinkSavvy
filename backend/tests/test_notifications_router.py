from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.notifications.unsubscribe import make_unsubscribe_token


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_notification_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/notifications")).status_code == 401
    assert (await client.get("/api/v1/notifications/preferences")).status_code == 401


async def test_list_notifications_is_empty_for_a_new_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["unread_count"] == 0


async def test_preferences_default_grid_includes_every_type(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/notifications/preferences", headers=headers)
    assert response.status_code == 200
    rows = response.json()["preferences"]
    assert any(
        row["type"] == "product.update" and row["channel"] == "email" and not row["enabled"]
        for row in rows
    )


async def test_set_preference_round_trips(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.put(
        "/api/v1/notifications/preferences",
        headers=headers,
        json={"channel": "email", "type": "content.reminder", "enabled": False},
    )
    assert response.status_code == 200
    rows = response.json()["preferences"]
    row = next(r for r in rows if r["type"] == "content.reminder" and r["channel"] == "email")
    assert row["enabled"] is False


async def test_unsubscribe_link_disables_email_for_that_type(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    me = await client.get("/api/v1/me", headers=headers)
    user_id = me.json()["user"]["id"]

    token = make_unsubscribe_token(
        user_id=uuid.UUID(user_id), notification_type="growth.weekly_report"
    )
    response = await client.get(f"/api/v1/notifications/unsubscribe?token={token}")
    assert response.status_code == 200
    assert "Unsubscribed" in response.text

    prefs = await client.get("/api/v1/notifications/preferences", headers=headers)
    row = next(
        r
        for r in prefs.json()["preferences"]
        if r["type"] == "growth.weekly_report" and r["channel"] == "email"
    )
    assert row["enabled"] is False


async def test_unsubscribe_rejects_a_bad_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/notifications/unsubscribe?token=garbage")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
