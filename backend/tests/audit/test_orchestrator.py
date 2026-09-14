from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit.categories import content
from app.audit.models import CategoryResult
from app.audit.orchestrator import run_audit
from app.models.audit import AuditCategoryResult, AuditFinding
from app.models.recommendation import Recommendation
from app.models.score_history import ScoreHistory
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot

from .categories.conftest import rich_snapshot


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"orchestrator-{uuid.uuid4()}@example.com", full_name="Orchestrator Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_run_audit_persists_full_result_and_score_history(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    snapshot_row = await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    audit = await run_audit(
        user=user,
        db=db_session,
        snapshot_row=snapshot_row,
        trigger="manual",
        session_factory=db_sessionmaker,
    )

    assert audit.status == "completed"
    assert audit.overall_score is not None
    assert audit.profile_snapshot_id == snapshot_row.id
    assert audit.duration_ms is not None
    assert audit.completed_at is not None

    category_results = (
        (
            await db_session.execute(
                select(AuditCategoryResult).where(AuditCategoryResult.audit_id == audit.id)
            )
        )
        .scalars()
        .all()
    )
    assert {r.category for r in category_results} == {
        "profile",
        "content",
        "engagement",
        "career",
        "visibility",
    }

    findings = (
        (await db_session.execute(select(AuditFinding).where(AuditFinding.audit_id == audit.id)))
        .scalars()
        .all()
    )
    assert len(findings) > 0

    score_history = (
        await db_session.execute(select(ScoreHistory).where(ScoreHistory.audit_id == audit.id))
    ).scalar_one()
    assert score_history.overall == audit.overall_score

    recommendations = (
        (
            await db_session.execute(
                select(Recommendation).where(Recommendation.audit_id == audit.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(recommendations) > 0
    priorities = sorted(r.priority for r in recommendations)
    assert priorities == list(range(1, len(recommendations) + 1))


async def test_run_audit_marks_completed_with_errors_when_a_category_fails(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session)
    snapshot_row = await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    async def _boom(ctx: object) -> CategoryResult:
        raise RuntimeError("category exploded")

    monkeypatch.setattr(content, "run", _boom)

    audit = await run_audit(
        user=user,
        db=db_session,
        snapshot_row=snapshot_row,
        trigger="manual",
        session_factory=db_sessionmaker,
    )

    assert audit.status == "completed_with_errors"
    assert audit.overall_score is not None  # renormalized over the 4 surviving categories

    content_result = (
        await db_session.execute(
            select(AuditCategoryResult).where(
                AuditCategoryResult.audit_id == audit.id,
                AuditCategoryResult.category == "content",
            )
        )
    ).scalar_one()
    assert content_result.status == "failed"
    assert content_result.score is None


async def test_run_audit_uses_supplied_target_role_over_inference(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    snapshot_row = await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    audit = await run_audit(
        user=user,
        db=db_session,
        snapshot_row=snapshot_row,
        trigger="manual",
        target_role="Staff Platform Engineer",
        session_factory=db_sessionmaker,
    )
    career_result = (
        await db_session.execute(
            select(AuditCategoryResult).where(
                AuditCategoryResult.audit_id == audit.id, AuditCategoryResult.category == "career"
            )
        )
    ).scalar_one()
    assert career_result.detail.get("target_role") == "Staff Platform Engineer"
    assert career_result.detail.get("target_role_is_assumed") is False
