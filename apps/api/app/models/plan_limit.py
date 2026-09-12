"""The rate card: how much of each metric a plan gets, and what happens
past it. Seeded by migration 0003 (see also
app/billing/plan_limits_seed.py, the same values for the test suite)."""

from __future__ import annotations

from sqlalchemy import Enum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

# A separate Enum instance from app.models.user.UserPlan (same "free"/"pro"
# values) — SQLAlchemy's Enum is a SchemaType tied to the one table it's
# first attached to, so the same instance can't be reused across tables.
PlanLimitPlan = Enum("free", "pro", name="plan_limit_plan")
PlanLimitWindow = Enum("day", "month", name="plan_limit_window")
PlanLimitOverageBehaviour = Enum("block", "soft_warn", name="plan_limit_overage_behaviour")


class PlanLimit(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plan_limits"
    __table_args__ = (
        UniqueConstraint("plan", "metric", name="uq_plan_limits_plan_metric"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    plan: Mapped[str] = mapped_column(PlanLimitPlan, nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    limit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    window: Mapped[str] = mapped_column(PlanLimitWindow, nullable=False)
    overage_behaviour: Mapped[str] = mapped_column(PlanLimitOverageBehaviour, nullable=False)
