from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit import job_handler  # noqa: F401 -- registers the "audit" job handler
from app.jobs.worker import run_once
from app.models.audit import Audit
from app.models.feature_flag import FeatureFlag
from app.models.job import Job
from app.models.score_history import ScoreHistory
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot

from .audit.categories.conftest import rich_snapshot


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _get_user(db: AsyncSession, email: str) -> User:
    return (await db.execute(select(User).where(User.email == email))).scalar_one()


async def _set_flag(db: AsyncSession, *, key: str, enabled: bool) -> None:
    flag = (await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))).scalar_one()
    flag.enabled_globally = enabled
    await db.commit()


async def _auth_headers(
    client: AsyncClient, db: AsyncSession, registered_user: dict[str, str]
) -> dict[str, str]:
    await _set_flag(db, key="audit", enabled=True)
    token = await _access_token(client, registered_user)
    return {"Authorization": f"Bearer {token}"}


async def test_start_audit_requires_the_audit_flag(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.post(
        "/api/v1/audits", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


async def test_start_audit_requires_an_active_snapshot(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    response = await client.post("/api/v1/audits", json={}, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_full_audit_run_via_worker_then_read_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    registered_user: dict[str, str],
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    user = await _get_user(db_session, registered_user["email"])
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    start = await client.post(
        "/api/v1/audits", json={"target_role": "Staff Backend Engineer"}, headers=headers
    )
    assert start.status_code == 202
    job_id = start.json()["job_id"]

    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True

    job_status = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert job_status.status_code == 200
    assert job_status.json()["status"] == "succeeded"
    assert job_status.json()["progress_percent"] == 100

    latest = await client.get("/api/v1/audits/latest", headers=headers)
    assert latest.status_code == 200
    body = latest.json()
    assert body["status"] in ("completed", "completed_with_errors")
    assert body["overall_score"] is not None
    assert {c["category"] for c in body["categories"]} == {
        "profile",
        "content",
        "engagement",
        "career",
        "visibility",
    }

    by_id = await client.get(f"/api/v1/audits/{body['id']}", headers=headers)
    assert by_id.status_code == 200
    assert by_id.json()["id"] == body["id"]

    history = await client.get("/api/v1/scores/history", headers=headers)
    assert history.status_code == 200
    history_body = history.json()
    assert history_body["range"] == "90d"
    assert len(history_body["points"]) == 1
    assert history_body["points"][0]["overall"] == body["overall_score"]

    recs = await client.get("/api/v1/recommendations", headers=headers)
    assert recs.status_code == 200
    rec_items = recs.json()["items"]
    assert len(rec_items) > 0
    assert [r["priority"] for r in rec_items] == sorted(r["priority"] for r in rec_items)

    rec_id = rec_items[0]["id"]
    patched = await client.patch(
        f"/api/v1/recommendations/{rec_id}", json={"status": "done"}, headers=headers
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "done"
    assert patched.json()["completed_at"] is not None

    open_only = await client.get("/api/v1/recommendations?status=open", headers=headers)
    assert rec_id not in [r["id"] for r in open_only.json()["items"]]


async def test_start_audit_rejects_when_a_run_is_already_in_flight(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    user = await _get_user(db_session, registered_user["email"])
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    db_session.add(Job(user_id=user.id, type="audit", payload={}, scheduled_for=datetime.now(UTC)))
    await db_session.commit()

    response = await client.post("/api/v1/audits", json={}, headers=headers)
    assert response.status_code == 429
    assert "job_id" in response.json()["error"]["details"]


async def test_start_audit_respects_the_manual_cooldown(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    user = await _get_user(db_session, registered_user["email"])
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    db_session.add(
        Audit(
            user_id=user.id,
            status="completed",
            scoring_version="2026.1",
            trigger="manual",
        )
    )
    await db_session.commit()

    response = await client.post("/api/v1/audits", json={}, headers=headers)
    assert response.status_code == 429
    assert "retry_after_seconds" in response.json()["error"]["details"]


async def test_get_audit_not_owned_returns_not_found(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    other_user = User(email=f"other-{uuid.uuid4()}@example.com", full_name="Other")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    other_audit = Audit(
        user_id=other_user.id, status="completed", scoring_version="2026.1", trigger="manual"
    )
    db_session.add(other_audit)
    await db_session.commit()
    await db_session.refresh(other_audit)

    response = await client.get(f"/api/v1/audits/{other_audit.id}", headers=headers)
    assert response.status_code == 404


async def test_score_history_rejects_a_malformed_range(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    response = await client.get("/api/v1/scores/history?range=notaduration", headers=headers)
    assert response.status_code == 422


async def test_score_history_excludes_points_outside_the_range(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, db_session, registered_user)
    user = await _get_user(db_session, registered_user["email"])
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    db_session.add(
        ScoreHistory(
            user_id=user.id,
            audit_id=audit.id,
            scoring_version="2026.1",
            overall=70,
            profile=70,
            content=None,
            engagement=None,
            career=None,
            visibility=None,
            recorded_at=datetime.now(UTC) - timedelta(days=200),
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/scores/history?range=90d", headers=headers)
    assert response.status_code == 200
    assert response.json()["points"] == []
