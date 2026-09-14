from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit, AuditCategoryResult, AuditFinding
from app.models.recommendation import Recommendation
from app.models.score_history import ScoreHistory
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"audit-model-{uuid.uuid4()}@example.com", full_name="Audit Model Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_audit_round_trip_with_category_results_and_findings(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="pending", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    result = AuditCategoryResult(
        audit_id=audit.id,
        category="profile",
        score=72,
        status="ok",
        inputs_available={"headline": True},
        detail={},
    )
    db_session.add(result)

    finding = AuditFinding(
        audit_id=audit.id,
        category="profile",
        code="headline_too_short",
        severity="important",
        title="Headline is too short",
        evidence={"headline": "Engineer", "length": 8},
        deterministic=True,
    )
    db_session.add(finding)
    await db_session.commit()

    reloaded = (
        await db_session.execute(
            select(AuditCategoryResult).where(AuditCategoryResult.audit_id == audit.id)
        )
    ).scalar_one()
    assert reloaded.category == "profile"
    assert reloaded.score == 72

    findings = (
        (await db_session.execute(select(AuditFinding).where(AuditFinding.audit_id == audit.id)))
        .scalars()
        .all()
    )
    assert len(findings) == 1
    assert findings[0].evidence == {"headline": "Engineer", "length": 8}


async def test_audit_category_result_unique_per_audit_and_category(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="pending", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    db_session.add(
        AuditCategoryResult(
            audit_id=audit.id, category="profile", status="ok", inputs_available={}, detail={}
        )
    )
    await db_session.commit()

    db_session.add(
        AuditCategoryResult(
            audit_id=audit.id, category="profile", status="ok", inputs_available={}, detail={}
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


def test_audit_children_are_configured_to_cascade_on_delete() -> None:
    """SQLite (used by this test suite) doesn't enforce foreign keys by
    default, so a real DELETE-cascades-to-children run isn't meaningful
    here -- this asserts the schema itself declares ON DELETE CASCADE,
    which is what MySQL (the real database) actually enforces."""
    for table, column in (
        (AuditCategoryResult.__table__, "audit_id"),
        (AuditFinding.__table__, "audit_id"),
        (Recommendation.__table__, "audit_id"),
        (ScoreHistory.__table__, "audit_id"),
    ):
        foreign_keys = list(table.c[column].foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].ondelete == "CASCADE"


async def test_recommendation_round_trip(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    rec = Recommendation(
        audit_id=audit.id,
        user_id=user.id,
        category="profile",
        priority=1,
        title="Sharpen your headline",
        why="Your headline is short and doesn't mention your specialty.",
        action_label="Fix headline",
        action_route="/profile",
        action_tool_id=None,
        estimated_impact_points=8,
    )
    db_session.add(rec)
    await db_session.commit()
    await db_session.refresh(rec)
    assert rec.status == "open"
    assert rec.completed_at is None


async def test_score_history_round_trip(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    audit = Audit(user_id=user.id, status="completed", scoring_version="2026.1", trigger="manual")
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    entry = ScoreHistory(
        user_id=user.id,
        audit_id=audit.id,
        scoring_version="2026.1",
        overall=68,
        profile=72,
        content=None,
        engagement=55,
        career=None,
        visibility=80,
        recorded_at=datetime.now(UTC),
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    assert entry.content is None
    assert entry.overall == 68
