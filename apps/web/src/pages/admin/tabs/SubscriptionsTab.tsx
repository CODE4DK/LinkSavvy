import { useEffect, useState } from "react";
import type { AdminSubscriptionResponse, WebhookEventResponse } from "@linksavvy/contracts";
import { getWebhookHistory, listSubscriptions, replayWebhook } from "@/lib/admin-api";

export function SubscriptionsTab() {
  const [status, setStatus] = useState("");
  const [subscriptions, setSubscriptions] = useState<AdminSubscriptionResponse[]>([]);
  const [selected, setSelected] = useState<AdminSubscriptionResponse | null>(null);
  const [webhooks, setWebhooks] = useState<WebhookEventResponse[]>([]);

  async function refresh() {
    setSubscriptions(await listSubscriptions(status || undefined));
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  async function openWebhooks(subscription: AdminSubscriptionResponse) {
    setSelected(subscription);
    setWebhooks(await getWebhookHistory(subscription.id));
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-fg"
        >
          <option value="">Any status</option>
          <option value="trialing">Trialing</option>
          <option value="active">Active</option>
          <option value="past_due">Past due</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <table className="mt-4 w-full text-sm">
          <tbody>
            {subscriptions.map((sub) => (
              <tr key={sub.id} className="border-t border-border">
                <td className="py-2">
                  <button
                    type="button"
                    onClick={() => openWebhooks(sub)}
                    className="text-left text-primary underline"
                  >
                    {sub.provider} — {sub.plan}
                  </button>
                </td>
                <td className="py-2 text-fg-muted">{sub.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-fg">Webhook history</h3>
          <ul className="mt-2 space-y-2 text-xs">
            {webhooks.length === 0 && <li className="text-fg-muted">No webhook events found.</li>}
            {webhooks.map((event) => (
              <li key={event.id} className="border-b border-border pb-2">
                <p className="text-fg">
                  {event.type} — <span className="text-fg-muted">{event.status}</span>
                </p>
                <p className="text-fg-muted">{new Date(event.received_at).toLocaleString()}</p>
                {event.error && <p className="text-danger">{event.error}</p>}
                {event.status !== "processed" && (
                  <button
                    type="button"
                    onClick={async () => {
                      await replayWebhook(event.id);
                      await openWebhooks(selected);
                    }}
                    className="mt-1 rounded-md border border-border px-2 py-0.5 text-fg"
                  >
                    Replay
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
