"""Consistency Score -- fully deterministic, computed entirely from
`content_plans` rows already marked `posted` (see
app.content.calendar_service.consistency_strip, which this module
reuses rather than re-querying the same 12-week window a second way).
Never a zero for a new user: fewer than four weeks of recorded activity
returns `insufficient_data` naming exactly what's missing.
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.content.calendar_service import consistency_strip
from app.growth.schema import GrowthScore, GrowthScoreStatus, GrowthScoreType, ScoreComponent
from app.growth.scoring_config import growth_component_weight, load_growth_scoring_config
from app.models.user import User

_SCORE_TYPE = "consistency"
_MIN_WEEKS_WITH_ACTIVITY = 4
_TARGET_POSTS_PER_WEEK = 2.0
_TARGET_STREAK_WEEKS = 8
_VARIANCE_PENALTY_PER_STDEV = 15


def _posts_per_week(counts: list[int]) -> tuple[int, dict[str, object]]:
    average = sum(counts) / len(counts)
    value = min(100, round(100 * average / _TARGET_POSTS_PER_WEEK))
    return value, {"average_posts_per_week": round(average, 2), "target": _TARGET_POSTS_PER_WEEK}


def _variance(counts: list[int]) -> tuple[int, dict[str, object]]:
    stdev = statistics.pstdev(counts)
    value = max(0, round(100 - stdev * _VARIANCE_PENALTY_PER_STDEV))
    return value, {"weekly_stdev": round(stdev, 2)}


def _longest_gap(counts: list[int]) -> tuple[int, dict[str, object]]:
    longest = current = 0
    for count in counts:
        if count == 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    value = max(0, 100 - max(0, longest - 1) * 20)
    return value, {"longest_gap_weeks": longest}


def _streak_length(counts: list[int]) -> tuple[int, dict[str, object]]:
    streak = 0
    for count in reversed(counts):
        if count > 0:
            streak += 1
        else:
            break
    value = min(100, round(100 * streak / _TARGET_STREAK_WEEKS))
    return value, {"current_streak_weeks": streak}


async def get_consistency_score(db: AsyncSession, *, user: User) -> GrowthScore:
    config = load_growth_scoring_config()
    weeks = await consistency_strip(db, user=user)
    counts = [count for _week_start, count in weeks]
    weeks_with_activity = sum(1 for count in counts if count > 0)

    if weeks_with_activity < _MIN_WEEKS_WITH_ACTIVITY:
        return GrowthScore(
            score_type=GrowthScoreType.CONSISTENCY,
            value=None,
            status=GrowthScoreStatus.INSUFFICIENT_DATA,
            components=[],
            computed_at=datetime.now(UTC),
            scoring_version=config.scoring_version,
            needed={
                "weeks_with_activity": weeks_with_activity,
                "weeks_needed": _MIN_WEEKS_WITH_ACTIVITY,
                "reason": "Record at least four weeks of posts to unlock this score.",
            },
        )

    raw = {
        "posts_per_week": _posts_per_week(counts),
        "variance": _variance(counts),
        "longest_gap": _longest_gap(counts),
        "streak_length": _streak_length(counts),
    }
    weights = {code: growth_component_weight(_SCORE_TYPE, code) for code in raw}
    overall = round(
        sum(value * weights[code] for code, (value, _evidence) in raw.items())
        / sum(weights.values())
    )
    components = [
        ScoreComponent(name=code, weight=weights[code], value=value, evidence=evidence)
        for code, (value, evidence) in raw.items()
    ]

    return GrowthScore(
        score_type=GrowthScoreType.CONSISTENCY,
        value=overall,
        status=GrowthScoreStatus.OK,
        components=components,
        computed_at=datetime.now(UTC),
        scoring_version=config.scoring_version,
    )
