# 2. Authentication and session strategy

Date: 2026-09-12

## Status

Accepted

## Context

Phase 01 needs a complete, deployable authentication system: email/password
registration with verification, login, session management, password reset,
and LinkedIn sign-in — built on a stack with no Redis and no separate
session store (MySQL is the sole datastore, per `CLAUDE.md`). It also needs
to support a user who never connects LinkedIn at all (the "parity path"),
and must never touch LinkedIn beyond its official OAuth/API hosts.

## Decisions

**Access/refresh split, refresh token in an httpOnly cookie.** A 15-minute
JWT access token is returned in the response body and kept in memory only
on the client (never `localStorage`, to limit XSS blast radius). A longer-
lived refresh token is set as an httpOnly, `Secure`, `SameSite=Lax` cookie
scoped to `/api/v1/auth`, so it's inaccessible to JavaScript and isn't sent
on cross-site requests.

**Refresh token rotation with reuse detection.** Every refresh issues a new
token and immediately revokes the old one, linking both to a shared
`family_id`. If a token is presented that's already been revoked, the whole
family is revoked and the caller is forced to log in again — the standard
signal that a token was stolen and replayed by an attacker after the
legitimate client already rotated past it.

**Rate limiting lives in MySQL, not Redis.** A `login_attempts` table (added
in this phase, alongside the tables listed in the Phase 01 spec) records
every attempt with a hashed IP and/or normalized email. Exponential backoff
is computed from recent failures in a sliding window. This keeps the limiter
correct across process restarts and multiple API workers without adding a
new datastore, at the cost of a write per attempt — acceptable at this
stage, and reconsidered only if it becomes a hot path.

**Tokens are single-use and stored hashed, never raw.** Email verification
and password reset tokens are random, delivered once via email, and only
their HMAC-SHA256 hash is persisted — mirroring how refresh tokens are
stored. A stolen database dump cannot be replayed as a live verification
link or session.

**LinkedIn sign-in is OpenID Connect, PKCE, and nothing else.** Only
`openid profile email` is requested. PKCE verifier/state/nonce are
persisted server-side (a short-lived `oauth_login_states` table, not
memory, so it works behind multiple workers) and consumed exactly once on
callback. The `id_token` is verified against LinkedIn's own JWKS
(signature, issuer, audience, nonce) before any account is created or
linked. This is authentication only — no scraping, no browser automation,
no stored LinkedIn credentials, consistent with the hard compliance rule in
`CLAUDE.md`. Every capability reachable via LinkedIn sign-in must also be
reachable without it.

**Passwords hashed with argon2id.** `argon2-cffi` with OWASP-baseline cost
parameters (19 MiB memory, 2 iterations). OAuth-only users have a `NULL`
`password_hash` and simply can't use the password-based flows.

**Generic responses to avoid account enumeration.** `register`,
`resend-verification`, and `forgot-password` return the same response
whether or not the email is already registered/verified/exists, and the
timing-sensitive branches (existing-user vs. new-user on register) still
issue the same success response either way.

## Consequences

- No server-side session store means one extra table (`login_attempts`)
  beyond the schema literally listed in the phase spec, and an extra write
  per auth attempt. This is a deliberate trade against introducing Redis.
- Refresh rotation means every silent-refresh cycle costs a database write;
  acceptable for a 15-minute access token lifetime, revisit if the ratio of
  refreshes to real work climbs.
- LinkedIn sign-in cannot be exercised end-to-end in CI or in this sandbox
  (no real client credentials, no live JWKS fetch) — `linkedin_start`
  is covered by a test asserting it fails closed (not silently) when
  unconfigured; the full callback path needs manual verification against a
  real LinkedIn app before Phase 01 ships to real users.
