from __future__ import annotations

from httpx import AsyncClient


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    token = await _access_token(client, creds)
    return {"Authorization": f"Bearer {token}"}


async def test_record_performance_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/content-plans/00000000-0000-0000-0000-000000000000/performance",
        json={"impressions": 100},
    )
    assert response.status_code == 401


async def test_record_performance_updates_the_plan(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post(
        "/api/v1/content-plans", headers=headers, json={"planned_for": "2026-06-05"}
    )
    plan_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/content-plans/{plan_id}/performance",
        headers=headers,
        json={"impressions": 1000, "reactions": 50},
    )
    assert response.status_code == 200
    assert response.json()["performance"] == {"impressions": 1000, "reactions": 50}


async def test_performance_summary_reports_insufficient_data(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/content-plans/performance-summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["sufficient_data"] is False
    assert body["total_data_points"] == 0
    assert body["by_content_type"] == []


async def test_performance_summary_reports_medians_once_there_is_enough_data(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    for reactions in [10, 20, 30, 40, 50]:
        created = await client.post(
            "/api/v1/content-plans", headers=headers, json={"planned_for": "2026-06-05"}
        )
        plan_id = created.json()["id"]
        await client.post(
            f"/api/v1/content-plans/{plan_id}/performance",
            headers=headers,
            json={"reactions": reactions},
        )

    response = await client.get("/api/v1/content-plans/performance-summary", headers=headers)
    body = response.json()
    assert body["sufficient_data"] is True
    assert body["total_data_points"] == 5
    assert body["by_content_type"][0]["median_engagement"] == 30.0
