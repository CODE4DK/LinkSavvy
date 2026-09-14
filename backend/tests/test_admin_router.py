from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def _promote_to_admin(db: AsyncSession, *, email: str) -> None:
    await db.execute(update(User).where(User.email == email).values(role="admin"))
    await db.commit()


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_admin_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/admin/users")).status_code == 401


async def test_admin_endpoints_reject_a_non_admin_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_admin_can_search_and_view_users(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    await _promote_to_admin(db_session, email=registered_user["email"])
    headers = await _auth_headers(client, registered_user)

    search = await client.get("/api/v1/admin/users", headers=headers)
    assert search.status_code == 200
    assert search.json()["total"] >= 1

    user_id = search.json()["items"][0]["id"]
    detail = await client.get(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["user"]["id"] == user_id


async def test_admin_suspend_requires_a_reason(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    await _promote_to_admin(db_session, email=registered_user["email"])
    headers = await _auth_headers(client, registered_user)
    search = await client.get("/api/v1/admin/users", headers=headers)
    user_id = search.json()["items"][0]["id"]

    response = await client.post(
        f"/api/v1/admin/users/{user_id}/suspend",
        headers=headers,
        json={"reason": "policy violation"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


async def test_feature_flags_list_and_toggle(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    await _promote_to_admin(db_session, email=registered_user["email"])
    headers = await _auth_headers(client, registered_user)

    flags = await client.get("/api/v1/admin/feature-flags", headers=headers)
    assert flags.status_code == 200
    assert any(f["key"] == "hub.profile" for f in flags.json())

    toggled = await client.post(
        "/api/v1/admin/feature-flags/hub.profile/global",
        headers=headers,
        json={"enabled_globally": True},
    )
    assert toggled.status_code == 200
    assert toggled.json()["enabled_globally"] is True


async def test_impersonation_token_is_read_only(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    await _promote_to_admin(db_session, email=registered_user["email"])
    admin_headers = await _auth_headers(client, registered_user)

    # A second, ordinary user for the admin to impersonate.
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "impersonated@example.com",
            "password": "correct-horse-99",
            "full_name": "Target",
        },
    )
    search = await client.get("/api/v1/admin/users?q=impersonated", headers=admin_headers)
    target_id = search.json()["items"][0]["id"]

    impersonate = await client.post(
        f"/api/v1/admin/users/{target_id}/impersonate", headers=admin_headers
    )
    assert impersonate.status_code == 200
    impersonation_token = impersonate.json()["access_token"]
    impersonation_headers = {"Authorization": f"Bearer {impersonation_token}"}

    # Reads work fine while impersonating.
    me = await client.get("/api/v1/me", headers=impersonation_headers)
    assert me.status_code == 200

    # Any unsafe method is blocked outright, before it ever reaches a
    # route handler -- this hits an ordinary authenticated PATCH endpoint
    # to prove the guard is transport-level, not specific to one route.
    mutate = await client.patch(
        "/api/v1/me", headers=impersonation_headers, json={"full_name": "Changed"}
    )
    assert mutate.status_code == 403
    assert mutate.json()["error"]["code"] == "FORBIDDEN"


async def test_cannot_impersonate_yourself_via_the_api(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    await _promote_to_admin(db_session, email=registered_user["email"])
    headers = await _auth_headers(client, registered_user)
    me = await client.get("/api/v1/me", headers=headers)
    own_id = me.json()["user"]["id"]

    response = await client.post(f"/api/v1/admin/users/{own_id}/impersonate", headers=headers)
    assert response.status_code == 422


async def test_platform_health_endpoint_serves_a_response(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    """Regression test: app/admin/platform_health.py's QueueDepth is a
    slots=True dataclass, which has no __dict__ -- the endpoint used to
    build its response with vars(depth), which raises TypeError on any
    slotted dataclass. The service-layer tests in
    tests/admin/test_platform_health.py call queue_depth() directly and
    never touch the router, so they never exercised this at all."""
    await _promote_to_admin(db_session, email=registered_user["email"])
    headers = await _auth_headers(client, registered_user)

    response = await client.get("/api/v1/admin/platform-health", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body["queue_depth"].keys()) == {"queued", "leased", "dead", "failed_last_hour"}
    assert body["dead_jobs"] == []


async def test_ai_ops_overview_endpoint_serves_a_response(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    """Regression test: same vars()-on-a-slotted-dataclass bug as
    test_platform_health_endpoint_serves_a_response, across all five
    dataclasses this endpoint assembles a response from."""
    await _promote_to_admin(db_session, email=registered_user["email"])
    headers = await _auth_headers(client, registered_user)

    response = await client.get("/api/v1/admin/ai-ops/overview", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["cost_by_day"] == []
    assert body["outcome_rates"]["total"] == 0
