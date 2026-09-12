"""The shapes every category audit returns -- not the SQLAlchemy models
(app/models/audit.py), which the orchestrator persists these into."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Category = Literal["profile", "content", "engagement", "career", "visibility"]
Severity = Literal["critical", "important", "opportunity"]
CategoryStatus = Literal["ok", "partial", "skipped", "failed"]


@dataclass(frozen=True, slots=True)
class CategoryFinding:
    code: str
    severity: Severity
    title: str
    # Must always cite something from the user's own data -- a finding
    # with no evidence is a bug, not a valid finding.
    evidence: dict[str, Any]
    deterministic: bool


@dataclass(frozen=True, slots=True)
class CategoryResult:
    category: Category
    status: CategoryStatus
    score: int | None
    inputs_available: dict[str, Any]
    detail: dict[str, Any]
    findings: list[CategoryFinding] = field(default_factory=list)
