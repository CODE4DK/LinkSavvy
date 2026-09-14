/**
 * Turns any `QUOTA_EXCEEDED` (402) response, anywhere in the app, into
 * the contextual paywall the spec asks for: what was hit, what pro gives,
 * and a one-click upgrade that returns the user to exactly what they were
 * doing. `ApiError` reports every 402 to `setQuotaExceededHandler` (see
 * lib/api.ts) the moment it's thrown -- this provider is the one
 * subscriber, mounted once at the app root.
 */

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { ApiError } from "./api";
import { setQuotaExceededHandler } from "./api";
import { createCheckout } from "./billing-api";

interface QuotaDetails {
  metric?: string;
  used?: number;
  limit?: number;
  window?: string;
  resets_at?: string;
  upgrade_required?: boolean;
}

interface PaywallContextValue {
  dismiss: () => void;
}

const PaywallContext = createContext<PaywallContextValue | null>(null);

const METRIC_LABELS: Record<string, string> = {
  ai_runs: "AI runs",
  tool_runs: "tool runs",
  assistant_messages: "assistant messages",
  saved_assets: "saved items",
  audits: "audits",
  resume_analyses: "resume analyses",
};

function metricLabel(metric: string | undefined): string {
  if (!metric) return "this feature";
  return METRIC_LABELS[metric] ?? metric.replace(/_/g, " ");
}

export function PaywallProvider({ children }: { children: ReactNode }) {
  const [error, setError] = useState<ApiError | null>(null);
  const [returnTo, setReturnTo] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setQuotaExceededHandler((err) => {
      setError(err);
      setReturnTo(location.pathname + location.search);
    });
    return () => setQuotaExceededHandler(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refresh the closure's captured location each render, not just on mount
  }, [location.pathname, location.search]);

  const value = useMemo(() => ({ dismiss: () => setError(null) }), []);

  const details = (error?.details ?? {}) as QuotaDetails;

  async function handleUpgrade() {
    setStarting(true);
    try {
      const checkout = await createCheckout({ plan: "pro", interval: "month" });
      if (returnTo) sessionStorage.setItem("post-checkout-return-to", returnTo);
      window.location.href = checkout.checkout_url;
    } finally {
      setStarting(false);
    }
  }

  return (
    <PaywallContext.Provider value={value}>
      {children}
      {error && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="paywall-title"
        >
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <h2 id="paywall-title" className="text-lg font-semibold text-fg">
              You've hit your {metricLabel(details.metric)} limit
            </h2>
            <p className="mt-2 text-sm text-fg/80">
              {details.used !== undefined && details.limit !== undefined
                ? `You've used ${details.used} of ${details.limit} ${metricLabel(
                    details.metric,
                  )} this ${details.window ?? "period"}.`
                : error.message}
            </p>
            <div className="mt-4 rounded-md bg-accent/10 p-3 text-sm text-fg">
              <p className="font-medium">Pro gives you:</p>
              <ul className="mt-1 list-inside list-disc space-y-0.5 text-fg/80">
                <li>Much higher limits on every metric, every day</li>
                <li>Priority access to advanced AI models</li>
                <li>Unlimited saved workspace items</li>
              </ul>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setError(null)}
                className="rounded-md px-3 py-2 text-sm text-fg/70 hover:bg-border/40"
              >
                Not now
              </button>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  navigate("/billing/pricing");
                }}
                className="rounded-md border border-border px-3 py-2 text-sm text-fg hover:bg-border/40"
              >
                See plans
              </button>
              <button
                type="button"
                disabled={starting}
                onClick={handleUpgrade}
                className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-foreground disabled:opacity-60"
              >
                {starting ? "Starting checkout…" : "Upgrade to pro"}
              </button>
            </div>
          </div>
        </div>
      )}
    </PaywallContext.Provider>
  );
}

export function usePaywall(): PaywallContextValue {
  const ctx = useContext(PaywallContext);
  if (!ctx) throw new Error("usePaywall must be used within a PaywallProvider");
  return ctx;
}
