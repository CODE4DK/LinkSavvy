from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_score_snapshot import GrowthScoreSnapshot
from app.models.user import User


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_history_endpoints_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/growth/scores/history")).status_code == 401
    response = await client.get(
        "/api/v1/growth/before-after", params={"from_date": "2026-01-01", "to_date": "2026-02-01"}
    )
    assert response.status_code == 401


async def test_score_history_returns_recorded_snapshots(
    client: AsyncClient, registered_user: dict[str, str], db_session: AsyncSession
) -> None:
    headers = await _auth_headers(client, registered_user)
    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()

    today = datetime.now(UTC).date()
    db_session.add(
        GrowthScoreSnapshot(
            user_id=user.id,
            score_type="visibility",
            value=55,
            status="ok",
            scoring_version="2026.1",
            snapshot_date=today,
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/growth/scores/history", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"health", "visibility", "consistency", "personal_branding"}
    assert body["visibility"] == [{"snapshot_date": today.isoformat(), "value": 55}]
    assert body["health"] == []


async def test_before_after_rejects_a_reversed_range(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    today = datetime.now(UTC).date()
    response = await client.get(
        "/api/v1/growth/before-after",
        headers=headers,
        params={"from_date": today.isoformat(), "to_date": (today - timedelta(days=1)).isoformat()},
    )
    assert response.status_code == 422


async def test_before_after_returns_empty_shape_with_no_activity(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    today = datetime.now(UTC).date()
    response = await client.get(
        "/api/v1/growth/before-after",
        headers=headers,
        params={
            "from_date": (today - timedelta(days=30)).isoformat(),
            "to_date": today.isoformat(),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["score_deltas"]) == 4
    assert body["tool_runs"] == []
    assert body["profile_edits"] == []
