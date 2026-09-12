"""LinkedIn OpenID Connect sign-in (authentication only).

Only `openid profile email` is requested. This module never touches
LinkedIn's web UI, HTML, or non-API endpoints — it speaks exclusively to
LinkedIn's documented OAuth/OIDC hosts.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Any, cast
from urllib.parse import urlencode

import httpx
import jwt

from app.settings import settings

AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
JWKS_URL = "https://www.linkedin.com/oauth/openid/jwks"
ISSUER = "https://www.linkedin.com/oauth"
SCOPE = "openid profile email"


class LinkedInOAuthError(Exception):
    pass


def generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def build_authorization_url(*, state: str, nonce: str, code_challenge: str) -> str:
    if not settings.linkedin_client_id or not settings.linkedin_redirect_uri:
        raise LinkedInOAuthError("LinkedIn OAuth is not configured")
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": SCOPE,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(*, code: str, code_verifier: str) -> dict[str, Any]:
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise LinkedInOAuthError("LinkedIn OAuth is not configured")
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.linkedin_redirect_uri,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
        "code_verifier": code_verifier,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        raise LinkedInOAuthError(f"token exchange failed: {response.text}")
    return cast(dict[str, Any], response.json())


async def fetch_jwks() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(JWKS_URL)
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


async def verify_id_token(id_token: str, *, expected_nonce: str) -> dict[str, Any]:
    jwks = await fetch_jwks()
    header = jwt.get_unverified_header(id_token)
    matching = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
    if matching is None:
        raise LinkedInOAuthError("no matching JWKS key for id_token")
    public_key = jwt.PyJWK.from_dict(matching).key
    try:
        claims = jwt.decode(
            id_token,
            key=public_key,
            algorithms=["RS256"],
            audience=settings.linkedin_client_id,
            issuer=ISSUER,
        )
    except jwt.PyJWTError as exc:
        raise LinkedInOAuthError(f"invalid id_token: {exc}") from exc
    if claims.get("nonce") != expected_nonce:
        raise LinkedInOAuthError("nonce mismatch")
    return claims
