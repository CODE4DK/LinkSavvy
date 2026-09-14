/**
 * Where Stripe/Razorpay's hosted checkout redirects back to
 * (settings.billing_checkout_success_path). Never trusts the redirect
 * itself as proof of payment -- the webhook is the only source of truth
 * (see app/billing/service.py) -- so this just polls
 * `GET /billing/subscription` until it reflects "pro", then sends the
 * user back to whatever they were doing before checkout (paywall-context
 * stashes that path in sessionStorage before redirecting out).
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getSubscription } from "@/lib/billing-api";

const POLL_INTERVAL_MS = 1500;
const MAX_ATTEMPTS = 20;

export function CheckoutReturnPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"waiting" | "confirmed" | "timed_out">("waiting");
  const cancelled = params.get("status") === "cancelled";

  useEffect(() => {
    if (cancelled) return;
    let attempts = 0;
    let cancelledEffect = false;

    async function poll() {
      attempts += 1;
      const subscription = await getSubscription().catch(() => null);
      if (cancelledEffect) return;
      if (subscription?.plan === "pro") {
        setStatus("confirmed");
        return;
      }
      if (attempts >= MAX_ATTEMPTS) {
        setStatus("timed_out");
        return;
      }
      setTimeout(poll, POLL_INTERVAL_MS);
    }
    poll();

    return () => {
      cancelledEffect = true;
    };
  }, [cancelled]);

  function continueToApp() {
    const returnTo = sessionStorage.getItem("post-checkout-return-to");
    sessionStorage.removeItem("post-checkout-return-to");
    navigate(returnTo || "/billing/manage");
  }

  if (cancelled) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="text-xl font-semibold text-fg">Checkout cancelled</h1>
        <p className="mt-2 text-sm text-fg-muted">No changes were made to your plan.</p>
        <button
          type="button"
          onClick={continueToApp}
          className="mt-6 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Back to LinkSavvy
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16 text-center">
      {status === "waiting" && (
        <>
          <h1 className="text-xl font-semibold text-fg">Confirming your subscription…</h1>
          <p className="mt-2 text-sm text-fg-muted">
            This usually takes a few seconds while we hear back from the payment provider.
          </p>
        </>
      )}
      {status === "confirmed" && (
        <>
          <h1 className="text-xl font-semibold text-fg">You're on pro 🎉</h1>
          <p className="mt-2 text-sm text-fg-muted">All pro limits and tools are unlocked now.</p>
          <button
            type="button"
            onClick={continueToApp}
            className="mt-6 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            Continue
          </button>
        </>
      )}
      {status === "timed_out" && (
        <>
          <h1 className="text-xl font-semibold text-fg">Still confirming</h1>
          <p className="mt-2 text-sm text-fg-muted">
            Payment can take a little longer to confirm than usual. Check back on the manage
            subscription page in a minute — no need to try checkout again.
          </p>
          <button
            type="button"
            onClick={() => navigate("/billing/manage")}
            className="mt-6 rounded-md border border-border px-4 py-2 text-sm font-medium text-fg"
          >
            Go to manage subscription
          </button>
        </>
      )}
    </div>
  );
}
