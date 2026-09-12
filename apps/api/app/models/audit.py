"""The Audit Engine's core aggregate: one `Audit` run, its five
`AuditCategoryResult` rows (one per category, always exactly five so a
skipped/failed category is visible rather than just absent), and the
`AuditFinding` rows each category contributes. See app/audit/."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

AuditStatus = Enum(
    "pending", "running", "completed", "completed_with_errors", "failed", name="audit_status"
)
AuditTrigger = Enum("onboarding", "manual", "scheduled", name="audit_trigger")


def _category_enum(name: str) -> Enum:
    # A SQLAlchemy Enum is a SchemaType tied to the one column it's first
    # attached to -- reusing the same instance across audit_category_results,
    # audit_findings, and (in recommendation.py) recommendations would
    # error on the second attachment, so each column gets its own instance
    # of the same five values.
    return Enum("profile", "content", "engagement", "career", "visibility", name=name)


AuditCategoryResultCategory = _category_enum("audit_category_result_category")
AuditFindingCategory = _category_enum("audit_finding_category")

AuditCategoryResultStatus = Enum(
    "ok", "partial", "skipped", "failed", name="audit_category_result_status"
)
AuditFindingSeverity = Enum("critical", "important", "opportunity", name="audit_finding_severity")


class Audit(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audits"
    __table_args__ = (
        Index("ix_audits_user_created", "user_id", "created_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # SET NULL, not CASCADE: the audit's own findings/scores stay part of
    # the user's history even if the snapshot they were computed from is
    # later superseded and purged.
    profile_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("profile_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(AuditStatus, nullable=False, default="pending")
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trigger: Mapped[str] = mapped_column(AuditTrigger, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditCategoryResult(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_category_results"
    __table_args__ = (
        UniqueConstraint("audit_id", "category", name="uq_audit_category_results_audit_category"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(AuditCategoryResultCategory, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(AuditCategoryResultStatus, nullable=False)
    # What data this category could/couldn't see and why -- the dashboard
    # renders "Not enough data yet" straight from this rather than a
    # generic low score. See app/audit/categories/.
    inputs_available: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class AuditFinding(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_findings"
    __table_args__ = (
        Index("ix_audit_findings_audit_category", "audit_id", "category"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(AuditFindingCategory, nullable=False)
    code: Mapped[str] = mapped_column(String(96), nullable=False)
    severity: Mapped[str] = mapped_column(AuditFindingSeverity, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Always non-empty -- a finding with no evidence citing the user's own
    # data is a bug, not a valid finding. Enforced in app/audit/, not the
    # database (evidence shape varies too much per finding code for a
    # useful CHECK constraint).
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    deterministic: Mapped[bool] = mapped_column(Boolean, nullable=False)
