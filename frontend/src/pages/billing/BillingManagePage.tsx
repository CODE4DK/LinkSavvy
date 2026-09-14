import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { PaymentResponse, SubscriptionResponse } from "@/contracts";
import {
  cancelSubscription,
  createPortalSession,
  getSubscription,
  listPayments,
} from "@/lib/billing-api";
import { ApiError } from "@/lib/api";

const CANCEL_REASONS = [
  "Too expensive",
  "Not using it enough",
  "Missing a feature I need",
  "Switching to another tool",
  "Just trying it out",
  "Other",
];

export function BillingManagePage() {
  const [subscription, setSubscription] = useState<SubscriptionResponse | null>(null);
  const [payments, setPayments] = useState<PaymentResponse[]>([]);
  const [portalError, setPortalError] = useState<string | null>(null);
  const [showCancelSurvey, setShowCancelSurvey] = useState(false);
  const [cancelReason, setCancelReason] = useState(CANCEL_REASONS[0]);
  const [cancelling, setCancelling] = useState(false);

  async function refresh() {
    const [sub, pay] = await Promise.all([getSubscription(), listPayments()]);
    setSubscription(sub);
    setPayments(pay);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function openPortal() {
    setPortalError(null);
    try {
      const { portal_url } = await createPortalSession();
      window.location.href = portal_url;
    } catch (err) {
      setPortalError(
        err instanceof ApiError
          ? err.message
          : "Billing portal isn't available for this account's payment method.",
      );
    }
  }

  async function confirmCancel() {
    setCancelling(true);
    try {
      const updated = await cancelSubscription({ at_period_end: true, reason: cancelReason });
      setSubscription(updated);
      setShowCancelSurvey(false);
    } finally {
      setCancelling(false);
    }
  }

  if (!subscription) {
    return <div className="p-6 text-sm text-fg-muted">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-semibold text-fg">Manage subscription</h1>

      <div className="mt-6 rounded-lg border border-border p-6">
        <p className="text-sm text-fg-muted">Current plan</p>
        <p className="text-xl font-semibold capitalize text-fg">{subscription.plan}</p>
        <p className="mt-1 text-sm text-fg-muted">
          Status: <span className="capitalize">{subscription.status}</span>
          {subscription.cancel_at_period_end && subscription.current_period_end && (
            <> — cancels on {new Date(subscription.current_period_end).toLocaleDateString()}</>
          )}
        </p>
        {subscription.status === "past_due" && (
          <p className="mt-2 rounded-md bg-warning/10 p-2 text-sm text-warning">
            Your last payment failed. Update your payment method to keep pro access.
          </p>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          {subscription.plan === "free" ? (
            <Link
              to="/billing/pricing"
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            >
              Upgrade to pro
            </Link>
          ) : (
            <>
              <button
                type="button"
                onClick={openPortal}
                className="rounded-md border border-border px-4 py-2 text-sm font-medium text-fg"
              >
                Manage payment method &amp; invoices
              </button>
              {!subscription.cancel_at_period_end && (
                <button
                  type="button"
                  onClick={() => setShowCancelSurvey(true)}
                  className="rounded-md px-4 py-2 text-sm font-medium text-danger"
                >
                  Cancel subscription
                </button>
              )}
            </>
          )}
        </div>
        {portalError && <p className="mt-2 text-sm text-fg-muted">{portalError}</p>}
      </div>

      {showCancelSurvey && (
        <div className="mt-4 rounded-lg border border-border p-6">
          <h2 className="text-sm font-medium text-fg">Before you go — why are you cancelling?</h2>
          <select
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            className="mt-3 w-full rounded-md border border-border bg-bg p-2 text-sm text-fg"
          >
            {CANCEL_REASONS.map((reason) => (
              <option key={reason} value={reason}>
                {reason}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-fg-muted">
            You'll keep pro access until the end of your current billing period.
          </p>
          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowCancelSurvey(false)}
              className="rounded-md px-3 py-2 text-sm text-fg/70"
            >
              Keep my subscription
            </button>
            <button
              type="button"
              disabled={cancelling}
              onClick={confirmCancel}
              className="rounded-md bg-danger px-3 py-2 text-sm font-medium text-danger-foreground disabled:opacity-60"
            >
              {cancelling ? "Cancelling…" : "Confirm cancellation"}
            </button>
          </div>
        </div>
      )}

      <div className="mt-6">
        <h2 className="text-sm font-medium text-fg">Invoices</h2>
        {payments.length === 0 ? (
          <p className="mt-2 text-sm text-fg-muted">No payments yet.</p>
        ) : (
          <table className="mt-2 w-full text-sm">
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id} className="border-t border-border">
                  <td className="py-2 text-fg-muted">
                    {payment.paid_at ? new Date(payment.paid_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="py-2 text-fg">
                    {(payment.amount_minor / 100).toFixed(2)} {payment.currency.toUpperCase()}
                  </td>
                  <td className="py-2 capitalize text-fg-muted">{payment.status}</td>
                  <td className="py-2 text-right">
                    {payment.invoice_url && (
                      <a
                        href={payment.invoice_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary underline"
                      >
                        Invoice
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
