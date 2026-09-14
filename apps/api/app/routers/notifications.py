"""The notification centre's HTTP surface, plus the one endpoint that
takes no auth at all: one-click unsubscribe, which a mail client hits
directly with nothing but the signed token in the URL (see
app/notifications/unsubscribe.py).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.notification import Notification
from app.models.user import User
from app.notifications import service
from app.notifications.unsubscribe import InvalidUnsubscribeToken, parse_unsubscribe_token
from app.schemas.notifications import (
    NotificationListResponse,
    NotificationResponse,
    PreferenceRow,
    PreferencesResponse,
    SetPreferenceRequest,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def _to_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=str(notification.id),
        type=notification.type,
        title=notification.title,
        body=notification.body,
        action_route=notification.action_route,
        metadata=notification.metadata_,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications_endpoint(
    unread_only: bool = False,
    limit: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    page = await service.list_notifications(
        db, user_id=user.id, limit=limit, unread_only=unread_only
    )
    return NotificationListResponse(
        items=[_to_response(item) for item in page.items], unread_count=page.unread_count
    )


@router.post("/{notification_id}/read", status_code=204)
async def mark_read_endpoint(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.mark_read(db, user_id=user.id, notification_id=notification_id)


@router.post("/read-all", status_code=204)
async def mark_all_read_endpoint(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    await service.mark_all_read(db, user_id=user.id)


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences_endpoint(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> PreferencesResponse:
    rows = await service.list_preferences(db, user_id=user.id)
    return PreferencesResponse(
        preferences=[
            PreferenceRow(channel=channel, type=notification_type, enabled=enabled)  # type: ignore[arg-type]
            for channel, notification_type, enabled in rows
        ]
    )


@router.put("/preferences", response_model=PreferencesResponse)
async def set_preference_endpoint(
    payload: SetPreferenceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferencesResponse:
    await service.set_preference(
        db,
        user_id=user.id,
        channel=payload.channel,
        notification_type=payload.type,
        enabled=payload.enabled,
    )
    rows = await service.list_preferences(db, user_id=user.id)
    return PreferencesResponse(
        preferences=[
            PreferenceRow(channel=channel, type=notification_type, enabled=enabled)  # type: ignore[arg-type]
            for channel, notification_type, enabled in rows
        ]
    )


async def _unsubscribe(token: str, db: AsyncSession) -> HTMLResponse:
    try:
        user_id, notification_type = parse_unsubscribe_token(token)
    except InvalidUnsubscribeToken as exc:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "Invalid or expired unsubscribe link") from exc

    await service.set_preference(
        db, user_id=user_id, channel="email", notification_type=notification_type, enabled=False
    )
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;padding:40px;text-align:center;'>"
        "<h1>Unsubscribed</h1>"
        f'<p>You won\'t get any more "{notification_type}" emails from LinkSavvy. '
        "You can turn this back on any time from your notification preferences.</p>"
        "</body></html>"
    )


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_get(token: str, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    return await _unsubscribe(token, db)


@router.post("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_post(token: str, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    """RFC 8058 one-click unsubscribe: mail clients POST here directly
    (List-Unsubscribe-Post: List-Unsubscribe=One-Click) with no user
    interaction at all, so this must accept exactly the same token-only
    request the GET version does."""
    return await _unsubscribe(token, db)
