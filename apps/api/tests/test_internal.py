from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _promote_to_admin(db: AsyncSession, email: str) -> None:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    user.role = "admin"
    await db.commit()


async def test_metrics_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/internal/metrics")
    assert response.status_code == 401


async def test_metrics_denies_non_admin_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get("/internal/metrics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_metrics_returns_data_for_admin(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    await _promote_to_admin(db_session, registered_user["email"])
    token = await _access_token(client, registered_user)
    response = await client.get("/internal/metrics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_invocations"] == 0
    assert body["latency_p50_ms"] is None
    assert body["cost_per_user_per_day_minor"] == {}


async def test_metrics_accepts_window_hours_query_param(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    await _promote_to_admin(db_session, registered_user["email"])
    token = await _access_token(client, registered_user)
    response = await client.get(
        "/internal/metrics?window_hours=1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["window_hours"] == 1
