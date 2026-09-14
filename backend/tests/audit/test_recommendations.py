from __future__ import annotations

import uuid

from app.audit.models import CategoryFinding, CategoryResult
from app.audit.recommendations import build_recommendations, resolve_route


def test_resolve_route_returns_none_for_unmapped_code() -> None:
    assert resolve_route("career.no_target_role") is None
    assert resolve_route("some.made_up.code") is None


def test_resolve_route_returns_a_route_for_every_mapped_code() -> None:
    route = resolve_route("profile.completeness.has_minimum_experiences")
    assert route is not None
    assert route.action_route == "/profile"
    assert route.estimated_impact_points > 0


def test_build_recommendations_skips_findings_without_a_route() -> None:
    result = CategoryResult(
        category="career",
        status="skipped",
        score=None,
        inputs_available={},
        detail={},
        findings=[
            CategoryFinding(
                code="career.no_target_role",
                severity="opportunity",
                title="Tell us your target role",
                evidence={},
                deterministic=True,
            )
        ],
    )
    recs = build_recommendations(audit_id=uuid.uuid4(), user_id=uuid.uuid4(), results=[result])
    assert recs == []


def test_build_recommendations_orders_by_severity_then_impact() -> None:
    results = [
        CategoryResult(
            category="profile",
            status="ok",
            score=80,
            inputs_available={},
            detail={},
            findings=[
                CategoryFinding(
                    code="profile.completeness.has_profile_photo",  # opportunity, impact 2
                    severity="opportunity",
                    title="Add a profile photo",
                    evidence={},
                    deterministic=True,
                ),
                CategoryFinding(
                    code="profile.completeness.has_minimum_experiences",  # critical, impact 10
                    severity="critical",
                    title="Add more work experience",
                    evidence={},
                    deterministic=True,
                ),
            ],
        ),
        CategoryResult(
            category="career",
            status="partial",
            score=40,
            inputs_available={},
            detail={},
            findings=[
                CategoryFinding(
                    code="career.missing_target_role_skills",  # important, impact 6
                    severity="important",
                    title="Add Kubernetes to your skills",
                    evidence={},
                    deterministic=True,
                )
            ],
        ),
    ]
    recs = build_recommendations(audit_id=uuid.uuid4(), user_id=uuid.uuid4(), results=results)
    assert len(recs) == 3
    codes_in_order = [r.why for r in recs]
    assert codes_in_order == [
        "Add more work experience",  # critical first
        "Add Kubernetes to your skills",  # then important
        "Add a profile photo",  # then opportunity
    ]
    assert [r.priority for r in recs] == [1, 2, 3]
