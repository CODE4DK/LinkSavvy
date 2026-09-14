"""Shared fixtures for category-audit tests: a real User row (needed for
the AI gateway's quota checks) and small ProfileSnapshot builders covering
the "rich" and "confirmed empty" cases each category needs to exercise
its skip/partial/ok paths honestly."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.context import AuditContext, RoleKeywords
from app.models.user import User
from app.profiles.completeness import compute_completeness
from app.profiles.schema import Experience, Identity, Metrics, ProfileSnapshot, ProfileSource, Skill

SAMPLE_ROLE_KEYWORDS = RoleKeywords(
    keywords=["distributed systems", "microservices", "Kubernetes", "API design", "Python"],
    must_have_skills=["Python", "Distributed Systems", "API Design", "Kubernetes", "SQL"],
)


@pytest_asyncio.fixture
async def audit_user(db_session: AsyncSession) -> User:
    user = User(email=f"audit-cat-{uuid.uuid4()}@example.com", full_name="Category Tester")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def rich_snapshot() -> ProfileSnapshot:
    """A profile with strong data in every section -- matches
    SAMPLE_ROLE_KEYWORDS exactly for full-overlap test cases."""
    return ProfileSnapshot(
        source=ProfileSource.MANUAL,
        captured_at=datetime.now(UTC),
        identity=Identity(
            full_name="Jamie Rivera",
            headline="Senior Backend Engineer specialising in distributed systems at scale",
            custom_url="jamierivera",
            industry="Software Development",
            location="Austin, TX",
        ),
        about=(
            "I build reliable backend systems for high-growth startups. "
            "Over the last eight years I've led teams shipping distributed "
            "systems that serve millions of requests a day. Feel free to "
            "reach out if you'd like to talk shop."
        ),
        experiences=[
            Experience(
                company="Acme Corp",
                title="Senior Backend Engineer",
                is_current=True,
                bullets=[
                    "Cut API latency by 40% by redesigning the caching layer",
                    "Led migration of monolith to microservices for 12 engineers",
                    "Mentored 3 junior engineers to promotion",
                ],
                skills=["Python", "Kubernetes"],
            )
        ],
        skills=[
            Skill(name="Python"),
            Skill(name="Distributed Systems"),
            Skill(name="API Design"),
            Skill(name="Kubernetes"),
            Skill(name="SQL"),
        ],
        metrics=Metrics(connections=550, followers=200, recommendations_received=6),
    )


def partial_skills_snapshot() -> ProfileSnapshot:
    """rich_snapshot but with only 2 of the 5 must-have skills listed."""
    return rich_snapshot().model_copy(update={"skills": [Skill(name="Python"), Skill(name="SQL")]})


def empty_snapshot() -> ProfileSnapshot:
    """Nothing known at all -- every optional field left at its `None`
    ("don't know") default."""
    return ProfileSnapshot(source=ProfileSource.MANUAL, captured_at=datetime.now(UTC))


def make_context(
    *,
    user: User,
    db: AsyncSession,
    snapshot: ProfileSnapshot,
    target_role: str | None = "Staff Backend Engineer",
    target_role_is_assumed: bool = False,
    role_keywords: RoleKeywords | None = None,
    content_history: list[str] | None = None,
) -> AuditContext:
    return AuditContext(
        user=user,
        db=db,
        snapshot=snapshot,
        completeness=compute_completeness(snapshot),
        correlation_id=str(uuid.uuid4()),
        content_history=content_history,
        target_role=target_role,
        target_role_is_assumed=target_role_is_assumed,
        role_keywords=role_keywords,
    )
