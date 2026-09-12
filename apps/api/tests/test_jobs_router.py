from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.queue import enqueue
from app.models.user import User


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def test_get_job_status_returns_queued_job(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    from sqlalchemy import select

    user = (
        await db_session.execute(select(User).where(User.email == registered_user["email"]))
    ).scalar_one()
    job = await enqueue(db_session, job_type="noop", payload={}, user_id=user.id)

    token = await _access_token(client, registered_user)
    response = await client.get(
        f"/api/v1/jobs/{job.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["progress_percent"] == 0
    assert body["attempts"] == 0


async def test_get_job_status_404s_for_another_users_job(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    other = User(email="someone-else@example.com", full_name="Someone Else")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    job = await enqueue(db_session, job_type="noop", payload={}, user_id=other.id)

    token = await _access_token(client, registered_user)
    response = await client.get(
        f"/api/v1/jobs/{job.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


async def test_get_job_status_404s_for_nonexistent_job(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get(
        f"/api/v1/jobs/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


async def test_get_job_status_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/jobs/{uuid.uuid4()}")
    assert response.status_code == 401
