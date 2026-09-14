"""GET /api/v1/dashboard -- the aggregate read backing the Dashboard UI.
The query-count tests exist because this endpoint's whole reason to
exist is avoiding N+1 round trips across audits/scores/recommendations;
a regression there is exactly the kind of thing that's invisible in a
response-shape assertion but shows up immediately in p95 latency.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot

from .audit.categories.conftest import rich_snapshot


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _get_user(db: AsyncSession, email: str) -> User:
    return (await db.execute(select(User).where(User.email == email))).scalar_one()


@contextmanager
def _count_queries() -> Iterator[list[str]]:
    statements: list[str] = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield statements
    finally:
        event.remove(Engine, "before_cursor_execute", before_cursor_execute)


async def test_dashboard_first_time_empty_state(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_first_time"] is True
    assert body["health_score"] is None
    assert body["run_audit"]["reason"] == "no_active_snapshot"
    assert body["run_audit"]["can_run"] is False
    assert body["score_history"]["points"] == []


async def test_dashboard_returns_full_snapshot_after_an_audit(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    from app.audit.orchestrator import run_audit

    user = await _get_user(db_session, registered_user["email"])
    snapshot_row = await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()
    audit = await run_audit(user=user, db=db_session, snapshot_row=snapshot_row, trigger="manual")

    token = await _access_token(client, registered_user)
    response = await client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_first_time"] is False
    assert body["health_score"]["audit_id"] == str(audit.id)
    assert body["health_score"]["overall"] == audit.overall_score
    assert len(body["health_score"]["categories"]) == 5
    assert len(body["score_history"]["points"]) == 1
    assert body["score_history"]["delta"] is None  # only one point so far
    assert len(body["top_recommendations"]) <= 3
    # Just ran a manual audit -- the cooldown should now be active.
    assert body["run_audit"]["reason"] == "cooldown_active"
    assert body["run_audit"]["retry_after_seconds"] is not None


async def test_dashboard_query_count_does_not_grow_with_recommendation_volume(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    from app.audit.orchestrator import run_audit

    user = await _get_user(db_session, registered_user["email"])
    snapshot_row = await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()
    audit = await run_audit(user=user, db=db_session, snapshot_row=snapshot_row, trigger="manual")

    token = await _access_token(client, registered_user)
    headers = {"Authorization": f"Bearer {token}"}

    with _count_queries() as statements_before:
        response_before = await client.get("/api/v1/dashboard", headers=headers)
    assert response_before.status_code == 200
    count_before = len(statements_before)
    assert count_before <= 20

    # Pile on a lot more open recommendations for the same audit -- the
    # aggregate's recommendation fetch is LIMIT-capped, so this should not
    # add a single extra query.
    for i in range(50):
        db_session.add(
            Recommendation(
                audit_id=audit.id,
                user_id=user.id,
                category="profile",
                priority=1000 + i,
                title=f"Extra recommendation {i}",
                why="Synthetic load for the query-count test.",
                action_label="Do it",
                action_route="/profile",
                estimated_impact_points=1,
            )
        )
    await db_session.commit()

    with _count_queries() as statements_after:
        response_after = await client.get("/api/v1/dashboard", headers=headers)
    assert response_after.status_code == 200
    count_after = len(statements_after)

    assert count_after == count_before
    assert len(response_after.json()["top_recommendations"]) == 3


async def test_get_dashboard_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 401
