"""Profile category: reuses Phase 2's completeness score, judges
headline, About, and experience writing quality with a single AI call,
and computes skills coverage against the target role deterministically
from the shared role_keywords answer."""

from __future__ import annotations

from typing import Any

from app.audit.context import AuditContext
from app.audit.models import Category, CategoryFinding, CategoryResult, CategoryStatus, Severity
from app.audit.scoring import component_weight, weighted_average

CATEGORY: Category = "profile"

_GAP_SEVERITY: dict[str, Severity] = {
    "high": "critical",
    "medium": "important",
    "low": "opportunity",
}


def _completeness_findings(ctx: AuditContext) -> list[CategoryFinding]:
    findings: list[CategoryFinding] = []
    for gap in ctx.completeness.gaps:
        findings.append(
            CategoryFinding(
                code=f"profile.completeness.{gap.code}",
                severity=_GAP_SEVERITY.get(gap.severity, "opportunity"),
                title=gap.message,
                evidence={"section": gap.section, "fix_hint": gap.fix_hint},
                deterministic=True,
            )
        )
    return findings


def _experience_bullets(ctx: AuditContext) -> str:
    lines: list[str] = []
    for experience in ctx.snapshot.experiences or []:
        for bullet in experience.bullets or []:
            lines.append(f"- {bullet}")
    return "\n".join(lines) if lines else "(not provided)"


def _skills_coverage(ctx: AuditContext) -> int | None:
    if ctx.role_keywords is None or not ctx.role_keywords.must_have_skills:
        return None
    if ctx.snapshot.skills is None:
        return None
    user_skills = {skill.name.strip().lower() for skill in ctx.snapshot.skills if skill.name}
    matched = [s for s in ctx.role_keywords.must_have_skills if s.strip().lower() in user_skills]
    return round(100 * len(matched) / len(ctx.role_keywords.must_have_skills))


async def run(ctx: AuditContext) -> CategoryResult:
    findings = _completeness_findings(ctx)
    inputs_available: dict[str, Any] = {
        "headline": bool(ctx.snapshot.identity and ctx.snapshot.identity.headline),
        "about": bool(ctx.snapshot.about),
        "experiences": bool(ctx.snapshot.experiences),
        "target_role": bool(ctx.target_role),
        "role_keywords": ctx.role_keywords is not None,
        "skills": ctx.snapshot.skills is not None,
    }

    headline = (
        ctx.snapshot.identity.headline if ctx.snapshot.identity else None
    ) or "(not provided)"
    about = ctx.snapshot.about or "(not provided)"
    experience_bullets = _experience_bullets(ctx)

    quality_result = await ctx.run_prompt(
        "audit.profile_quality.v1",
        {"headline": headline, "about": about, "experience_bullets": experience_bullets},
    )
    assert quality_result.parsed is not None
    quality: dict[str, Any] = quality_result.parsed
    for section in ("headline", "about", "experience"):
        section_data = quality[section]
        for issue in section_data.get("issues", []):
            findings.append(
                CategoryFinding(
                    code=f"profile.{section}_quality_issue",
                    severity="important",
                    title=issue,
                    evidence={"section": section, "score": section_data["score"]},
                    deterministic=False,
                )
            )

    skills_coverage_score = _skills_coverage(ctx)
    if skills_coverage_score is None:
        findings.append(
            CategoryFinding(
                code="profile.no_skills_coverage_context",
                severity="opportunity",
                title="Set a target role to see how your skills stack up",
                evidence={"unlock": "Set a target role to unlock skills-coverage scoring."},
                deterministic=True,
            )
        )

    score = weighted_average(
        {
            "completeness": ctx.completeness.score,
            "headline_quality": quality["headline"]["score"],
            "about_quality": quality["about"]["score"],
            "experience_quality": quality["experience"]["score"],
            "skills_coverage": skills_coverage_score,
        },
        {
            "completeness": component_weight(CATEGORY, "completeness"),
            "headline_quality": component_weight(CATEGORY, "headline_quality"),
            "about_quality": component_weight(CATEGORY, "about_quality"),
            "experience_quality": component_weight(CATEGORY, "experience_quality"),
            "skills_coverage": component_weight(CATEGORY, "skills_coverage"),
        },
    )

    status: CategoryStatus = "ok" if skills_coverage_score is not None else "partial"
    return CategoryResult(
        category=CATEGORY,
        status=status,
        score=score,
        inputs_available=inputs_available,
        detail={"quality": quality},
        findings=findings,
    )
