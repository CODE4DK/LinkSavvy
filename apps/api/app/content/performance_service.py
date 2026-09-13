"""Manual performance capture: the user types in what LinkedIn's own
analytics showed them (impressions/reactions/comments/reposts/profile
views -- never scraped, per CLAUDE.md's hard compliance rule), and
this feeds two things: `resolve_content_history`'s fallback (a posted
plan is content history regardless of whether it has performance
numbers) and the "what worked" panel below, comparing post types by
median engagement once there's enough data to say anything meaningful.
"""

from __future__ import annotations

import statistics
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.calendar_service import get_owned_plan
from app.models.content_plan import ContentPlan
from app.models.user import User
from app.schemas.content_plans import PerformanceNumbers

# Below this many posts with any engagement data, a median-by-post-type
# comparison is more likely to mislead than inform -- say so instead of
# drawing a chart from three data points.
_MIN_DATA_POINTS = 5

_ENGAGEMENT_KEYS = ("reactions", "comments", "reposts")


async def record_performance(
    db: AsyncSession, *, user: User, plan_id: uuid.UUID, numbers: PerformanceNumbers
) -> ContentPlan:
    plan = await get_owned_plan(db, user=user, plan_id=plan_id)
    updates = numbers.model_dump(exclude_none=True)
    plan.performance = {**plan.performance, **updates}
    await db.commit()
    await db.refresh(plan)
    return plan


def _engagement(performance: dict[str, object]) -> int | None:
    values = [performance.get(key) for key in _ENGAGEMENT_KEYS]
    numeric = [v for v in values if isinstance(v, int)]
    if not numeric:
        return None
    return sum(numeric)


async def performance_summary(
    db: AsyncSession, *, user: User
) -> tuple[bool, int, list[tuple[str, int, float]]]:
    """Returns `(sufficient_data, total_data_points, by_content_type)`,
    where `by_content_type` is `[(content_type, sample_size,
    median_engagement)]`."""
    stmt = select(ContentPlan).where(
        ContentPlan.user_id == user.id, ContentPlan.deleted_at.is_(None)
    )
    plans = (await db.execute(stmt)).scalars().all()

    engagement_by_type: dict[str, list[int]] = defaultdict(list)
    total = 0
    for plan in plans:
        engagement = _engagement(plan.performance)
        if engagement is None:
            continue
        total += 1
        engagement_by_type[plan.content_type].append(engagement)

    if total < _MIN_DATA_POINTS:
        return False, total, []

    by_content_type = [
        (content_type, len(values), statistics.median(values))
        for content_type, values in sorted(engagement_by_type.items())
    ]
    return True, total, by_content_type
