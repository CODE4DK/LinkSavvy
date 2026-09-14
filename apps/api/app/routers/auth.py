from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import client_ip, get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.email_verification import EmailVerification
from app.models.oauth_identity import OAuthIdentity
from app.models.oauth_login_state import OAuthLoginState
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LinkedInStartResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SessionOut,
    VerifyEmailRequest,
)
from app.schemas.user import UserPublic
from app.security.csrf import CSRF_COOKIE_NAME, generate_csrf_token, verify_csrf
from app.security.jwt import create_access_token
from app.security.passwords import hash_password, verify_password
from app.security.tokens import generate_raw_token, hash_ip, hash_token
from app.services import sessions as session_service
from app.services.audit import record_audit_event
from app.services.email import send_password_reset_email, send_verification_email
from app.services.linkedin import (
    LinkedInOAuthError,
    build_authorization_url,
    exchange_code_for_tokens,
    generate_nonce,
    generate_pkce_pair,
    generate_state,
    verify_id_token,
)
from app.services.rate_limit import check_rate_limit, record_attempt
from app.settings import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"
OAUTH_STATE_TTL_MINUTES = 10


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_ttl_days * 24 * 3600,
        path=REFRESH_COOKIE_PATH,
    )
    # Not httpOnly -- the frontend reads it and echoes it back as
    # X-CSRF-Token on the two endpoints (refresh, logout) that
    # authenticate from this cookie alone. See app/security/csrf.py.
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=generate_csrf_token(),
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_ttl_days * 24 * 3600,
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    response.delete_cookie(key=CSRF_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email_normalized == email.lower()))
    return result.scalar_one_or_none()


@router.post("/register", response_model=MessageResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    ip_hash = hash_ip(client_ip(request))
    await check_rate_limit(
        db,
        email_normalized=payload.email.lower(),
        ip_hash=ip_hash,
        limit=settings.register_rate_limit_per_minute,
    )

    existing = await _get_user_by_email(db, payload.email)
    generic_message = MessageResponse(
        message="If that email is new to us, check your inbox for a verification link."
    )
    if existing is not None:
        # Same response either way — registration must not reveal whether
        # the address is already in use.
        await record_attempt(
            db, email_normalized=payload.email.lower(), ip_hash=ip_hash, succeeded=True
        )
        await db.commit()
        return generic_message

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.flush()

    raw_token = generate_raw_token()
    db.add(
        EmailVerification(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.email_verification_ttl_hours),
        )
    )
    await record_attempt(
        db, email_normalized=payload.email.lower(), ip_hash=ip_hash, succeeded=True
    )
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.register",
        target_type="user",
        target_id=str(user.id),
        ip_hash=ip_hash,
    )
    await db.commit()

    await send_verification_email(to=payload.email, token=raw_token)
    return generic_message


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    token_hash = hash_token(payload.token)
    result = await db.execute(
        select(EmailVerification).where(EmailVerification.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record is None or record.consumed_at is not None:
        raise ApiError(ErrorCode.NOT_FOUND, "Verification token not found")
    if record.expires_at < datetime.now(UTC):
        raise ApiError(ErrorCode.TOKEN_EXPIRED, "Verification token has expired")

    user = await db.get(User, record.user_id)
    if user is None:
        raise ApiError(ErrorCode.NOT_FOUND, "Verification token not found")

    user.email_verified_at = datetime.now(UTC)
    record.consumed_at = datetime.now(UTC)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.verify_email",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()
    return MessageResponse(message="Email verified. You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    ip_hash = hash_ip(client_ip(request))
    await check_rate_limit(
        db,
        email_normalized=payload.email.lower(),
        ip_hash=ip_hash,
        limit=settings.register_rate_limit_per_minute,
    )
    generic_message = MessageResponse(
        message="If that account needs verifying, a new link is on its way."
    )
    user = await _get_user_by_email(db, payload.email)
    await record_attempt(
        db, email_normalized=payload.email.lower(), ip_hash=ip_hash, succeeded=True
    )
    if user is None or user.email_verified_at is not None:
        await db.commit()
        return generic_message

    raw_token = generate_raw_token()
    db.add(
        EmailVerification(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.email_verification_ttl_hours),
        )
    )
    await db.commit()
    await send_verification_email(to=user.email, token=raw_token)
    return generic_message


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    ip_hash = hash_ip(client_ip(request))
    email_normalized = payload.email.lower()
    await check_rate_limit(
        db,
        email_normalized=email_normalized,
        ip_hash=ip_hash,
        limit=settings.login_rate_limit_per_minute,
    )

    user = await _get_user_by_email(db, payload.email)
    if (
        user is None
        or user.password_hash is None
        or not verify_password(payload.password, user.password_hash)
    ):
        await record_attempt(
            db, email_normalized=email_normalized, ip_hash=ip_hash, succeeded=False
        )
        await db.commit()
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "Incorrect email or password")

    if user.status != "active" or user.deleted_at is not None:
        await record_attempt(
            db, email_normalized=email_normalized, ip_hash=ip_hash, succeeded=False
        )
        await db.commit()
        raise ApiError(ErrorCode.FORBIDDEN, "This account is not active")

    if user.email_verified_at is None:
        await record_attempt(db, email_normalized=email_normalized, ip_hash=ip_hash, succeeded=True)
        await db.commit()
        raise ApiError(ErrorCode.EMAIL_NOT_VERIFIED, "Please verify your email before logging in")

    raw_refresh, _ = await session_service.issue_refresh_token(
        db,
        user_id=user.id,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=ip_hash,
    )
    user.last_login_at = datetime.now(UTC)
    await record_attempt(db, email_normalized=email_normalized, ip_hash=ip_hash, succeeded=True)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.login",
        target_type="user",
        target_id=str(user.id),
        ip_hash=ip_hash,
    )
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    access_token = create_access_token(user.id, role=user.role)
    return LoginResponse(
        access_token=access_token,
        expires_in=settings.access_token_ttl_minutes * 60,
        user=UserPublic.from_model(user),
    )


@router.post("/refresh", response_model=RefreshResponse, dependencies=[Depends(verify_csrf)])
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "No refresh token presented")

    try:
        new_raw, new_row = await session_service.rotate_refresh_token(
            db,
            raw_token=raw_token,
            user_agent=request.headers.get("User-Agent"),
            ip_hash=hash_ip(client_ip(request)),
        )
    except ApiError:
        await db.commit()
        _clear_refresh_cookie(response)
        raise

    user = await db.get(User, new_row.user_id)
    if user is None or user.status != "active" or user.deleted_at is not None:
        _clear_refresh_cookie(response)
        raise ApiError(ErrorCode.FORBIDDEN, "Account is not active")

    await db.commit()
    _set_refresh_cookie(response, new_raw)
    access_token = create_access_token(user.id, role=user.role)
    return RefreshResponse(
        access_token=access_token, expires_in=settings.access_token_ttl_minutes * 60
    )


@router.post("/logout", response_model=MessageResponse, dependencies=[Depends(verify_csrf)])
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        await session_service.revoke_token_by_hash(db, raw_token=raw_token)
        await db.commit()
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await session_service.revoke_all_for_user(db, user_id=user.id)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.logout_all",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out of all sessions.")


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SessionOut]:
    current_raw = request.cookies.get(REFRESH_COOKIE_NAME)
    current_hash = hash_token(current_raw) if current_raw else None
    active = await session_service.list_active_sessions(db, user_id=user.id)
    return [
        SessionOut(
            id=str(row.id),
            user_agent=row.user_agent,
            issued_at=row.issued_at,
            expires_at=row.expires_at,
            current=(row.token_hash == current_hash),
        )
        for row in active
    ]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    revoked = await session_service.revoke_session(db, user_id=user.id, session_id=session_id)
    if not revoked:
        raise ApiError(ErrorCode.NOT_FOUND, "Session not found")
    await db.commit()
    return MessageResponse(message="Session revoked.")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    ip_hash = hash_ip(client_ip(request))
    await check_rate_limit(
        db,
        email_normalized=payload.email.lower(),
        ip_hash=ip_hash,
        limit=settings.register_rate_limit_per_minute,
    )
    generic_message = MessageResponse(
        message="If that email has an account, a reset link is on its way."
    )
    user = await _get_user_by_email(db, payload.email)
    await record_attempt(
        db, email_normalized=payload.email.lower(), ip_hash=ip_hash, succeeded=True
    )
    if user is None or user.password_hash is None:
        await db.commit()
        return generic_message

    raw_token = generate_raw_token()
    db.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.password_reset_ttl_hours),
        )
    )
    await db.commit()
    await send_password_reset_email(to=user.email, token=raw_token)
    return generic_message


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    token_hash = hash_token(payload.token)
    result = await db.execute(select(PasswordReset).where(PasswordReset.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if record is None or record.consumed_at is not None:
        raise ApiError(ErrorCode.NOT_FOUND, "Reset token not found")
    if record.expires_at < datetime.now(UTC):
        raise ApiError(ErrorCode.TOKEN_EXPIRED, "Reset token has expired")

    user = await db.get(User, record.user_id)
    if user is None:
        raise ApiError(ErrorCode.NOT_FOUND, "Reset token not found")

    user.password_hash = hash_password(payload.new_password)
    record.consumed_at = datetime.now(UTC)
    await session_service.revoke_all_for_user(db, user_id=user.id)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.reset_password",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()
    return MessageResponse(message="Password reset. Please log in again.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    if user.password_hash is None or not verify_password(
        payload.current_password, user.password_hash
    ):
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "Current password is incorrect")

    user.password_hash = hash_password(payload.new_password)
    await session_service.revoke_all_for_user(db, user_id=user.id)
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.change_password",
        target_type="user",
        target_id=str(user.id),
    )
    await db.commit()
    _clear_refresh_cookie(response)
    return MessageResponse(message="Password changed. Please log in again.")


@router.get("/linkedin/start", response_model=LinkedInStartResponse)
async def linkedin_start(db: AsyncSession = Depends(get_db)) -> LinkedInStartResponse:
    verifier, challenge = generate_pkce_pair()
    state = generate_state()
    nonce = generate_nonce()
    db.add(
        OAuthLoginState(
            state=state,
            code_verifier=verifier,
            nonce=nonce,
            expires_at=datetime.now(UTC) + timedelta(minutes=OAUTH_STATE_TTL_MINUTES),
        )
    )
    await db.commit()
    try:
        url = build_authorization_url(state=state, nonce=nonce, code_challenge=challenge)
    except LinkedInOAuthError as exc:
        raise ApiError(ErrorCode.INTERNAL, str(exc)) from exc
    return LinkedInStartResponse(authorization_url=url)


@router.get("/linkedin/callback", response_model=LoginResponse)
async def linkedin_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    result = await db.execute(select(OAuthLoginState).where(OAuthLoginState.state == state))
    login_state = result.scalar_one_or_none()
    if login_state is None or login_state.expires_at < datetime.now(UTC):
        raise ApiError(ErrorCode.TOKEN_EXPIRED, "OAuth state expired or unknown")
    await db.delete(login_state)

    try:
        tokens = await exchange_code_for_tokens(code=code, code_verifier=login_state.code_verifier)
        claims = await verify_id_token(tokens["id_token"], expected_nonce=login_state.nonce)
    except (LinkedInOAuthError, KeyError) as exc:
        await db.commit()
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, f"LinkedIn sign-in failed: {exc}") from exc

    provider_user_id = claims["sub"]
    email = claims.get("email")
    ip_hash = hash_ip(client_ip(request))

    identity_result = await db.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == "linkedin",
            OAuthIdentity.provider_user_id == provider_user_id,
        )
    )
    identity = identity_result.scalar_one_or_none()

    if identity is not None:
        user = await db.get(User, identity.user_id)
    elif email:
        user = await _get_user_by_email(db, email)
        if user is not None and user.email_verified_at is None:
            user = None  # do not silently link to an unverified address
        if user is None:
            user = User(
                email=email,
                full_name=claims.get("name", email.split("@")[0]),
                avatar_url=claims.get("picture"),
                email_verified_at=datetime.now(UTC),
            )
            db.add(user)
            await db.flush()
        identity = OAuthIdentity(
            user_id=user.id,
            provider="linkedin",
            provider_user_id=provider_user_id,
            scopes="openid profile email",
            connected_at=datetime.now(UTC),
        )
        db.add(identity)
    else:
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, "LinkedIn did not return an email")

    if user is None:
        raise ApiError(ErrorCode.NOT_FOUND, "Account not found")

    user.last_login_at = datetime.now(UTC)
    raw_refresh, _ = await session_service.issue_refresh_token(
        db,
        user_id=user.id,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=ip_hash,
    )
    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.linkedin_login",
        target_type="user",
        target_id=str(user.id),
        ip_hash=ip_hash,
    )
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    access_token = create_access_token(user.id, role=user.role)
    return LoginResponse(
        access_token=access_token,
        expires_in=settings.access_token_ttl_minutes * 60,
        user=UserPublic.from_model(user),
    )
