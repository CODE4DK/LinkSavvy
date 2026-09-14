# Service Level Objectives

## Uptime

**Target: 99.5% monthly uptime**, measured as the fraction of external
uptime checks against `GET /ready` (see `app/main.py`) that succeed.
99.5% allows about 3.6 hours of downtime per 30-day month — enough
headroom for a planned maintenance window without an SLO breach, while
still holding the bar most users would expect from a paid product.

`/ready` is deliberately stricter than `/health`: it round-trips the
database, so a check against it fails the moment the app can't actually
serve a real request, not just when the process is technically running.
An external uptime monitor (see `docs/runbook.md` "Monitoring setup" for
the concrete provider/config once one is chosen) should poll `/ready` at
1-minute intervals from at least two regions, and page on N consecutive
failures (not a single blip — see "Alerting" below for why).

## Latency

| Path | Target | Measured by |
| --- | --- | --- |
| Dashboard aggregate (`GET /api/v1/dashboard`) | p95 < 3s | `apps/api/loadtest/dashboard_and_tools.js`, `tests/test_dashboard_router.py::test_dashboard_query_count_does_not_grow_with_recommendation_volume` |
| AI tool run (`POST /api/v1/tools/{tool_id}/run`) | p95 < 10s | `apps/api/loadtest/dashboard_and_tools.js` |
| Everything else | No formal SLO yet — tracked informally via the correlation-id-tagged structured logs (see `docs/performance.md`) | — |

## Error rate

**Target: < 1% of requests return a 5xx**, measured over a rolling 5
minutes. This is deliberately about *our* failures, not client errors —
a spike in 4xx (bad input, expired tokens, quota exceeded) is not an SLO
breach, and conflating the two would hide a real 5xx spike inside noisy
4xx traffic.

The one exception carved out already, by design rather than as an SLO
loophole: `AI_PROVIDER_UNAVAILABLE` (502, both AI providers down — see
`app/ai/gateway.py::AIProviderUnavailable`, tested by
`tests/ai/test_gateway.py`) is graceful degradation, not an application
failure, and is tracked separately as "AI availability" below rather than
counted against the general error-rate SLO.

## AI availability

**Target: < 0.5% of AI invocations end in `AIProviderUnavailable`**
(both the primary and fallback provider failing the same request),
measured from the `ai_invocations` table the admin AI-ops tab already
surfaces (`app/admin/ai_ops.py`). This is a distinct SLO from the
general error rate because it depends on two third-party providers'
uptime, not just ours — the circuit breaker
(`app/ai/circuit_breaker.py`) and provider fallback
(`app/ai/gateway.py::_call_with_fallback`) exist specifically to keep
this number low even when one provider degrades.

## Alerting

Alert policy (see `docs/runbook.md` "Incidents" for what to do once
paged):

- **Page immediately** on: `/ready` failing 3 consecutive checks (≈3
  minutes of confirmed downtime), 5xx rate > 5% over 5 minutes, or the
  job queue's dead-letter count increasing (a job that exhausted its
  retries is a silent failure otherwise — see the admin platform-health
  tab, `app/admin/platform_health.py`).
- **Notify, don't page**, on: 5xx rate between 1-5% over 15 minutes,
  AI-unavailable rate between 0.5-2%, or a circuit breaker opening for
  either AI provider (`app/ai/circuit_breaker.py::snapshot`) — worth a
  human looking soon, not worth waking anyone up.
- **Never alert** on an individual `AIProviderUnavailable` — it's
  designed to happen occasionally and degrade gracefully; only a
  sustained rate is actionable.

Consecutive-failure thresholds (not single-sample) are used throughout on
purpose: a single dropped health check from network jitter is not an
incident, and paging on it trains people to ignore pages.

## What's not covered yet

This document describes the SLOs the system is *designed* to meet, not
a live dashboard measuring them against a real production traffic
history — LinkSavvy has not shipped to production yet as of Phase 10.
Wiring the actual alerting rules into a monitoring provider (Prometheus/
Grafana, Datadog, or similar) is a deployment-time task, tracked in
`docs/runbook.md`, not a code change in this repository.
