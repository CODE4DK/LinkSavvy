# Privacy

What LinkSavvy retains, for how long, and how a user gets their data out or
gets it deleted. This document is the map; the code it describes is the
authority — if the two disagree, `app/privacy/purge.py` and
`app/privacy/retention_scheduler.py` are correct and this file is out of
date.

## Data retention policy

| Data | Retention | Enforced by |
| --- | --- | --- |
| Raw pasted/uploaded profile text or résumé (`ProfileImportBlob`, encrypted at rest) | `profile_import_retention_days` (default 30) after upload | `purge_expired_profile_imports` |
| The **parsed** `ProfileSnapshot` that import produced | Indefinite — this is the user's own profile data, not transient input | Never purged automatically; removed on account deletion |
| AI response cache (`AICache.response`) | Per-prompt `cache_ttl_seconds` (see `app/ai/prompts/*.prompt.md`), typically well under a day | `purge_expired_ai_cache` |
| AI invocation metering (`AIInvocation` — tokens, cost, latency, correlation id; **never** prompt or completion content, see `docs/security.md` "What never reaches logs") | `ai_invocation_payload_retention_days` (default 90) | `purge_old_ai_invocations` |
| Email send log (`EmailLog`) | `log_retention_days` (default 30) | `purge_old_email_logs` |
| Requested data export ZIPs (`DataExport.encrypted_zip`) | 7 days from generation, then the download link 404s and the row is deleted | `purge_expired_data_exports` (TTL set at creation in `app/privacy/export_job.py`) |
| Soft-deleted account (`User.status = "deleted"`) | `account_hard_delete_after_days` (default 30) grace period, then hard-deleted | `find_users_due_for_hard_delete` + `hard_delete_user` |
| `audit_log` (admin action trail) | Indefinite — this is the compliance record of who did what, not user content. An actor's own identity is nulled out (`ondelete="SET NULL"`) the moment they're hard-deleted, so the log never outlives an account as identifying data | N/A |
| Application logs | Never contain user content in the first place (see `docs/security.md`), so no separate log-content retention policy is needed beyond normal infra log rotation |

All of the above run on one interval-based scheduler,
`app/privacy/retention_scheduler.py::run_scheduler`, polling hourly by
default (not the weekly/calendar shape of the other schedulers in this
codebase, since retention is a "how much has piled up since last time"
job). Each sweep logs a `retention_sweep` line with a count per category
whenever it deletes anything.

## Requesting your data (`POST /me/export`)

1. `POST /api/v1/me/export` enqueues a `privacy.export` job through the
   Phase 4 job runner and returns a `job_id` immediately — composing the
   export can take a moment, so this never blocks the request.
2. The job (`app/privacy/export_job.py`) calls
   `app/privacy/export.py::compose_export_zip`, which walks every mapped
   table with a `user_id` column (`Base.registry.mappers`) — the same
   generic approach `hard_delete_user` uses below, so a future phase's new
   table is included automatically without this code needing to change —
   and writes one JSON file per non-empty table into a ZIP, plus an
   `account.json` summary and a `README.txt` explaining the contents.
3. The ZIP is encrypted at rest (`app/security/crypto.py::encrypt_bytes`)
   into `DataExport.encrypted_zip` and expires after 7 days.
4. A `privacy.export_ready` notification fires through the shared
   notification pipeline (in-app + email, per the user's preferences),
   linking to `GET /api/v1/me/export/{export_id}`, which streams the
   decrypted ZIP — 404s if the requester isn't the owner or the export has
   expired.

**Deliberately excluded from the export**, and why:

- Password hash, encrypted OAuth tokens, refresh-token hashes
  (`app/privacy/export.py::_SENSITIVE_COLUMNS`) — a downloadable ZIP is a
  bigger blast radius than the database itself; re-exporting a live
  secret would hand an attacker who compromises the export flow (or the
  user's inbox) a working credential, not just a data record.
- Raw `ProfileImportBlob` ciphertext — transient by design (see the
  retention table above) and not directly keyed by `user_id` (it's
  referenced via `profile_imports.raw_input_ref`); the parsed
  `ProfileSnapshot` it produced, which is what's actually permanent, *is*
  included.

## Deleting your account (`DELETE /me`)

Deletion is two-phase, matching how most privacy regulations expect
"delete my account" to behave — immediate from the user's point of view,
but not an irreversible foot-gun for an accidental click or a compromised
session making the request:

1. **Immediate soft delete.** `DELETE /me` (after re-confirming the
   current password) sets `status = "deleted"` and `deleted_at = now()`.
   The account can no longer log in, and every session is revoked.
2. **Scheduled hard delete.** After `account_hard_delete_after_days` (30
   by default), `app/privacy/purge.py::hard_delete_user` runs:
   - cancels the provider-side billing customer (`delete_customer` on
     whichever of Stripe/Razorpay the user was on) — a failure here is
     logged for manual reconciliation but never blocks the local deletion,
     since the user's own data being gone doesn't depend on the provider
     succeeding;
   - deletes every row in every mapped table with a `user_id` column for
     that user (the same generic walk the export job uses, so a future
     phase's table needs no changes here either);
   - deletes the `users` row itself, at which point each table's own
     `ondelete="CASCADE"` foreign key (declared in its own migration)
     lets MySQL cascade to anything the direct walk didn't reach (a
     message under a conversation, a version under an asset, a finding
     under an audit, and so on).

There is currently no self-service "cancel my deletion" endpoint during
the grace window — a user who changes their mind within the window should
contact support, who can clear `status`/`deleted_at` directly. That's a
deliberate scope cut for this phase, not an oversight; a self-service
"restore my account" flow is a reasonable follow-up.

## Encryption at rest

See `docs/security.md` "Encryption at rest" for the full inventory
(OAuth tokens, uploaded résumés/pasted text, data export ZIPs) and the key
rotation procedure.
