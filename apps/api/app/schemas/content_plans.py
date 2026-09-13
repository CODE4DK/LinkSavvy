from __future__ import annotations

import uuid
from datetime import date, datetime
from datetime import time as time_of_day
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ContentPlanStatus = Literal["idea", "drafted", "ready", "scheduled", "posted", "skipped"]


class ContentPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: uuid.UUID | None = None
    title: str = ""
    body_preview: str = ""
    content_type: str = "post"
    status: ContentPlanStatus = "idea"
    planned_for: date
    planned_time: time_of_day | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str = ""


class ContentPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    body_preview: str | None = None
    content_type: str | None = None
    status: ContentPlanStatus | None = None
    tags: list[str] | None = None
    notes: str | None = None


class RescheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planned_for: date
    planned_time: time_of_day | None = None


class ReminderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reminder_at: datetime | None = None


class PerformanceNumbers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    impressions: int | None = None
    reactions: int | None = None
    comments: int | None = None
    reposts: int | None = None
    profile_views: int | None = None


class MarkContentPlanPostedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    linkedin_url: str | None = None
    posted_at: datetime | None = None
    performance: PerformanceNumbers | None = None


class Cadence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days_of_week: list[int] = Field(min_length=1, description="0=Monday ... 6=Sunday")
    time: time_of_day | None = None
    start_date: date
    weeks: int = Field(ge=1, le=52)


class RecurringSlotsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cadence: Cadence


class BulkScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cadence: Cadence
    plan_ids: list[uuid.UUID] = Field(min_length=1)


class ContentPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    asset_id: str | None
    title: str
    body_preview: str
    content_type: str
    status: ContentPlanStatus
    planned_for: date
    planned_time: time_of_day | None
    posted_at: datetime | None
    reminder_at: datetime | None
    recurrence_rule: str | None
    tags: list[str]
    performance: dict[str, int | str]
    notes: str
    created_at: datetime
    updated_at: datetime


class ConsistencyWeek(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_start: date
    posted_count: int
