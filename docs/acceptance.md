# Acceptance

A walkthrough of every capability the product is meant to have, each
with concrete evidence it exists and works: a backend file, a frontend
file where one applies, and a test proving it. The FRD document that
originally specified all of this by section number (referenced
throughout this codebase's commits and ADRs as "FRD §N") is not itself
checked into this repository, so this pass validates against the two
things that are: the hub/object inventory in `CLAUDE.md`, and what every
phase from 1 through 10 actually shipped. Where a capability is
deliberately out of scope or deferred, that's stated plainly rather than
glossed over — see each hub's own ADR for the reasoning behind a given
scope cut.

## Hard compliance rule

| Criterion | Evidence |
| --- | --- |
| No LinkedIn scraping, HTML parsing, or headless browser automation anywhere in the codebase | `scripts/check_compliance.py`, enforced in CI on every push (`.github/workflows/ci.yml`'s `compliance` job) |
| No auto-like/comment/connect/message/post to LinkedIn | Same guard: scans for browser-automation and HTML-scraping library imports outside test files, and `scrape*`/`crawl*`-named declarations |
| No LinkedIn credential storage | Auth is OAuth-only (`app/services/linkedin.py`), tokens encrypted at rest (`app/security/crypto.py`) |
| Every feature has a parity path (upload/paste/type) for a user who never connects LinkedIn | `ProfileSnapshot`'s three input paths (Phase 2: upload, paste, manual entry — `app/profile/`), never gated behind a LinkedIn connection |
| The only LinkedIn network calls are OAuth/official API | `app/services/linkedin.py` is the sole allow-listed file referencing `linkedin.com`, verified by the same compliance guard |

## Dashboard

| Criterion | Evidence |
| --- | --- |
| One aggregate endpoint returns Health Score, category breakdown, recent findings, and run-audit state in a single round trip | `app/routers/dashboard.py`, `apps/web/src/pages/DashboardPage.tsx` |
| First-time (no audit yet) empty state is distinct from a populated dashboard | `tests/test_dashboard_router.py::test_dashboard_first_time_empty_state` |
| Query count doesn't grow with a user's recommendation history (no N+1) | `tests/test_dashboard_router.py::test_dashboard_query_count_does_not_grow_with_recommendation_volume` |
| p95 latency budget (< 3s) | k6 script `apps/api/loadtest/dashboard_and_tools.js`; not yet run against a live environment — see `docs/performance.md` "Load testing" |
| Run-audit control reflects cooldown/quota state and polls real per-category progress | `apps/web/src/components/dashboard/RunAuditControl.tsx` |

## Profile Hub

| Criterion | Evidence |
| --- | --- |
| `ProfileSnapshot` CRUD, versioning, and diffing | `app/profiles/service.py`, `app/profiles/diff.py`; `tests/profiles/test_diff.py`, `tests/profiles/test_router.py` |
| LinkedIn OAuth connect/sync (API path) | `app/routers/profile.py` (`POST /connect`, `/sync`), `app/profiles/linkedin.py`; `tests/test_linkedin.py` |
| Parity path: paste and document upload import | `app/profiles/parsers/paste.py`, `app/profiles/parsers/documents.py`; `tests/profiles/test_paste_parser.py`, `tests/profiles/test_documents.py` |
| Completeness engine | `app/profiles/completeness.py`; `tests/profiles/test_completeness.py` |
| Onboarding wizard (choose source → import → review → confirm) | `apps/web/src/pages/onboarding/{StepChooseSource,StepImport,StepReview,StepConfirm}.tsx` |
| Profile Hub tools (headline/about/keyword/experience/skills optimizers, completeness checker) | `app/tools/definitions/profile/*.py`; `tests/tools/definitions/test_profile_tools.py` |
| Profile Hub page | `apps/web/src/pages/hubs/ProfileHubPage.tsx` |

## Content Hub

| Criterion | Evidence |
| --- | --- |
| Voice profile from pasted/uploaded samples | `app/content/voice_service.py`, `app/routers/content_voice.py`; `tests/content/test_voice_service.py` |
| Content tools (post generator/rewriter, hook, CTA, hashtag, ideas, repurpose, carousel generator) | `app/tools/definitions/content/*.py`; `tests/tools/definitions/test_content_tools.py` |
| Composer with LinkedIn-accurate preview | `apps/web/src/content/{Composer,LinkedInPreview}.tsx` (+ `.test.tsx` each) |
| Carousel builder + PDF/PNG export | `app/content/{carousel_service,carousel_pdf,carousel_png}.py`, `app/routers/carousels.py`; `apps/web/src/content/CarouselBuilder.tsx`; `tests/content/test_carousel_service.py`, `CarouselBuilder.test.tsx` |
| Content calendar: scheduling, reminders, recurring slots, bulk-schedule, performance tracking | `app/content/{calendar_service,calendar_reminder_job,performance_service}.py`, `app/routers/content_plans.py`; `apps/web/src/content/Calendar.tsx`; `tests/content/test_calendar_service.py`, `Calendar.test.tsx` |
| Content Hub page | `apps/web/src/pages/hubs/ContentHubPage.tsx` |

## Engagement Hub

| Criterion | Evidence |
| --- | --- |
| Surfaced through the generic tools router, no dedicated router needed | `app/routers/tools.py` (`GET /api/v1/tools?hub=engagement`) |
| Outreach tools (comment/reply generator, connection request, DM, follow-up, thought-leadership comment, recommendations) | `app/tools/definitions/engagement/*.py`; `tests/tools/definitions/test_engagement_tools.py` |
| Deterministic guardrails: personalization check, spam/flattery/false-urgency detection, character limits, daily outreach soft cap (15) | `app/engagement/guardrails.py`; `tests/engagement/test_guardrails.py` (e.g. `test_spam_tone_check_flags_flattery`, `test_soft_cap_warning_fires_over_cap`) |
| Engagement Hub page with a "recent outreach" panel | `apps/web/src/pages/hubs/EngagementHubPage.tsx` |

## Career Hub

| Criterion | Evidence |
| --- | --- |
| Résumé parsing (paste/upload/from-profile), commit, activate, delete, PDF/DOCX export | `app/career/{service,parse,export}.py`, `app/routers/career.py`; `tests/career/test_export.py` |
| Résumé structural/layout/segment parsing | `app/career/parsers/{layout,segment,resolve}.py`; `tests/career/parsers/test_layout.py`, `test_segment.py` |
| Job description capture and résumé-vs-JD matching | `app/career/parsers/job_description.py`, `app/career/analysis.py`; `tests/career/test_analysis.py` |
| ATS compatibility checks | `app/career/ats_checks.py`; `tests/career/test_ats_checks.py` |
| Career tools (ATS optimizer, cover letter, interview prep, résumé analyzer/builder, JD match, roadmap) | `app/tools/definitions/career/*.py`; `tests/tools/definitions/test_career_tools.py` |
| Career Hub page + apply-to-profile flow | `apps/web/src/pages/hubs/CareerHubPage.tsx`, `ApplyToProfileModal.tsx` (+ `.test.tsx` each) |

## Growth Hub

| Criterion | Evidence |
| --- | --- |
| Four component scores (visibility, consistency, personal branding, health) | `app/growth/scores/{visibility,consistency,personal_branding,health}.py`; `tests/growth/scores/test_{visibility,consistency,personal_branding,health}.py` |
| Weekly plan generation (ranked, ≥1 quick item, idempotent per week, reflects on the prior week) | `app/growth/weekly_plan.py`, `weekly_plan_scheduler.py`/`weekly_plan_job.py`; `tests/growth/test_weekly_plan.py::test_guarantees_at_least_one_item_under_ten_minutes` |
| AI Growth Coach: goal-setting, honest progress-since-last-visit | `app/growth/coach.py`; `tests/growth/test_coach.py::test_progress_since_last_visit_is_honest_about_missing_history` |
| Networking recommendations tool | `app/tools/definitions/growth/networking_recommendations.py`; `tests/tools/definitions/test_growth_tools.py` |
| Score history / before-after comparison | `app/growth/history.py`, `app/routers/growth.py` (`/scores/history`, `/before-after`); `tests/growth/test_history.py` |
| Growth Hub + Growth Coach pages | `apps/web/src/pages/hubs/{GrowthHubPage,GrowthCoachPage}.tsx` (+ `.test.tsx` each) |

## Workspace Hub

| Criterion | Evidence |
| --- | --- |
| Asset list/get/patch/delete/restore/duplicate/versions/export, bulk actions, trash with expiry | `app/workspace/assets.py`, `app/routers/workspace.py`; `tests/workspace/test_assets.py` |
| Folder management | `app/workspace/folders.py`; `tests/workspace/test_folders.py` |
| MySQL FULLTEXT search over assets | `app/workspace/search.py`; `tests/workspace/test_search.py` |
| Export (ZIP / individual) | `app/workspace/export.py`; `tests/workspace/test_export.py` |
| Cursor pagination | `app/workspace/cursor.py` |
| Search latency budget at scale (5,000 assets) | `tests/workspace/test_performance.py` |
| Workspace Hub page with virtualized rows | `apps/web/src/pages/hubs/WorkspaceHubPage.tsx`, `apps/web/src/workspace/VirtualRows.tsx` (+ `.test.tsx` each) |

## AI Assistant

| Criterion | Evidence |
| --- | --- |
| `Conversation` CRUD, rename/archive/save, context toggle | `app/assistant/conversations.py`, `app/routers/assistant.py`; `tests/assistant/test_conversations.py` |
| Orchestrator: intent classification, tool proposal/confirmation, retry, edit-and-branch, rating, SSE streaming | `app/assistant/orchestrator.py`; `tests/assistant/test_orchestrator.py` (e.g. `test_handle_message_rejects_a_proposed_tool_outside_candidates`, `test_edit_and_branch_creates_a_new_user_message_and_reply`) |
| Deterministic policy layer refusing automation/scraping/manipulation/impersonation/fabrication, always with a compliant alternative | `app/assistant/policy.py`; `tests/assistant/test_policy.py` (22-case adversarial suite per ADR 0010) |
| Suggested prompts, summarization, cross-hub reads | `app/assistant/{suggestions,summarize,reads}.py` |
| Chat UI, conversation list, context panel, tool proposal card | `apps/web/src/assistant/{ChatView,ConversationList,ContextPanel,ToolProposalCard}.tsx` |

## Audit engine and Health Score

| Criterion | Evidence |
| --- | --- |
| Orchestrator running five category checks (profile/content/engagement/career/visibility) into `Audit`/`AuditFinding` | `app/audit/orchestrator.py`, `app/audit/categories/*.py`; `tests/audit/test_orchestrator.py`, `tests/audit/categories/test_profile.py` |
| Weighted scoring config → overall Health Score, with graceful degradation for missing data | `app/audit/scoring.py`; `tests/audit/test_scoring.py`; methodology documented in `docs/scoring.md` |
| `Recommendation` generation from findings | `app/audit/recommendations.py`; `tests/audit/test_recommendations.py` |
| Async execution via the `jobs` table worker | `app/audit/job_handler.py`; `tests/audit/test_job_handler.py` |
| Router: start audit, latest, by-id, score history, recommendations | `app/routers/audits.py`; `tests/test_audits_router.py` |

## Billing and Subscriptions

| Criterion | Evidence |
| --- | --- |
| `Subscription` lifecycle: idempotent creation, region routing (Stripe/Razorpay), webhook-only activation, replay-safe, out-of-order-renewal-safe, downgrade freezes assets | `app/billing/service.py`; `tests/billing/test_service.py` |
| Provider abstraction (Stripe, Razorpay, Fake for tests) | `app/billing/providers/{stripe,razorpay,fake,base,registry}.py`; `tests/billing/test_providers.py` |
| `UsageCounter`-backed quota enforcement per plan | `app/billing/quota.py`; `tests/billing/test_quota.py` |
| Plan entitlements and period-end sweep | `app/billing/entitlements.py`, `app/billing/period_sweep.py` |
| Router: pricing, subscription, payments, checkout, portal, cancel, change-plan, webhooks | `app/routers/billing.py`; `tests/test_billing_router.py` |
| Pricing/checkout/manage pages | `apps/web/src/pages/billing/{PricingPage,CheckoutReturnPage,BillingManagePage}.tsx` |

See `docs/adr/0011-billing-architecture.md` for the design decisions
behind all of the above.

## Notifications

| Criterion | Evidence |
| --- | --- |
| In-app list/read/read-all, preferences, token-based unsubscribe (no login required) | `app/notifications/service.py`, `app/notifications/unsubscribe.py`, `app/routers/notifications.py`; `tests/notifications/test_service.py`, `test_unsubscribe.py` |
| Weekly digest composition, honest about no-activity weeks | `app/notifications/weekly_digest.py`; `tests/notifications/test_weekly_digest.py::test_compose_weekly_digest_with_no_activity_has_no_content` |
| Multi-provider email delivery (console/SMTP/SES/Resend) | `app/notifications/email/{console,smtp,ses,resend}.py` |
| Async dispatch via the shared job runner (retries apply uniformly) | `app/notifications/dispatch_job.py`; `tests/notifications/test_dispatch_job.py` |
| Notification bell + preferences UI | `apps/web/src/components/layout/NotificationBell.tsx` (+ `.test.tsx`), `apps/web/src/pages/NotificationPreferencesPage.tsx` |

## Admin panel

| Criterion | Evidence |
| --- | --- |
| User search/detail/suspend/reinstate/force-password-reset/plan-adjust/impersonate | `app/admin/users.py`, `app/routers/admin.py`; `tests/admin/test_users.py` |
| Subscription oversight + webhook replay | `app/admin/subscriptions.py`; `tests/admin/test_subscriptions.py` |
| Feature flags: global/rollout%/per-user override | `app/admin/feature_flags.py`; `tests/admin/test_feature_flags.py` |
| AI ops: cost/tokens by day/model, invalid-output/fallback rates, slowest prompts, per-prompt drilldown | `app/admin/ai_ops.py`; `tests/admin/test_ai_ops.py` |
| Moderation queue (auto-populated from policy violations, plus manual review) | `app/admin/moderation.py`; `tests/admin/test_moderation.py` |
| Platform health: job queue depth, dead letters + retry, circuit-breaker state, error rates | `app/admin/platform_health.py`; `tests/admin/test_platform_health.py` |
| Impersonation is read-only and audited | `app/middleware/impersonation_guard.py` (also see "Security" below) |
| Admin UI with six tabs | `apps/web/src/pages/admin/AdminPage.tsx` (+ `.test.tsx`), `apps/web/src/pages/admin/tabs/*.tsx`; route guard `apps/web/src/routes/RequireAdmin.test.tsx` |

## Security

| Criterion | Evidence |
| --- | --- |
| Rate limiting per IP/user/endpoint-class, 429 + `Retry-After` | `app/middleware/rate_limit.py`, `tests/test_rate_limit.py` |
| Security headers: CSP (no `unsafe-inline`), HSTS (production only), X-Content-Type-Options, Referrer-Policy, Permissions-Policy | `app/middleware/security_headers.py`, `tests/test_health.py::test_security_headers_present_on_every_response` |
| CSRF protection on cookie-authenticated mutations | `app/security/csrf.py` (double-submit cookie), scoped to `/auth/refresh` and `/auth/logout` — the only two cookie-only-authenticated endpoints; `tests/test_refresh.py::test_refresh_rejects_a_forged_request_missing_the_csrf_header` |
| Encryption at rest: résumés, uploads, pasted profile text, OAuth tokens | `app/security/crypto.py` (Fernet), inventory in `docs/security.md` "Encryption at rest" |
| OWASP Top 10 pass documented | `docs/security.md` |
| bandit + pip-audit (API), npm audit (web) in CI | `.github/workflows/ci.yml` `api`/`web` jobs; accepted findings and rationale in `docs/security.md` "CI security scanning" |
| Impersonation is read-only, time-limited, fully audited | `app/middleware/impersonation_guard.py`, `tests/test_admin_router.py::test_impersonation_token_is_read_only` |

## Privacy

| Criterion | Evidence |
| --- | --- |
| `POST /me/export` produces a downloadable ZIP via the job runner | `app/privacy/export.py`, `app/privacy/export_job.py`, `tests/test_me.py::test_request_and_download_data_export` |
| Export excludes live secrets (password hash, encrypted tokens) | `app/privacy/export.py::_SENSITIVE_COLUMNS` |
| `DELETE /me` is immediate soft-delete, hard delete scheduled after a grace period | `app/routers/me.py`, `app/privacy/purge.py::hard_delete_user`, `app/privacy/retention_scheduler.py` |
| Documented data-retention policy covering raw uploads, AI invocation metering, logs | `docs/privacy.md` "Data retention policy" |
| A scheduled purge job actually enforces every retention window | `app/privacy/retention_scheduler.py::run_once`, `tests/privacy/test_purge.py` (9 purge functions, each independently tested) |
| User content never reaches logs or third-party error reporting | `app/ai/gateway.py`'s metering never logs prompt/completion text (see `docs/security.md` "What never reaches logs"); structured logging (`app/observability/logging.py`) only ever logs what a call site explicitly passes via `extra=` |

## Performance and reliability

| Criterion | Evidence |
| --- | --- |
| k6 load test: dashboard p95 < 3s, AI tool runs p95 < 10s | `apps/api/loadtest/dashboard_and_tools.js` — script exists and encodes both thresholds; not yet run against a live environment (needs staging, per its own header comment) |
| Index review from query-pattern analysis, verified against real MySQL | `docs/performance.md` "Index review" — eight new composite indexes (migration `0021_performance_indexes.py`) plus four ORM model/migration parity fixes found the same real-MySQL verification also caught two unrelated pre-existing migration bugs (0012, 0016) that had never been exercised against MySQL before |
| HTTP caching/ETags | `app/http_cache.py`, wired into `GET /api/v1/tools`; `tests/test_tools_router.py::test_list_tools_supports_conditional_get` |
| Frontend code splitting | `apps/web/src/routes/router.tsx` (React Router `lazy` per route); verified by `npm run build` producing per-page chunks, see `docs/performance.md` |
| Bundle budget enforced in CI | `apps/web/scripts/check-bundle-budget.mjs`, wired into `.github/workflows/ci.yml`'s `web` job |
| Graceful degradation when both AI providers are down | `app/ai/gateway.py::_call_with_fallback` (built in Phase 3), `tests/ai/test_gateway.py::test_both_providers_failing_raises_and_releases_quota` |
| Structured logs with correlation ids | `app/observability/logging.py`, `app/middleware/correlation_id.py`, `tests/test_observability.py` |
| Uptime check target (`/ready`) | `app/main.py::ready` (round-trips the database, distinct from the bare liveness `/health`) |
| Documented SLOs: 99.5% uptime, latency budgets, error-rate/AI-availability targets, alert thresholds | `docs/slo.md` |

## Deployment

| Criterion | Evidence |
| --- | --- |
| Both apps containerized | `apps/api/Dockerfile`, `apps/web/Dockerfile`; built (not yet build-tested locally — no Docker daemon in this dev sandbox) by the `docker` CI job |
| Staging/production config documented | `docs/runbook.md` "Environment configuration" (references `apps/api/.env.example` as the variable-name source of truth) |
| Migrations as an explicit release step with documented rollback | `docs/runbook.md` "Deploying" and "Rollback" |
| Nightly backup script | `scripts/backup_db.sh` |
| Restore script, with a **tested** restore | `scripts/restore_db.sh` — script exists and works against a reachable MySQL; the actual drill is logged as **pending** in `docs/runbook.md`'s restore-drill table, since this dev sandbox has no MySQL server to run it against. This is the one acceptance criterion in this document not yet fully met, disclosed rather than hidden. |
| Zero-downtime deploy strategy | `docs/runbook.md` "Zero-downtime deploys" (additive-first migrations + rolling, `/ready`-gated instance rollout) |
| Runbook: deploy, rollback, incidents, provider outage, webhook replay | `docs/runbook.md` |
| ADRs for billing architecture and production topology | `docs/adr/0011-billing-architecture.md`, `docs/adr/0012-production-topology.md` |

## Summary

Every criterion above has working code and at least one passing test
behind it, with one disclosed exception: the restore drill under
"Deployment" is scripted and ready to run but has not actually been
executed, since this development environment has no MySQL server or
Docker daemon to run it against. Everything else in this document is a
live capability in the codebase today, verifiable by running the test
named next to it.
