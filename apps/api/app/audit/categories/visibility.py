"""Visibility category: keyword coverage and profile metadata that make a
profile easier to find in LinkedIn's own search and in a recruiter's
skim -- never anything about gaming an external ranking algorithm."""

from __future__ import annotations

import re
from typing import Any

from app.audit.context import AuditContext
from app.audit.models import Category, CategoryFinding, CategoryResult, CategoryStatus
from app.audit.scoring import component_weight, weighted_average

CATEGORY: Category = "visibility"


def _text_contains_keyword(text: str, keyword: str) -> bool:
    return re.search(re.escape(keyword), text, re.IGNORECASE) is not None


def _keyword_density(ctx: AuditContext) -> tuple[int | None, list[str]]:
    if ctx.role_keywords is None or not ctx.role_keywords.keywords:
        return None, []
    headline = (ctx.snapshot.identity.headline if ctx.snapshot.identity else None) or ""
    about = ctx.snapshot.about or ""
    combined = f"{headline}\n{about}"
    present = [kw for kw in ctx.role_keywords.keywords if _text_contains_keyword(combined, kw)]
    return round(100 * len(present) / len(ctx.role_keywords.keywords)), present


def _custom_url(ctx: AuditContext) -> tuple[int | None, list[CategoryFinding]]:
    custom_url = ctx.snapshot.identity.custom_url if ctx.snapshot.identity else None
    if custom_url is None:
        return None, []
    if custom_url:
        return 100, []
    return 0, [
        CategoryFinding(
            code="visibility.no_custom_url",
            severity="opportunity",
            title="Claim a custom LinkedIn URL so your profile is easier to find and share",
            evidence={"custom_url": custom_url},
            deterministic=True,
        )
    ]


def _profile_metadata(ctx: AuditContext) -> tuple[int | None, list[CategoryFinding]]:
    identity = ctx.snapshot.identity
    if identity is None:
        return None, []
    sub_scores: list[int] = []
    findings: list[CategoryFinding] = []
    if identity.industry is not None:
        sub_scores.append(100 if identity.industry else 0)
        if not identity.industry:
            findings.append(
                CategoryFinding(
                    code="visibility.no_industry",
                    severity="opportunity",
                    title="Set your industry so recruiters searching by industry can find you",
                    evidence={"industry": identity.industry},
                    deterministic=True,
                )
            )
    if identity.location is not None:
        sub_scores.append(100 if identity.location else 0)
        if not identity.location:
            findings.append(
                CategoryFinding(
                    code="visibility.no_location",
                    severity="opportunity",
                    title="Set your location so recruiters searching by location can find you",
                    evidence={"location": identity.location},
                    deterministic=True,
                )
            )
    if not sub_scores:
        return None, findings
    return round(sum(sub_scores) / len(sub_scores)), findings


def _skill_alignment(ctx: AuditContext) -> int | None:
    if ctx.role_keywords is None or not ctx.role_keywords.must_have_skills:
        return None
    if ctx.snapshot.skills is None:
        return None
    user_skills = {skill.name.strip().lower() for skill in ctx.snapshot.skills if skill.name}
    matched = [s for s in ctx.role_keywords.must_have_skills if s.strip().lower() in user_skills]
    return round(100 * len(matched) / len(ctx.role_keywords.must_have_skills))


def _brand_consistency(ctx: AuditContext) -> tuple[int | None, list[CategoryFinding]]:
    if ctx.role_keywords is None or not ctx.role_keywords.keywords:
        return None, []
    headline = ctx.snapshot.identity.headline if ctx.snapshot.identity else None
    about = ctx.snapshot.about
    if headline is None and about is None:
        return None, []
    headline_has_keyword = bool(headline) and any(
        _text_contains_keyword(headline or "", kw) for kw in ctx.role_keywords.keywords
    )
    about_has_keyword = bool(about) and any(
        _text_contains_keyword(about or "", kw) for kw in ctx.role_keywords.keywords
    )
    score = round(100 * (int(headline_has_keyword) + int(about_has_keyword)) / 2)
    findings: list[CategoryFinding] = []
    if not headline_has_keyword or not about_has_keyword:
        findings.append(
            CategoryFinding(
                code="visibility.inconsistent_brand_vocabulary",
                severity="opportunity",
                title="Use consistent, role-relevant language across your headline and About section",
                evidence={
                    "headline_has_target_keyword": headline_has_keyword,
                    "about_has_target_keyword": about_has_keyword,
                    "target_role": ctx.target_role,
                },
                deterministic=True,
            )
        )
    return score, findings


async def run(ctx: AuditContext) -> CategoryResult:
    findings: list[CategoryFinding] = []
    inputs_available: dict[str, Any] = {
        "target_role": bool(ctx.target_role),
        "role_keywords": ctx.role_keywords is not None,
        "identity": ctx.snapshot.identity is not None,
        "skills": ctx.snapshot.skills is not None,
    }

    keyword_density_score, present_keywords = _keyword_density(ctx)
    if keyword_density_score is None:
        findings.append(
            CategoryFinding(
                code="visibility.no_target_role_for_keywords",
                severity="opportunity",
                title="Tell us the role you're targeting to check keyword coverage",
                evidence={"unlock": "Set a target role to unlock keyword-density scoring."},
                deterministic=True,
            )
        )

    custom_url_score, custom_url_findings = _custom_url(ctx)
    findings.extend(custom_url_findings)

    metadata_score, metadata_findings = _profile_metadata(ctx)
    findings.extend(metadata_findings)

    skill_alignment_score = _skill_alignment(ctx)

    brand_score, brand_findings = _brand_consistency(ctx)
    findings.extend(brand_findings)

    score = weighted_average(
        {
            "keyword_density": keyword_density_score,
            "custom_url": custom_url_score,
            "profile_metadata": metadata_score,
            "skill_alignment": skill_alignment_score,
            "brand_consistency": brand_score,
        },
        {
            "keyword_density": component_weight(CATEGORY, "keyword_density"),
            "custom_url": component_weight(CATEGORY, "custom_url"),
            "profile_metadata": component_weight(CATEGORY, "profile_metadata"),
            "skill_alignment": component_weight(CATEGORY, "skill_alignment"),
            "brand_consistency": component_weight(CATEGORY, "brand_consistency"),
        },
    )

    if score is None:
        return CategoryResult(
            category=CATEGORY,
            status="skipped",
            score=None,
            inputs_available={
                **inputs_available,
                "unlock": "Set a target role and fill in your profile details to unlock visibility scoring.",
            },
            detail={},
            findings=findings,
        )

    all_available = all(
        s is not None
        for s in (
            keyword_density_score,
            custom_url_score,
            metadata_score,
            skill_alignment_score,
            brand_score,
        )
    )
    status: CategoryStatus = "ok" if all_available else "partial"
    return CategoryResult(
        category=CATEGORY,
        status=status,
        score=score,
        inputs_available=inputs_available,
        detail={"matched_keywords": present_keywords},
        findings=findings,
    )
