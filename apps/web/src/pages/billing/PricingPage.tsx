/**
 * Built straight from `GET /api/v1/billing/pricing` (which is itself
 * built from `plan_limits` -- see app/routers/billing.py) so this page
 * can never claim a limit the backend doesn't actually enforce.
 */

import { useEffect, useState } from "react";
import type { PlanLimitResponse } from "@linksavvy/contracts";
import { getPricing, createCheckout } from "@/lib/billing-api";

const METRIC_LABELS: Record<string, string> = {
  ai_runs: "AI runs",
  tool_runs: "Tool runs",
  assistant_messages: "Assistant messages",
  saved_assets: "Saved workspace items",
  audits: "Audits",
  resume_analyses: "Resume analyses",
};

function formatLimit(row: PlanLimitResponse): string {
  const label = METRIC_LABELS[row.metric] ?? row.metric.replace(/_/g, " ");
  return `${row.limit_value.toLocaleString()} ${label} / ${row.window}`;
}

export function PricingPage() {
  const [limits, setLimits] = useState<PlanLimitResponse[] | null>(null);
  const [starting, setStarting] = useState<"month" | "year" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPricing().then((res) => setLimits(res.limits));
  }, []);

  async function upgrade(interval: "month" | "year") {
    setStarting(interval);
    setError(null);
    try {
      const checkout = await createCheckout({ plan: "pro", interval });
      window.location.href = checkout.checkout_url;
    } catch {
      setError("Couldn't start checkout. Please try again in a moment.");
      setStarting(null);
    }
  }

  const freeLimits = limits?.filter((row) => row.plan === "free") ?? [];
  const proLimits = limits?.filter((row) => row.plan === "pro") ?? [];

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-semibold text-fg">Plans</h1>
      <p className="mt-1 text-sm text-fg-muted">
        Everything on the free plan works without connecting LinkedIn or paying anything. Pro
        raises every limit and unlocks priority AI models.
      </p>

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <div className="rounded-lg border border-border p-6">
          <h2 className="text-lg font-semibold text-fg">Free</h2>
          <p className="mt-1 text-2xl font-bold text-fg">$0</p>
          <ul className="mt-4 space-y-2 text-sm text-fg-muted">
            {freeLimits.map((row) => (
              <li key={row.metric}>{formatLimit(row)}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-primary p-6">
          <h2 className="text-lg font-semibold text-fg">Pro</h2>
          <p className="mt-1 text-2xl font-bold text-fg">$29/mo or $290/yr</p>
          <ul className="mt-4 space-y-2 text-sm text-fg-muted">
            {proLimits.map((row) => (
              <li key={row.metric}>{formatLimit(row)}</li>
            ))}
          </ul>
          <div className="mt-6 flex flex-col gap-2">
            <button
              type="button"
              disabled={starting !== null}
              onClick={() => upgrade("month")}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
            >
              {starting === "month" ? "Starting checkout…" : "Upgrade monthly"}
            </button>
            <button
              type="button"
              disabled={starting !== null}
              onClick={() => upgrade("year")}
              className="rounded-md border border-border px-4 py-2 text-sm font-medium text-fg disabled:opacity-60"
            >
              {starting === "year" ? "Starting checkout…" : "Upgrade yearly (save ~17%)"}
            </button>
          </div>
          {error && <p className="mt-2 text-sm text-danger">{error}</p>}
        </div>
      </div>
    </div>
  );
}
