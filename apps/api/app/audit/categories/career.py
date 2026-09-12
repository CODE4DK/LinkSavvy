"""Career category: role alignment and skill-gap findings, computed
deterministically from the target role's must-have skills (resolved once
by the orchestrator -- see app/audit/role_keywords.py). Resume
cross-referencing has no ingestion path yet (that's Career Hub's job, a
later phase), so that sub-check is always skipped rather than guessed.
"""

from __future__ import annotations

from typing import Any

from app.audit.context import AuditContext
from app.audit.models import Category, CategoryFinding, CategoryResult, Severity
from app.audit.scoring import component_weight, weighted_average

CATEGORY: Category = "career"


def _user_skill_names(ctx: AuditContext) -> set[str] | None:
    if ctx.snapshot.skills is None:
        return None
    return {skill.name.strip().lower() for skill in ctx.snapshot.skills if skill.name}


def _skill_overlap(ctx: AuditContext, user_skills: set[str]) -> tuple[int, list[str], list[str]]:
    must_have = ctx.role_keywords.must_have_skills if ctx.role_keywords else []
    matched = [skill for skill in must_have if skill.strip().lower() in user_skills]
    missing = [skill for skill in must_have if skill.strip().lower() not in user_skills]
    score = round(100 * len(matched) / len(must_have))
    return score, matched, missing


async def run(ctx: AuditContext) -> CategoryResult:
    findings: list[CategoryFinding] = [
        CategoryFinding(
            code="career.no_resume_uploaded",
            severity="opportunity",
            title="Upload a resume to unlock resume cross-reference checks",
            evidence={"unlock": "Upload a resume in the Career Hub to unlock this check."},
            deterministic=True,
        )
    ]
    inputs_available: dict[str, Any] = {
        "resume": False,
        "target_role": bool(ctx.target_role),
        "role_keywords": ctx.role_keywords is not None,
        "skills": ctx.snapshot.skills is not None,
    }

    role_alignment_score: int | None = None
    readiness_score: int | None = None
    matched_skills: list[str] = []

    if ctx.target_role is None:
        findings.append(
            CategoryFinding(
                code="career.no_target_role",
                severity="opportunity",
                title="Tell us the role you're targeting to unlock alignment checks",
                evidence={"unlock": "Set a target role to unlock role-alignment scoring."},
                deterministic=True,
            )
        )
    elif ctx.role_keywords is None or not ctx.role_keywords.must_have_skills:
        findings.append(
            CategoryFinding(
                code="career.no_role_keywords",
                severity="opportunity",
                title="We couldn't resolve expected skills for this target role",
                evidence={"target_role": ctx.target_role},
                deterministic=True,
            )
        )
    else:
        user_skills = _user_skill_names(ctx)
        if user_skills is None:
            findings.append(
                CategoryFinding(
                    code="career.no_skills_listed",
                    severity="opportunity",
                    title="Add skills to your profile to unlock role-alignment scoring",
                    evidence={"unlock": "List your skills to unlock this check."},
                    deterministic=True,
                )
            )
        else:
            overlap_score, matched_skills, missing_skills = _skill_overlap(ctx, user_skills)
            role_alignment_score = overlap_score
            readiness_score = overlap_score
            if missing_skills:
                severity: Severity = (
                    "important"
                    if len(missing_skills) >= len(ctx.role_keywords.must_have_skills) / 2
                    else "opportunity"
                )
                findings.append(
                    CategoryFinding(
                        code="career.missing_target_role_skills",
                        severity=severity,
                        title=f"Add {missing_skills[0]} to your skills to better match {ctx.target_role}",
                        evidence={"target_role": ctx.target_role, "missing_skills": missing_skills},
                        deterministic=True,
                    )
                )

    overall_score = weighted_average(
        {
            "resume_presence": None,
            "role_alignment": role_alignment_score,
            "readiness_gaps": readiness_score,
        },
        {
            "resume_presence": component_weight(CATEGORY, "resume_presence"),
            "role_alignment": component_weight(CATEGORY, "role_alignment"),
            "readiness_gaps": component_weight(CATEGORY, "readiness_gaps"),
        },
    )

    if overall_score is None:
        return CategoryResult(
            category=CATEGORY,
            status="skipped",
            score=None,
            inputs_available={
                **inputs_available,
                "unlock": "Set a target role and list your skills to unlock career scoring.",
            },
            detail={},
            findings=findings,
        )

    return CategoryResult(
        category=CATEGORY,
        status="partial",
        score=overall_score,
        inputs_available=inputs_available,
        detail={
            "matched_skills": matched_skills,
            "target_role": ctx.target_role,
            "target_role_is_assumed": ctx.target_role_is_assumed,
        },
        findings=findings,
    )
