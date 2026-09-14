"""Composes the Phase 08 weekly plan and score deltas into one digest --
the content half of the `notifications.weekly_digest` job (see
weekly_digest_job.py for the job handler itself)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.growth.history import get_score_history
from app.growth.weekly_plan import get_current_plan
from app.models.user import User

_SCORE_LABELS: dict[str, str] = {
    "health": "Health score",
    "visibility": "Visibility",
    "consistency": "Consistency",
    "personal_branding": "Personal branding",
}


@dataclass(frozen=True, slots=True)
class ScoreDelta:
    label: str
    from_value: float
    to_value: float

    @property
    def change(self) -> float:
        return round(self.to_value - self.from_value, 1)


@dataclass(frozen=True, slots=True)
class WeeklyDigestContent:
    has_content: bool
    focus: str | None
    item_titles: list[str]
    completed_count: int
    total_count: int
    score_deltas: list[ScoreDelta]


async def compose_weekly_digest(db: AsyncSession, *, user: User) -> WeeklyDigestContent:
    plan = await get_current_plan(db, user=user)
    history = await get_score_history(
        db, user_id=user.id, since=(datetime.now(UTC) - timedelta(days=8)).date()
    )

    deltas: list[ScoreDelta] = []
    for score_type, snapshots in history.items():
        if len(snapshots) < 2:
            continue
        deltas.append(
            ScoreDelta(
                label=_SCORE_LABELS.get(score_type, score_type),
                from_value=snapshots[0].value,
                to_value=snapshots[-1].value,
            )
        )

    if plan is None:
        return WeeklyDigestContent(
            has_content=bool(deltas),
            focus=None,
            item_titles=[],
            completed_count=0,
            total_count=0,
            score_deltas=deltas,
        )

    return WeeklyDigestContent(
        has_content=True,
        focus=plan.focus or None,
        item_titles=[item["title"] for item in plan.items],
        completed_count=plan.completed_count,
        total_count=len(plan.items),
        score_deltas=deltas,
    )


def render_digest_body(content: WeeklyDigestContent) -> str:
    lines: list[str] = []
    if content.focus:
        lines.append(f"This week's focus: {content.focus}.")
    if content.total_count:
        lines.append(f"You completed {content.completed_count} of {content.total_count} items.")
    if content.item_titles:
        lines.append("On your plan: " + "; ".join(content.item_titles) + ".")
    for delta in content.score_deltas:
        direction = "up" if delta.change > 0 else "down" if delta.change < 0 else "steady at"
        if direction == "steady at":
            lines.append(f"{delta.label} is {direction} {delta.to_value}.")
        else:
            lines.append(f"{delta.label} is {direction} {abs(delta.change)} to {delta.to_value}.")
    if not lines:
        lines.append("No new activity to report this week -- your Growth Hub is waiting for you.")
    return " ".join(lines)
