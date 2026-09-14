from __future__ import annotations

import dataclasses
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.errors import ApiError, ErrorCode
from app.models.linkedin_connection import LinkedInConnection
from app.models.oauth_identity import OAuthIdentity
from app.models.oauth_login_state import OAuthLoginState
from app.models.profile_import import ProfileImportRow
from app.models.user import User
from app.profiles.diff import diff_snapshots
from app.profiles.linkedin import map_linkedin_userinfo_to_snapshot
from app.profiles.parsers.documents import (
    UnsupportedDocumentError,
    extract_docx_text,
    extract_pdf_text,
    sniff_upload_kind,
)
from app.profiles.parsers.paste import parse_paste, parsed_profile_to_snapshot
from app.profiles.schema import (
    ImportSource,
    ImportStatus,
    LinkedInSyncStatus,
    ProfileSnapshot,
    ProfileSource,
)
from app.profiles.service import (
    commit_snapshot,
    get_active_snapshot,
    get_snapshot_by_version,
    list_snapshots,
    store_raw_input,
)
from app.schemas.auth import LinkedInStartResponse, MessageResponse
from app.schemas.profile import (
    CommitImportRequest,
    FieldChange,
    ImportPasteRequest,
    ImportResponse,
    ListItemChange,
    SnapshotDetail,
    SnapshotDiff,
    SnapshotSummary,
    SyncResponse,
)
from app.security.crypto import decrypt, encrypt
from app.services.audit import record_audit_event
from app.services.linkedin import (
    LinkedInOAuthError,
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_userinfo,
    generate_nonce,
    generate_pkce_pair,
    generate_state,
    verify_id_token,
)
from app.settings import settings

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

OAUTH_STATE_TTL_MINUTES = 10


def _document_kind_to_source(kind: str) -> ImportSource:
    return ImportSource.UPLOAD_PDF if kind == "pdf" else ImportSource.UPLOAD_DOCX


async def _find_linkedin_identity(db: AsyncSession, *, user_id: uuid.UUID) -> OAuthIdentity | None:
    result = await db.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user_id, OAuthIdentity.provider == "linkedin"
        )
    )
    return result.scalar_one_or_none()


async def _find_connection(
    db: AsyncSession, *, oauth_identity_id: uuid.UUID
) -> LinkedInConnection | None:
    result = await db.execute(
        select(LinkedInConnection).where(LinkedInConnection.oauth_identity_id == oauth_identity_id)
    )
    return result.scalar_one_or_none()


@router.post("/connect", response_model=LinkedInStartResponse)
async def connect(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> LinkedInStartResponse:
    verifier, challenge = generate_pkce_pair()
    state = generate_state()
    nonce = generate_nonce()
    db.add(
        OAuthLoginState(
            state=state,
            code_verifier=verifier,
            nonce=nonce,
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(minutes=OAUTH_STATE_TTL_MINUTES),
        )
    )
    await db.commit()
    try:
        url = build_authorization_url(
            state=state,
            nonce=nonce,
            code_challenge=challenge,
            redirect_uri=settings.linkedin_profile_redirect_uri,
        )
    except LinkedInOAuthError as exc:
        raise ApiError(ErrorCode.INTERNAL, str(exc)) from exc
    return LinkedInStartResponse(authorization_url=url)


@router.get("/connect/callback", response_model=MessageResponse)
async def connect_callback(
    code: str,
    state: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    result = await db.execute(select(OAuthLoginState).where(OAuthLoginState.state == state))
    login_state = result.scalar_one_or_none()
    if (
        login_state is None
        or login_state.expires_at < datetime.now(UTC)
        or login_state.user_id != user.id
    ):
        raise ApiError(ErrorCode.TOKEN_EXPIRED, "OAuth state expired or unknown")
    await db.delete(login_state)

    try:
        tokens = await exchange_code_for_tokens(
            code=code,
            code_verifier=login_state.code_verifier,
            redirect_uri=settings.linkedin_profile_redirect_uri,
        )
        claims = await verify_id_token(tokens["id_token"], expected_nonce=login_state.nonce)
    except (LinkedInOAuthError, KeyError) as exc:
        await db.commit()
        raise ApiError(ErrorCode.INVALID_CREDENTIALS, f"LinkedIn connect failed: {exc}") from exc

    provider_user_id = claims["sub"]
    identity = await _find_linkedin_identity(db, user_id=user.id)
    if identity is None:
        other_result = await db.execute(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == "linkedin",
                OAuthIdentity.provider_user_id == provider_user_id,
            )
        )
        other = other_result.scalar_one_or_none()
        if other is not None and other.user_id != user.id:
            raise ApiError(
                ErrorCode.FORBIDDEN,
                "This LinkedIn account is already linked to a different LinkSavvy account.",
            )
        identity = other

    if identity is None:
        identity = OAuthIdentity(
            user_id=user.id,
            provider="linkedin",
            provider_user_id=provider_user_id,
            scopes="openid profile email",
            connected_at=datetime.now(UTC),
        )
        db.add(identity)
        await db.flush()

    access_token = tokens.get("access_token")
    if access_token:
        identity.access_token_encrypted = encrypt(access_token)
    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        identity.refresh_token_encrypted = encrypt(refresh_token)
    expires_in = tokens.get("expires_in")
    if isinstance(expires_in, int):
        identity.expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    connection = await _find_connection(db, oauth_identity_id=identity.id)
    if connection is None:
        connection = LinkedInConnection(
            user_id=user.id,
            oauth_identity_id=identity.id,
            scopes="openid profile email",
            sync_status=LinkedInSyncStatus.NEVER_SYNCED.value,
        )
        db.add(connection)
    await db.flush()

    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="profile.linkedin_connect",
        target_type="linkedin_connection",
        target_id=str(connection.id),
    )
    await db.commit()
    return MessageResponse(message="LinkedIn connected.")


@router.post("/sync", response_model=SyncResponse)
async def sync(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SyncResponse:
    identity = await _find_linkedin_identity(db, user_id=user.id)
    if identity is None or not identity.access_token_encrypted:
        raise ApiError(
            ErrorCode.NOT_FOUND,
            "LinkedIn is not connected yet. Connect it first via POST /profile/connect.",
        )
    connection = await _find_connection(db, oauth_identity_id=identity.id)

    access_token = decrypt(identity.access_token_encrypted)
    try:
        claims = await fetch_userinfo(access_token)
    except LinkedInOAuthError as exc:
        if connection is not None:
            connection.sync_status = LinkedInSyncStatus.ERROR.value
            await db.commit()
        raise ApiError(ErrorCode.INTERNAL, f"LinkedIn sync failed: {exc}") from exc

    snapshot, available_fields = map_linkedin_userinfo_to_snapshot(claims)

    if connection is not None:
        connection.last_synced_at = datetime.now(UTC)
        connection.sync_status = LinkedInSyncStatus.OK.value
        connection.api_fields_available = available_fields
    await db.commit()

    return SyncResponse(draft=snapshot, available_fields=available_fields)


@router.post("/sync/commit", response_model=SnapshotSummary)
async def commit_sync(
    payload: CommitImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SnapshotSummary:
    row = await commit_snapshot(
        db, user=user, payload=payload.payload, source=ProfileSource.LINKEDIN_API
    )
    await db.commit()
    return SnapshotSummary.model_validate(row)


@router.post("/imports", response_model=ImportResponse)
async def create_paste_import(
    payload: ImportPasteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportResponse:
    if not payload.text.strip():
        raise ApiError(ErrorCode.VALIDATION_FAILED, "Pasted text is empty.")
    raw_bytes = payload.text.encode("utf-8")
    if len(raw_bytes) > settings.profile_paste_max_bytes:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            f"Pasted text is too long (max {settings.profile_paste_max_bytes} bytes).",
        )

    blob = await store_raw_input(db, content=raw_bytes, content_type="text/plain")
    import_row = ProfileImportRow(
        user_id=user.id,
        source=ImportSource.PASTE.value,
        status=ImportStatus.PARSING.value,
        raw_input_ref=blob.id,
    )
    db.add(import_row)
    await db.flush()

    parsed = parse_paste(payload.text)
    snapshot = parsed_profile_to_snapshot(parsed, source=ProfileSource.PASTE)

    import_row.draft_payload = snapshot.model_dump(mode="json")
    import_row.parse_warnings = list(parsed.warnings)
    import_row.status = ImportStatus.NEEDS_REVIEW.value
    await db.commit()

    return ImportResponse(
        import_id=str(import_row.id),
        status=import_row.status,
        draft=snapshot,
        parse_warnings=parsed.warnings,
    )


@router.post("/imports/upload", response_model=ImportResponse)
async def create_upload_import(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportResponse:
    content = await file.read()
    if len(content) > settings.profile_upload_max_bytes:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED,
            f"File is too large (max {settings.profile_upload_max_bytes} bytes).",
        )

    content_type = file.content_type or ""
    try:
        kind = sniff_upload_kind(content, content_type)
    except UnsupportedDocumentError as exc:
        raise ApiError(ErrorCode.VALIDATION_FAILED, str(exc)) from exc

    source = _document_kind_to_source(kind)
    blob = await store_raw_input(db, content=content, content_type=content_type)

    try:
        extracted_text = extract_pdf_text(content) if kind == "pdf" else extract_docx_text(content)
    except UnsupportedDocumentError as exc:
        import_row = ProfileImportRow(
            user_id=user.id,
            source=source.value,
            status=ImportStatus.FAILED.value,
            raw_input_ref=blob.id,
            error=str(exc),
        )
        db.add(import_row)
        await db.commit()
        raise ApiError(ErrorCode.VALIDATION_FAILED, str(exc)) from exc

    import_row = ProfileImportRow(
        user_id=user.id,
        source=source.value,
        status=ImportStatus.PARSING.value,
        raw_input_ref=blob.id,
    )
    db.add(import_row)
    await db.flush()

    parsed = parse_paste(extracted_text)
    snapshot = parsed_profile_to_snapshot(parsed, source=ProfileSource(source.value))

    import_row.draft_payload = snapshot.model_dump(mode="json")
    import_row.parse_warnings = list(parsed.warnings)
    import_row.status = ImportStatus.NEEDS_REVIEW.value
    await db.commit()

    return ImportResponse(
        import_id=str(import_row.id),
        status=import_row.status,
        draft=snapshot,
        parse_warnings=parsed.warnings,
    )


@router.post("/imports/{import_id}/commit", response_model=SnapshotSummary)
async def commit_import(
    import_id: uuid.UUID,
    payload: CommitImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SnapshotSummary:
    import_row = await db.get(ProfileImportRow, import_id)
    if import_row is None or import_row.user_id != user.id:
        raise ApiError(ErrorCode.NOT_FOUND, "Import not found")
    if import_row.status == ImportStatus.COMMITTED.value:
        raise ApiError(ErrorCode.VALIDATION_FAILED, "This import has already been committed.")
    if import_row.status == ImportStatus.FAILED.value:
        raise ApiError(
            ErrorCode.VALIDATION_FAILED, "This import failed to parse and cannot be committed."
        )

    source = ProfileSource(import_row.source)
    row = await commit_snapshot(db, user=user, payload=payload.payload, source=source)
    import_row.status = ImportStatus.COMMITTED.value
    await db.commit()
    return SnapshotSummary.model_validate(row)


@router.put("/snapshot", response_model=SnapshotSummary)
async def put_manual_snapshot(
    payload: ProfileSnapshot,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SnapshotSummary:
    row = await commit_snapshot(db, user=user, payload=payload, source=ProfileSource.MANUAL)
    await db.commit()
    return SnapshotSummary.model_validate(row)


@router.get("/snapshot", response_model=SnapshotDetail)
async def get_current_snapshot(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SnapshotDetail:
    row = await get_active_snapshot(db, user_id=user.id)
    if row is None:
        raise ApiError(ErrorCode.NOT_FOUND, "No profile snapshot has been committed yet.")
    return SnapshotDetail(
        version=row.version,
        source=row.source,
        captured_at=row.captured_at,
        completeness_score=row.completeness_score,
        is_active=row.is_active,
        payload=ProfileSnapshot.model_validate(row.payload),
    )


@router.get("/snapshots", response_model=list[SnapshotSummary])
async def get_snapshots(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[SnapshotSummary]:
    rows = await list_snapshots(db, user_id=user.id)
    return [SnapshotSummary.model_validate(row) for row in rows]


@router.get("/snapshots/{version_a}/diff/{version_b}", response_model=SnapshotDiff)
async def get_snapshot_diff(
    version_a: int,
    version_b: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SnapshotDiff:
    row_a = await get_snapshot_by_version(db, user_id=user.id, version=version_a)
    row_b = await get_snapshot_by_version(db, user_id=user.id, version=version_b)
    if row_a is None or row_b is None:
        raise ApiError(ErrorCode.NOT_FOUND, "One or both snapshot versions were not found.")

    snapshot_a = ProfileSnapshot.model_validate(row_a.payload)
    snapshot_b = ProfileSnapshot.model_validate(row_b.payload)
    result = diff_snapshots(snapshot_a, snapshot_b)
    return SnapshotDiff(
        from_version=version_a,
        to_version=version_b,
        field_changes=[FieldChange(**dataclasses.asdict(fc)) for fc in result.field_changes],
        list_changes={
            name: [ListItemChange(**dataclasses.asdict(lc)) for lc in items]
            for name, items in result.list_changes.items()
        },
    )
