"""Engagement category: network signals from profile metrics,
contactability from a claimed custom URL and an About section that
invites contact, and concrete manual engagement ideas from AI. Every
suggestion here must be something the user does themselves by hand --
never automation of the LinkedIn actions themselves (CLAUDE.md's hard
compliance rule)."""

from __future__ import annotations

import re
from typing import Any

from app.audit.context import AuditContext
from app.audit.models import Category, CategoryFinding, CategoryResult, CategoryStatus
from app.audit.scoring import component_weight, weighted_average

CATEGORY: Category = "engagement"

_CTA_PATTERN = re.compile(
    r"reach out|get in touch|let'?s connect|feel free to (message|contact|email)|"
    r"dm me|message me|email me( at)?|connect with me",
    re.IGNORECASE,
)

_CONNECTIONS_TARGET = 500
_FOLLOWERS_TARGET = 500
_RECOMMENDATIONS_TARGET = 5


def _network_signals(ctx: AuditContext) -> tuple[int | None, dict[str, int]]:
    metrics = ctx.snapshot.metrics
    if metrics is None:
        return None, {}
    sub_scores: dict[str, int] = {}
    if metrics.connections is not None:
        sub_scores["connections"] = min(100, round(100 * metrics.connections / _CONNECTIONS_TARGET))
    if metrics.followers is not None:
        sub_scores["followers"] = min(100, round(100 * metrics.followers / _FOLLOWERS_TARGET))
    if metrics.recommendations_received is not None:
        sub_scores["recommendations"] = min(
            100, round(100 * metrics.recommendations_received / _RECOMMENDATIONS_TARGET)
        )
    if not sub_scores:
        return None, {}
    return round(sum(sub_scores.values()) / len(sub_scores)), sub_scores


def _contactability(
    ctx: AuditContext,
) -> tuple[int | None, list[CategoryFinding], dict[str, int]]:
    findings: list[CategoryFinding] = []
    sub_scores: dict[str, int] = {}

    custom_url = ctx.snapshot.identity.custom_url if ctx.snapshot.identity else None
    if custom_url is not None:
        sub_scores["custom_url"] = 100 if custom_url else 0
        if not custom_url:
            findings.append(
                CategoryFinding(
                    code="engagement.no_custom_url",
                    severity="opportunity",
                    title="Claim a custom LinkedIn URL to make your profile easier to share",
                    evidence={"custom_url": custom_url},
                    deterministic=True,
                )
            )

    about = ctx.snapshot.about
    if about is not None:
        has_cta = bool(_CTA_PATTERN.search(about))
        sub_scores["contact_cta"] = 100 if has_cta else 0
        if not has_cta:
            findings.append(
                CategoryFinding(
                    code="engagement.no_contact_cta",
                    severity="opportunity",
                    title="Add a call to action in your About section inviting people to reach out",
                    evidence={"about_length": len(about)},
                    deterministic=True,
                )
            )

    if not sub_scores:
        return None, findings, sub_scores
    return round(sum(sub_scores.values()) / len(sub_scores)), findings, sub_scores


async def run(ctx: AuditContext) -> CategoryResult:
    findings: list[CategoryFinding] = []
    inputs_available: dict[str, Any] = {
        "metrics": ctx.snapshot.metrics is not None,
        "identity": ctx.snapshot.identity is not None,
        "about": ctx.snapshot.about is not None,
    }

    network_score, network_sub_scores = _network_signals(ctx)
    if network_score is None:
        findings.append(
            CategoryFinding(
                code="engagement.no_network_metrics",
                severity="opportunity",
                title="We can't assess your network reach yet",
                evidence={
                    "unlock": (
                        "Connect LinkedIn or enter your connection count manually to "
                        "unlock this check."
                    )
                },
                deterministic=True,
            )
        )

    contactability_score, contact_findings, contact_sub_scores = _contactability(ctx)
    findings.extend(contact_findings)
    if contactability_score is None:
        findings.append(
            CategoryFinding(
                code="engagement.no_contactability_signals",
                severity="opportunity",
                title="We can't assess how contactable your profile is yet",
                evidence={"unlock": "Add a custom URL or an About section to unlock this check."},
                deterministic=True,
            )
        )

    opportunities_score: int | None = None
    opportunities: list[dict[str, str]] = []
    headline = ctx.snapshot.identity.headline if ctx.snapshot.identity else None
    industry = ctx.snapshot.identity.industry if ctx.snapshot.identity else None
    if headline and ctx.target_role:
        result = await ctx.run_prompt(
            "audit.engagement_opportunities.v1",
            {
                "headline": headline,
                "industry": industry or "(not provided)",
                "target_role": ctx.target_role,
            },
        )
        assert result.parsed is not None
        opportunities = result.parsed["opportunities"]
        opportunities_score = 100
        for item in opportunities:
            findings.append(
                CategoryFinding(
                    code="engagement.opportunity_suggested",
                    severity="opportunity",
                    title=item["title"],
                    evidence={
                        "rationale": item["rationale"],
                        "headline": headline,
                        "target_role": ctx.target_role,
                    },
                    deterministic=False,
                )
            )
    else:
        findings.append(
            CategoryFinding(
                code="engagement.no_opportunities_context",
                severity="opportunity",
                title="Add a headline and target role to unlock personalised engagement ideas",
                evidence={
                    "headline_present": bool(headline),
                    "target_role_present": bool(ctx.target_role),
                },
                deterministic=True,
            )
        )

    score = weighted_average(
        {
            "network_signals": network_score,
            "contactability": contactability_score,
            "engagement_opportunities": opportunities_score,
        },
        {
            "network_signals": component_weight(CATEGORY, "network_signals"),
            "contactability": component_weight(CATEGORY, "contactability"),
            "engagement_opportunities": component_weight(CATEGORY, "engagement_opportunities"),
        },
    )

    if score is None:
        return CategoryResult(
            category=CATEGORY,
            status="skipped",
            score=None,
            inputs_available={
                **inputs_available,
                "unlock": "Connect LinkedIn or fill in your profile details to unlock engagement scoring.",
            },
            detail={},
            findings=findings,
        )

    all_available = all(
        s is not None for s in (network_score, contactability_score, opportunities_score)
    )
    status: CategoryStatus = "ok" if all_available else "partial"
    return CategoryResult(
        category=CATEGORY,
        status=status,
        score=score,
        inputs_available=inputs_available,
        detail={
            "network_sub_scores": network_sub_scores,
            "contact_sub_scores": contact_sub_scores,
            "opportunities": opportunities,
        },
        findings=findings,
    )
