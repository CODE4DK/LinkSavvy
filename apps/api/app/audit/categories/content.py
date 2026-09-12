"""Content category: posting readiness/consistency from user-supplied
content history, and content opportunities seeded from the user's
experience and skills. There's no ingestion path for post history yet
(that's Content Hub's job, a later phase) -- `ctx.content_history` is
realistically always `None` today, so this category skips that half
gracefully rather than guessing, while opportunity-seeding still works
from profile data alone.
"""

from __future__ import annotations

from typing import Any

from app.audit.context import AuditContext
from app.audit.models import Category, CategoryFinding, CategoryResult, CategoryStatus
from app.audit.scoring import component_weight, weighted_average

CATEGORY: Category = "content"


def _content_opportunities(ctx: AuditContext) -> tuple[list[CategoryFinding], int | None]:
    skills = [skill.name for skill in (ctx.snapshot.skills or []) if skill.name][:5]
    if not skills:
        return [], None
    findings = [
        CategoryFinding(
            code="content.opportunity_from_skills",
            severity="opportunity",
            title=f"Share a post about your experience with {skills[0]}",
            evidence={"skills": skills},
            deterministic=True,
        )
    ]
    # More listed skills means more raw material for content ideas.
    score = min(100, len(skills) * 20)
    return findings, score


async def run(ctx: AuditContext) -> CategoryResult:
    findings: list[CategoryFinding] = []
    inputs_available: dict[str, Any] = {
        "content_history": bool(ctx.content_history),
        "skills": bool(ctx.snapshot.skills),
    }

    posting_readiness_score: int | None = None
    if ctx.content_history:
        posting_readiness_score = min(100, len(ctx.content_history) * 10)
    else:
        findings.append(
            CategoryFinding(
                code="content.no_history_supplied",
                severity="opportunity",
                title="We can't assess your posting consistency yet",
                evidence={
                    "content_history_count": 0,
                    "unlock": "Paste or upload some of your recent posts to unlock this check.",
                },
                deterministic=True,
            )
        )

    opportunity_findings, opportunity_score = _content_opportunities(ctx)
    findings.extend(opportunity_findings)

    score = weighted_average(
        {"posting_readiness": posting_readiness_score, "content_opportunities": opportunity_score},
        {
            "posting_readiness": component_weight(CATEGORY, "posting_readiness"),
            "content_opportunities": component_weight(CATEGORY, "content_opportunities"),
        },
    )

    if score is None:
        return CategoryResult(
            category=CATEGORY,
            status="skipped",
            score=None,
            inputs_available={
                **inputs_available,
                "unlock": (
                    "Paste or upload some of your recent posts, or add skills to your "
                    "profile, to unlock this category."
                ),
            },
            detail={},
            findings=findings,
        )

    status: CategoryStatus = "ok" if ctx.content_history else "partial"
    return CategoryResult(
        category=CATEGORY,
        status=status,
        score=score,
        inputs_available=inputs_available,
        detail={},
        findings=findings,
    )
