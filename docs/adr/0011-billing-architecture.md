# 11. Billing architecture

Date: 2026-12-05

## Status

Accepted

## Context

Phase 10 adds subscriptions, payments, and a webhook pipeline against
two payment providers (Stripe for most of the world, Razorpay for
India, per CLAUDE.md's region-routing requirement) without ever trusting
a client redirect to grant paid access, without duplicating entitlement
logic per provider, and without losing a user's saved work when they
downgrade or their card fails. This ADR records the provider
abstraction, the entitlement/enforcement design, and the webhook
idempotency guarantee everything else depends on.

## Decisions

**One `BillingProvider` interface, mirroring the Phase 3 AI provider
pattern.** `app/billing/providers/base.py` defines `create_checkout`,
`create_portal_session`, `cancel`, `change_plan`, `delete_customer`, and
the webhook-handling pair below — `stripe.py` and `razorpay.py`
implement it against their respective SDKs/APIs, and `fake.py` is the
one every test runs against (`tests/conftest.py`'s
`_fake_billing_providers` autouse fixture), the same zero-network-calls
guarantee the AI gateway's own fake provider gives the whole suite.
Region routing (`app/billing/providers/registry.py::provider_name_for_billing_country`)
is a pure function of `User.billing_country`, decided once at first
checkout and never mutated afterward — moving a subscriber from one
provider to another means cancelling one subscription and starting a
fresh one, not migrating a row, since the two providers have no shared
identity for the same underlying subscription.

**`parse_webhook` and `parse_payload` are separate methods.**
`parse_webhook(raw_body, signature)` verifies the provider's signature
and returns a `NormalisedEvent`; `parse_payload(payload)` does the same
normalisation from an already-verified stored payload, with no signature
to check. This split exists specifically so admin webhook replay
(`app/admin/subscriptions.py`, `app.billing.service.reprocess_stored_event`)
can re-run a stored, previously-verified event without needing a
signature that no longer exists to re-verify — the same shape every
real provider's own "resend webhook" tooling has. The known cost: replaying
an event that already fully succeeded (rather than one that failed
outright) can duplicate a side-effect row like `Payment`; this is
documented at the call site and in `docs/runbook.md` "Webhook replay"
rather than solved with a broader idempotency scheme, since real
providers carry the identical caveat.

**Every provider emits one normalised event vocabulary.**
`NormalisedEventType` (`subscription.activated`, `.renewed`,
`.payment_failed`, `.cancelled`, `.plan_changed`, `refund.issued`) is
what `app.billing.service._apply_normalised_event` actually branches on
— Stripe's and Razorpay's own wildly different webhook event names never
leak past their own adapter. Adding a third provider in a future phase
means writing one adapter that emits this same vocabulary, not touching
the entitlement logic at all.

**Idempotency is keyed on `provider_event_id`, and persisted before
anything else happens.** `process_webhook_event` writes the
`WebhookEvent` row (unique on `provider_event_id`) inside the same
transaction as processing it; a duplicate delivery (every provider's own
retry policy assumes at-least-once delivery) short-circuits on the
unique constraint before any entitlement changes run twice. Out-of-order
delivery is handled by period timestamps, not delivery order: a
`subscription.renewed` event with an earlier `current_period_end` than
what's already stored is a no-op, not a regression, so a delayed retry
can never roll back a later, already-applied state.

**The webhook is the *only* place entitlements are granted — never a
client redirect.** `apply_entitlements` (`app/billing/entitlements.py`)
is called exclusively from `process_webhook_event`/
`reprocess_stored_event`. The frontend's post-checkout return page
(`CheckoutReturnPage.tsx`) polls `GET /billing/subscription` instead of
trusting its own redirect URL's query string, so a user closing the tab
before the webhook lands (or a network blip losing the redirect
entirely) can never desync the UI from what actually happened — the
poll just keeps showing "processing" until the webhook, which will
arrive independently of whether the browser round-trip succeeded, lands.

**A downgrade takes effect at period end, never immediately.**
`cancel_subscription` sets `cancel_at_period_end=True`; the actual plan
change happens in `app/billing/period_sweep.py`'s scheduler once
`current_period_end` passes — a user who paid for the current period
keeps what they paid for until it's actually over. The same scheduler
handles `past_due`'s grace period (`past_due_grace_period_days`,
default 7): full access continues through the grace window so one
transient card decline doesn't lock someone out mid-renewal, then drops
to free the same way a real cancellation does.

**Over-limit assets become read-only, never deleted.**
`_freeze_overflow_assets` (`app/billing/entitlements.py`) sets
`Asset.read_only = True` on whatever exceeds the free tier's storage cap
(`FREE_ASSET_STORAGE_CAP = 20`) the moment a downgrade actually takes
effect — oldest-created assets are frozen first, so what a user
interacted with most recently stays editable. `patch_asset` raises
`FORBIDDEN` with `details={"upgrade_required": True}` on a frozen asset,
which the frontend turns into a contextual paywall rather than a bare
error. Re-upgrading calls `_unfreeze_assets` and reverses it exactly —
nothing is ever deleted for being over a plan's limit, only made
read-only, since deleting a user's own content because they stopped
paying is a far worse experience than temporarily restricting edits to it.

## Consequences

- A third payment provider (a future phase's requirement, not this
  one's) is a new adapter implementing `BillingProvider` and emitting
  the existing `NormalisedEventType` vocabulary — `service.py`'s
  entitlement logic needs no changes.
- Webhook replay from the admin panel is safe for a failed event and
  merely redundant (not corrupting) for a successful one that gets
  replayed anyway — the caveat is disclosed, not engineered away, since
  real providers accept the same trade-off.
- The checkout-return page's polling loop means there's a brief window
  (typically seconds, bounded by the provider's own webhook delivery
  latency) where a just-paid user sees "processing" rather than instant
  confirmation — a deliberate trade against ever showing a false
  "you're upgraded" before the webhook actually confirms it.
- Region routing being immutable means a subscriber who moves countries
  keeps their original provider for the life of that subscription; a
  future phase wanting "detected country changed, offer to switch
  providers" is new, explicit UX, not an automatic behavior this
  architecture already supports.
