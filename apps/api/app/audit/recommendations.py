"""Maps audit findings to actionable `Recommendation` rows.

A fixed, deterministic table keyed by finding `code` -- a recommendation's
copy, route, and estimated impact never depend on an AI call. Only
findings that point at a single, concrete, distinct action are mapped
here; a purely informational "we don't have enough data yet, unlock this
by doing X" finding (`*.no_target_role`, `*.no_opportunities_context`,
and similar) is still recorded on its `AuditCategoryResult` for the
dashboard's "not enough data" state, but doesn't get its own
recommendation card -- several categories raise their own version of
"tell us your target role", and turning each into a separate card would
just repeat the same advice three times in the top recommendations feed.

Where two categories would otherwise recommend the identical action
(engagement and visibility both notice a missing custom URL), only one
canonical code is mapped so a single audit run can't surface the same
card twice; see the comment by `visibility.no_custom_url` below.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.audit.models import CategoryFinding, CategoryResult
from app.models.recommendation import Recommendation

_SEVERITY_RANK: dict[str, int] = {"critical": 0, "important": 1, "opportunity": 2}


@dataclass(frozen=True, slots=True)
class RecommendationRoute:
    title: str
    action_label: str
    action_route: str
    estimated_impact_points: int
    action_tool_id: str | None = None


_ROUTES: dict[str, RecommendationRoute] = {
    "profile.completeness.headline_present_and_substantial": RecommendationRoute(
        title="Sharpen your headline",
        action_label="Fix headline",
        action_route="/profile",
        estimated_impact_points=8,
    ),
    "profile.completeness.about_present_and_substantial": RecommendationRoute(
        title="Write your About section",
        action_label="Add About",
        action_route="/profile",
        estimated_impact_points=8,
    ),
    "profile.completeness.has_minimum_experiences": RecommendationRoute(
        title="Add more work experience",
        action_label="Add experience",
        action_route="/profile",
        estimated_impact_points=10,
    ),
    "profile.completeness.current_role_has_detailed_description": RecommendationRoute(
        title="Describe your current role in more detail",
        action_label="Add bullet points",
        action_route="/profile",
        estimated_impact_points=6,
    ),
    "profile.completeness.has_minimum_skills": RecommendationRoute(
        title="List more of your skills",
        action_label="Add skills",
        action_route="/profile",
        estimated_impact_points=5,
    ),
    "profile.completeness.has_certification_or_project": RecommendationRoute(
        title="Add a certification or project",
        action_label="Add one",
        action_route="/profile",
        estimated_impact_points=3,
    ),
    "profile.completeness.has_custom_url": RecommendationRoute(
        title="Claim a custom LinkedIn URL",
        action_label="Claim URL",
        action_route="/profile",
        estimated_impact_points=2,
    ),
    "profile.completeness.has_profile_photo": RecommendationRoute(
        title="Add a profile photo",
        action_label="Add photo",
        action_route="/profile",
        estimated_impact_points=2,
    ),
    "profile.headline_quality_issue": RecommendationRoute(
        title="Improve your headline's writing",
        action_label="Rewrite headline",
        action_route="/profile",
        estimated_impact_points=5,
        action_tool_id="headline_rewriter",
    ),
    "profile.about_quality_issue": RecommendationRoute(
        title="Improve your About section's writing",
        action_label="Rewrite About",
        action_route="/profile",
        estimated_impact_points=5,
        action_tool_id="about_rewriter",
    ),
    "profile.experience_quality_issue": RecommendationRoute(
        title="Turn your experience bullets into achievements",
        action_label="Rewrite bullets",
        action_route="/profile",
        estimated_impact_points=5,
        action_tool_id="experience_rewriter",
    ),
    "content.opportunity_from_skills": RecommendationRoute(
        title="Share a post idea from your own experience",
        action_label="See idea",
        action_route="/content",
        estimated_impact_points=3,
    ),
    "content.no_history_supplied": RecommendationRoute(
        title="Paste or upload some recent posts",
        action_label="Add posts",
        action_route="/content",
        estimated_impact_points=4,
    ),
    "engagement.no_contact_cta": RecommendationRoute(
        title="Invite people to reach out in your About section",
        action_label="Edit About",
        action_route="/profile",
        estimated_impact_points=3,
    ),
    "engagement.no_network_metrics": RecommendationRoute(
        title="Connect LinkedIn or add your network numbers",
        action_label="Connect LinkedIn",
        action_route="/engagement",
        estimated_impact_points=2,
    ),
    "engagement.opportunity_suggested": RecommendationRoute(
        title="Try a manual engagement idea",
        action_label="See idea",
        action_route="/engagement",
        estimated_impact_points=3,
    ),
    "career.missing_target_role_skills": RecommendationRoute(
        title="Add skills your target role expects",
        action_label="Add skills",
        action_route="/profile",
        estimated_impact_points=6,
    ),
    "career.no_resume_uploaded": RecommendationRoute(
        title="Upload your resume for career cross-referencing",
        action_label="Upload resume",
        action_route="/career",
        estimated_impact_points=3,
    ),
    # Canonical home for "claim a custom URL" -- engagement.no_custom_url
    # fires the identical fact and is intentionally left unmapped so one
    # audit run can't produce the same card twice.
    "visibility.no_custom_url": RecommendationRoute(
        title="Claim a custom LinkedIn URL",
        action_label="Claim URL",
        action_route="/profile",
        estimated_impact_points=3,
    ),
    "visibility.no_industry": RecommendationRoute(
        title="Set your industry",
        action_label="Add industry",
        action_route="/profile",
        estimated_impact_points=2,
    ),
    "visibility.no_location": RecommendationRoute(
        title="Set your location",
        action_label="Add location",
        action_route="/profile",
        estimated_impact_points=2,
    ),
    "visibility.inconsistent_brand_vocabulary": RecommendationRoute(
        title="Use consistent, role-relevant wording across your profile",
        action_label="Review wording",
        action_route="/profile",
        estimated_impact_points=4,
    ),
}


def resolve_route(code: str) -> RecommendationRoute | None:
    return _ROUTES.get(code)


def build_recommendations(
    *, audit_id: uuid.UUID, user_id: uuid.UUID, results: list[CategoryResult]
) -> list[Recommendation]:
    """Ranks every mappable finding across all categories by severity
    (ties broken by estimated impact) and returns one Recommendation per
    finding, in that priority order -- there's no separate cap here, so a
    "top 3" or "top 5" is a display-layer slice, not a modeling decision.
    """
    candidates: list[tuple[CategoryResult, CategoryFinding, RecommendationRoute]] = []
    for result in results:
        for finding in result.findings:
            route = resolve_route(finding.code)
            if route is not None:
                candidates.append((result, finding, route))

    candidates.sort(
        key=lambda item: (_SEVERITY_RANK[item[1].severity], -item[2].estimated_impact_points)
    )

    return [
        Recommendation(
            audit_id=audit_id,
            user_id=user_id,
            category=result.category,
            priority=priority,
            title=route.title,
            why=finding.title,
            action_label=route.action_label,
            action_route=route.action_route,
            action_tool_id=route.action_tool_id,
            estimated_impact_points=route.estimated_impact_points,
        )
        for priority, (result, finding, route) in enumerate(candidates, start=1)
    ]
