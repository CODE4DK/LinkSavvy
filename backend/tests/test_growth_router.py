from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.weekly_plan import generate_plan_for_user
from app.models.audit import Audit
from app.models.recommendation import Recommendation
from app.models.user import User


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_growth_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/growth/scores")).status_code == 401
    assert (await client.get("/api/v1/growth/plan")).status_code == 401
    assert (await client.get("/api/v1/growth/goal")).status_code == 401


async def test_scores_endpoint_returns_all_four_skipped_for_a_fresh_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/growth/scores", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"health", "visibility", "consistency", "personal_branding"}
    assert body["health"]["status"] == "skipped"
    assert body["visibility"]["status"] == "skipped"


async def test_plan_endpoint_404s_before_any_plan_is_generated(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get("/api/v1/growth/plan", headers=headers)
    assert response.status_code == 404


async def test_plan_endpoint_and_item_completion(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()

    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)
    db_session.add(
        Recommendation(
            audit_id=audit.id,
            user_id=user.id,
            category="profile",
            priority=0,
            title="Sharpen your headline",
            why="It's vague.",
            action_label="Fix headline",
            action_route="/profile",
            estimated_impact_points=8,
            status="open",
        )
    )
    await db_session.commit()

    await generate_plan_for_user(db_session, user=user)

    response = await client.get("/api/v1/growth/plan", headers=headers)
    assert response.status_code == 200
    plan_body = response.json()
    assert len(plan_body["items"]) == 1
    assert plan_body["items"][0]["title"] == "Sharpen your headline"
    assert plan_body["completed_count"] == 0

    patch_response = await client.patch(
        f"/api/v1/growth/plan/{plan_body['id']}/items/0",
        headers=headers,
        json={"completed": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["completed_count"] == 1

    bad_index = await client.patch(
        f"/api/v1/growth/plan/{plan_body['id']}/items/9",
        headers=headers,
        json={"completed": True},
    )
    assert bad_index.status_code == 404


async def test_goal_lifecycle(client: AsyncClient, registered_user: dict[str, str]) -> None:
    headers = await _auth_headers(client, registered_user)

    assert (await client.get("/api/v1/growth/goal", headers=headers)).status_code == 404

    create_response = await client.post(
        "/api/v1/growth/goal",
        headers=headers,
        json={
            "goal_type": "role_change",
            "target_role": "Staff Engineer",
            "target_description": "Move into a staff-level role.",
            "horizon_weeks": 12,
        },
    )
    assert create_response.status_code == 200
    body = create_response.json()
    assert body["status"] == "active"
    assert body["target_role"] == "Staff Engineer"
    assert set(body["baseline_scores"].keys()) == {
        "health",
        "visibility",
        "consistency",
        "personal_branding",
    }

    get_response = await client.get("/api/v1/growth/goal", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]
