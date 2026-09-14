"""The admin panel's HTTP surface: users, subscriptions, feature flags,
AI operations, moderation, and platform health. Every endpoint requires
`get_current_admin`; every mutating one writes to `audit_log` (see the
service-layer functions in app/admin/*.py, which do the actual writing).
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import ai_ops, feature_flags, moderation, platform_health, subscriptions, users
from app.deps import get_current_admin, get_db
from app.models.ai_invocation import AIInvocation
from app.models.feature_flag import FeatureFlag
from app.models.job import Job
from app.models.moderation_flag import ModerationFlag
from app.models.subscription import Subscription
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.schemas.admin import (
    AdjustPlanRequest,
    AdminSubscriptionResponse,
    AdminSubscriptionSummary,
    AdminToolRunSummary,
    AdminUserDetailResponse,
    AdminUserResponse,
    AdminUserSearchResponse,
    AiInvocationResponse,
    AiOpsOverviewResponse,
    CostByDayResponse,
    CostByDimensionResponse,
    FeatureFlagResponse,
    ForcePasswordResetResponse,
    ImpersonateResponse,
    JobResponse,
    ModerationFlagResponse,
    OutcomeRatesResponse,
    PlatformHealthResponse,
    QueueDepthResponse,
    ReviewFlagRequest,
    SetFlagGlobalRequest,
    SetFlagRolloutRequest,
    SetFlagUserOverrideRequest,
    SlowPromptResponse,
    SuspendUserRequest,
    WebhookEventResponse,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        plan=user.plan,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


# -- Users --------------------------------------------------------------


@router.get("/users", response_model=AdminUserSearchResponse)
async def search_users_endpoint(
    q: str | None = None,
    plan: str | None = None,
    status: str | None = None,
    signed_up_after: date | None = None,
    signed_up_before: date | None = None,
    offset: int = 0,
    limit: int = Query(default=25, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserSearchResponse:
    page = await users.search_users(
        db,
        query=q,
        plan=plan,
        status=status,
        signed_up_after=signed_up_after,
        signed_up_before=signed_up_before,
        offset=offset,
        limit=limit,
    )
    return AdminUserSearchResponse(items=[_user_response(u) for u in page.items], total=page.total)


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user_detail_endpoint(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetailResponse:
    detail = await users.get_user_detail(db, user_id=user_id)
    return AdminUserDetailResponse(
        user=_user_response(detail.user),
        subscription=(
            AdminSubscriptionSummary(
                provider=detail.subscription.provider,
                plan=detail.subscription.plan,
                status=detail.subscription.status,
                current_period_end=detail.subscription.current_period_end,
            )
            if detail.subscription
            else None
        ),
        recent_tool_runs=[
            AdminToolRunSummary(
                id=str(run.id), tool_id=run.tool_id, status=run.status, created_at=run.created_at
            )
            for run in detail.recent_tool_runs
        ],
        ai_spend_minor_this_month=detail.ai_spend_minor_30d,
        ai_run_count_this_month=detail.ai_run_count_30d,
    )


@router.post("/users/{user_id}/suspend", response_model=AdminUserResponse)
async def suspend_user_endpoint(
    user_id: uuid.UUID,
    payload: SuspendUserRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    user = await users.suspend_user(db, admin_id=admin.id, user_id=user_id, reason=payload.reason)
    return _user_response(user)


@router.post("/users/{user_id}/reinstate", response_model=AdminUserResponse)
async def reinstate_user_endpoint(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    user = await users.reinstate_user(db, admin_id=admin.id, user_id=user_id)
    return _user_response(user)


@router.post("/users/{user_id}/force-password-reset", response_model=ForcePasswordResetResponse)
async def force_password_reset_endpoint(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ForcePasswordResetResponse:
    token = await users.force_password_reset(db, admin_id=admin.id, user_id=user_id)
    return ForcePasswordResetResponse(reset_token=token)


@router.post("/users/{user_id}/adjust-plan", response_model=AdminUserResponse)
async def adjust_plan_endpoint(
    user_id: uuid.UUID,
    payload: AdjustPlanRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    user = await users.adjust_plan(
        db, admin_id=admin.id, user_id=user_id, plan=payload.plan, reason=payload.reason
    )
    return _user_response(user)


@router.post("/users/{user_id}/impersonate", response_model=ImpersonateResponse)
async def impersonate_user_endpoint(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ImpersonateResponse:
    token, expires_at = await users.start_impersonation(db, admin_id=admin.id, user_id=user_id)
    return ImpersonateResponse(access_token=token, expires_at=expires_at)


# -- Subscriptions --------------------------------------------------------


def _subscription_response(subscription: Subscription) -> AdminSubscriptionResponse:
    return AdminSubscriptionResponse(
        id=str(subscription.id),
        user_id=str(subscription.user_id),
        provider=subscription.provider,
        plan=subscription.plan,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


def _webhook_event_response(event: WebhookEvent) -> WebhookEventResponse:
    return WebhookEventResponse(
        id=str(event.id),
        provider=event.provider,
        provider_event_id=event.provider_event_id,
        type=event.type,
        status=event.status,
        attempts=event.attempts,
        received_at=event.received_at,
        processed_at=event.processed_at,
        error=event.error,
    )


@router.get("/subscriptions", response_model=list[AdminSubscriptionResponse])
async def list_subscriptions_endpoint(
    status: str | None = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSubscriptionResponse]:
    page = await subscriptions.list_subscriptions(db, status=status)
    return [_subscription_response(s) for s in page.items]


@router.get("/subscriptions/{subscription_id}/webhooks", response_model=list[WebhookEventResponse])
async def get_webhook_history_endpoint(
    subscription_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookEventResponse]:
    events = await subscriptions.get_webhook_history(db, subscription_id=subscription_id)
    return [_webhook_event_response(e) for e in events]


@router.post("/webhooks/{webhook_event_id}/replay", response_model=WebhookEventResponse)
async def replay_webhook_endpoint(
    webhook_event_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> WebhookEventResponse:
    event = await subscriptions.replay_webhook(
        db, admin_id=admin.id, webhook_event_id=webhook_event_id
    )
    return _webhook_event_response(event)


# -- Feature flags --------------------------------------------------------


def _flag_response(flag: FeatureFlag) -> FeatureFlagResponse:
    return FeatureFlagResponse(
        key=flag.key,
        enabled_globally=flag.enabled_globally,
        rollout_percent=flag.rollout_percent,
        description=flag.description,
    )


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags_endpoint(
    admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[FeatureFlagResponse]:
    flags = await feature_flags.list_flags(db)
    return [_flag_response(f) for f in flags]


@router.post("/feature-flags/{key}/global", response_model=FeatureFlagResponse)
async def set_flag_global_endpoint(
    key: str,
    payload: SetFlagGlobalRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagResponse:
    flag = await feature_flags.set_global(
        db, admin_id=admin.id, key=key, enabled_globally=payload.enabled_globally
    )
    return _flag_response(flag)


@router.post("/feature-flags/{key}/rollout", response_model=FeatureFlagResponse)
async def set_flag_rollout_endpoint(
    key: str,
    payload: SetFlagRolloutRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagResponse:
    flag = await feature_flags.set_rollout(
        db, admin_id=admin.id, key=key, rollout_percent=payload.rollout_percent
    )
    return _flag_response(flag)


@router.post("/feature-flags/{key}/user-override", status_code=204)
async def set_flag_user_override_endpoint(
    key: str,
    payload: SetFlagUserOverrideRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await feature_flags.set_user_override(
        db,
        admin_id=admin.id,
        key=key,
        user_id=uuid.UUID(payload.user_id),
        enabled=payload.enabled,
    )


# -- AI operations --------------------------------------------------------


@router.get("/ai-ops/overview", response_model=AiOpsOverviewResponse)
async def ai_ops_overview_endpoint(
    days: int = Query(default=30, le=180),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AiOpsOverviewResponse:
    cost_day = await ai_ops.cost_by_day(db, days=days)
    cost_model = await ai_ops.cost_by_model(db, days=days)
    cost_prompt = await ai_ops.cost_by_prompt(db, days=days)
    rates = await ai_ops.outcome_rates(db, days=days)
    slow = await ai_ops.slowest_prompts(db, days=days)
    return AiOpsOverviewResponse(
        cost_by_day=[CostByDayResponse(**asdict(row)) for row in cost_day],
        cost_by_model=[CostByDimensionResponse(**asdict(row)) for row in cost_model],
        cost_by_prompt=[CostByDimensionResponse(**asdict(row)) for row in cost_prompt],
        outcome_rates=OutcomeRatesResponse(**asdict(rates)),
        slowest_prompts=[SlowPromptResponse(**asdict(row)) for row in slow],
    )


def _invocation_response(invocation: AIInvocation) -> AiInvocationResponse:
    return AiInvocationResponse(
        id=str(invocation.id),
        user_id=str(invocation.user_id),
        prompt_id=invocation.prompt_id,
        prompt_version=invocation.prompt_version,
        tier=invocation.tier,
        provider=invocation.provider,
        model=invocation.model,
        tokens_in=invocation.tokens_in,
        tokens_out=invocation.tokens_out,
        cost_minor=invocation.cost_minor,
        latency_ms=invocation.latency_ms,
        cached=invocation.cached,
        fallback_used=invocation.fallback_used,
        outcome=invocation.outcome,
        created_at=invocation.created_at,
    )


@router.get("/ai-ops/prompts/{prompt_id}", response_model=list[AiInvocationResponse])
async def prompt_drilldown_endpoint(
    prompt_id: str,
    days: int = Query(default=30, le=180),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AiInvocationResponse]:
    invocations = await ai_ops.prompt_drilldown(db, prompt_id=prompt_id, days=days)
    return [_invocation_response(i) for i in invocations]


# -- Moderation -------------------------------------------------------------


def _flag_view(flag: ModerationFlag) -> ModerationFlagResponse:
    return ModerationFlagResponse(
        id=str(flag.id),
        user_id=str(flag.user_id),
        source=flag.source,
        target_type=flag.target_type,
        target_id=flag.target_id,
        reason=flag.reason,
        excerpt=flag.excerpt,
        status=flag.status,
        reviewed_by=str(flag.reviewed_by) if flag.reviewed_by else None,
        reviewed_at=flag.reviewed_at,
        review_note=flag.review_note,
        created_at=flag.created_at,
    )


@router.get("/moderation/flags", response_model=list[ModerationFlagResponse])
async def list_moderation_flags_endpoint(
    status: str | None = "pending",
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ModerationFlagResponse]:
    flags = await moderation.list_flags(db, status=status)
    return [_flag_view(f) for f in flags]


@router.post("/moderation/flags/{flag_id}/review", response_model=ModerationFlagResponse)
async def review_moderation_flag_endpoint(
    flag_id: uuid.UUID,
    payload: ReviewFlagRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ModerationFlagResponse:
    flag = await moderation.review_flag(
        db, admin_id=admin.id, flag_id=flag_id, status=payload.status, note=payload.note
    )
    return _flag_view(flag)


# -- Platform health ----------------------------------------------------


def _job_response(job: Job) -> JobResponse:
    return JobResponse(
        id=str(job.id),
        type=job.type,
        status=job.status,
        attempts=job.attempts,
        error=job.error,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


@router.get("/platform-health", response_model=PlatformHealthResponse)
async def platform_health_endpoint(
    admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> PlatformHealthResponse:
    depth = await platform_health.queue_depth(db)
    dead = await platform_health.list_dead_jobs(db)
    return PlatformHealthResponse(
        queue_depth=QueueDepthResponse(**asdict(depth)),
        dead_jobs=[_job_response(j) for j in dead],
        circuit_breakers=platform_health.provider_circuit_state(),
    )


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_dead_job_endpoint(
    job_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    job = await platform_health.retry_dead_job(db, admin_id=admin.id, job_id=job_id)
    return _job_response(job)
