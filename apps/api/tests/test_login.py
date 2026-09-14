from httpx import AsyncClient


async def test_login_succeeds_and_sets_refresh_cookie(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    response = await client.post("/api/v1/auth/login", json=registered_user)
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == registered_user["email"]
    assert "refresh_token" in response.cookies


async def test_login_sets_the_csrf_cookie_readable_from_every_page(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    """Regression test for a real bug a browser-level check caught that
    httpx's flat cookie jar structurally cannot: the CSRF cookie was
    scoped to Path=/api/v1/auth, same as the refresh-token cookie next to
    it. `response.cookies.get(...)` (what every other test uses) ignores
    Path entirely, so that bug passed the whole suite -- a real browser's
    `document.cookie`, which the frontend actually reads this cookie
    through (see apps/web/src/lib/api.ts::readCsrfCookie), only exposes a
    cookie on pages under its Path. Since the SPA's own pages (the
    dashboard, a hub page, settings) don't live under /api/v1/auth, that
    scoping made every refresh past the very first page load send no
    X-CSRF-Token and get rejected. This inspects the raw Set-Cookie
    header, the only way to see the Path attribute at all."""
    response = await client.post("/api/v1/auth/login", json=registered_user)
    assert response.status_code == 200

    set_cookie_headers = response.headers.get_list("set-cookie")
    csrf_header = next(h for h in set_cookie_headers if h.startswith("csrf_token="))
    assert "path=/;" in csrf_header.lower() or csrf_header.lower().endswith("path=/")


async def test_login_rejects_wrong_password(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "wrong-password-1"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_blocks_unverified_email(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "unverified@example.com",
            "password": "correct-horse-99",
            "full_name": "Unverified",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "correct-horse-99"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


async def test_login_rate_limits_after_repeated_failures(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    bad = {"email": registered_user["email"], "password": "wrong-password-1"}
    last = None
    for _ in range(15):
        last = await client.post("/api/v1/auth/login", json=bad)
    assert last is not None
    assert last.status_code == 429
    assert last.json()["error"]["code"] == "RATE_LIMITED"


async def test_me_requires_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


async def test_me_returns_user_and_flags(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    login = await client.post("/api/v1/auth/login", json=registered_user)
    access_token = login.json()["access_token"]

    response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == registered_user["email"]
    assert "hub.profile" in body["feature_flags"]
