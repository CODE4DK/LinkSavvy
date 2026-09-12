"""Shared ORM-row -> response-schema mappers for the audit API
(app/routers/audits.py) and the dashboard aggregate (app/routers/dashboard.py)
-- kept in one place so the two never drift on how a category result or a
recommendation is shaped for the wire.
"""

from __future__ import annotations

from app.models.audit import AuditCategoryResult, AuditFinding
from app.models.recommendation import Recommendation
from app.schemas.audit import (
    AuditCategoryResultResponse,
    AuditFindingResponse,
    RecommendationResponse,
)


def to_finding_response(finding: AuditFinding) -> AuditFindingResponse:
    return AuditFindingResponse(
        id=str(finding.id),
        category=finding.category,
        code=finding.code,
        severity=finding.severity,
        title=finding.title,
        evidence=finding.evidence,
        deterministic=finding.deterministic,
    )


def to_category_result_response(
    result: AuditCategoryResult, findings: list[AuditFinding]
) -> AuditCategoryResultResponse:
    return AuditCategoryResultResponse(
        category=result.category,
        score=result.score,
        status=result.status,
        inputs_available=result.inputs_available,
        detail=result.detail,
        findings=[to_finding_response(finding) for finding in findings],
    )


def to_recommendation_response(recommendation: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        id=str(recommendation.id),
        audit_id=str(recommendation.audit_id),
        category=recommendation.category,
        priority=recommendation.priority,
        title=recommendation.title,
        why=recommendation.why,
        action_label=recommendation.action_label,
        action_route=recommendation.action_route,
        action_tool_id=recommendation.action_tool_id,
        estimated_impact_points=recommendation.estimated_impact_points,
        status=recommendation.status,
        completed_at=recommendation.completed_at,
    )
