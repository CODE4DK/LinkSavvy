from __future__ import annotations

from httpx import AsyncClient


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    token = await _access_token(client, creds)
    return {"Authorization": f"Bearer {token}"}


async def test_content_plans_require_auth(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/content-plans", params={"start": "2026-06-01", "end": "2026-06-30"}
    )
    assert response.status_code == 401


async def test_create_list_and_update_plan(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)

    created = await client.post(
        "/api/v1/content-plans",
        headers=headers,
        json={"title": "My idea", "planned_for": "2026-06-05"},
    )
    assert created.status_code == 200
    plan_id = created.json()["id"]
    assert created.json()["status"] == "idea"

    listed = await client.get(
        "/api/v1/content-plans",
        headers=headers,
        params={"start": "2026-06-01", "end": "2026-06-30"},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = await client.patch(
        f"/api/v1/content-plans/{plan_id}", headers=headers, json={"status": "drafted"}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "drafted"


async def test_reschedule_plan(client: AsyncClient, registered_user: dict[str, str]) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post(
        "/api/v1/content-plans", headers=headers, json={"planned_for": "2026-06-05"}
    )
    plan_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/content-plans/{plan_id}/reschedule",
        headers=headers,
        json={"planned_for": "2026-06-20"},
    )
    assert response.status_code == 200
    assert response.json()["planned_for"] == "2026-06-20"


async def test_delete_plan_removes_it_from_listing(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post(
        "/api/v1/content-plans", headers=headers, json={"planned_for": "2026-06-05"}
    )
    plan_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/content-plans/{plan_id}", headers=headers)
    assert deleted.status_code == 204

    listed = await client.get(
        "/api/v1/content-plans",
        headers=headers,
        params={"start": "2026-06-01", "end": "2026-06-30"},
    )
    assert listed.json() == []


async def test_mark_posted_endpoint(client: AsyncClient, registered_user: dict[str, str]) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post(
        "/api/v1/content-plans", headers=headers, json={"planned_for": "2026-06-05"}
    )
    plan_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/content-plans/{plan_id}/mark-posted",
        headers=headers,
        json={
            "linkedin_url": "https://www.linkedin.com/feed/update/urn:li:activity:1",
            "performance": {"impressions": 500},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "posted"
    assert body["performance"]["impressions"] == 500


async def test_recurring_slots_endpoint(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/content-plans/recurring-slots",
        headers=headers,
        json={
            "cadence": {
                "days_of_week": [1, 3],
                "start_date": "2026-06-01",
                "weeks": 2,
            }
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 4


async def test_bulk_schedule_endpoint(client: AsyncClient, registered_user: dict[str, str]) -> None:
    headers = await _auth_headers(client, registered_user)
    idea_one = await client.post(
        "/api/v1/content-plans",
        headers=headers,
        json={"title": "Idea one", "planned_for": "2026-01-01"},
    )
    idea_two = await client.post(
        "/api/v1/content-plans",
        headers=headers,
        json={"title": "Idea two", "planned_for": "2026-01-01"},
    )

    response = await client.post(
        "/api/v1/content-plans/bulk-schedule",
        headers=headers,
        json={
            "cadence": {"days_of_week": [1, 3], "start_date": "2026-06-01", "weeks": 2},
            "plan_ids": [idea_one.json()["id"], idea_two.json()["id"]],
        },
    )
    assert response.status_code == 200
    scheduled = response.json()
    assert len(scheduled) == 2
    assert all(plan["status"] == "scheduled" for plan in scheduled)


async def test_consistency_endpoint_returns_twelve_weeks(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/content-plans/consistency", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 12


async def test_get_plan_404s_for_unknown_id(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get(
        "/api/v1/content-plans/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
