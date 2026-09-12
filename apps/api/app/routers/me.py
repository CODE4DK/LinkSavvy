from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import MeResponse, UserPublic
from app.services.feature_flags import resolve_flags_for_user

router = APIRouter(prefix="/api/v1", tags=["me"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MeResponse:
    flags = await resolve_flags_for_user(db, user_id=user.id)
    return MeResponse(
        user=UserPublic(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            locale=user.locale,
            timezone=user.timezone,
            role=user.role,
            plan=user.plan,
            email_verified=user.email_verified_at is not None,
            created_at=user.created_at,
        ),
        feature_flags=flags,
    )
