import { useEffect, useState } from "react";
import type { PreferenceRow } from "@/contracts";
import { getNotificationPreferences, setNotificationPreference } from "@/lib/notifications-api";

const TYPE_LABELS: Record<string, string> = {
  "subscription.activated": "Subscription activated",
  "subscription.renewed": "Subscription renewed",
  "subscription.payment_failed": "Subscription payment failed",
  "subscription.cancelled": "Subscription cancelled",
  "subscription.plan_changed": "Plan changed",
  "billing.payment_failed": "Payment failed",
  "audit.completed": "Audit completed",
  "growth.weekly_report": "Weekly growth report",
  "content.reminder": "Content post reminders",
  "product.update": "Product updates",
  "privacy.export_ready": "Data export ready",
};

export function NotificationPreferencesPage() {
  const [rows, setRows] = useState<PreferenceRow[] | null>(null);

  useEffect(() => {
    getNotificationPreferences().then((res) => setRows(res.preferences));
  }, []);

  async function toggle(row: PreferenceRow) {
    const updated = await setNotificationPreference({
      channel: row.channel,
      type: row.type,
      enabled: !row.enabled,
    });
    setRows(updated.preferences);
  }

  if (!rows) return <div className="p-6 text-sm text-fg-muted">Loading…</div>;

  const types = Array.from(new Set(rows.map((r) => r.type)));

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-semibold text-fg">Notification preferences</h1>
      <p className="mt-1 text-sm text-fg-muted">
        Choose what you hear about, and how. In-app notifications always show in the bell menu;
        email sends a copy to your inbox too.
      </p>

      <table className="mt-6 w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-fg-muted">
            <th className="py-2 font-normal">Type</th>
            <th className="py-2 text-center font-normal">In-app</th>
            <th className="py-2 text-center font-normal">Email</th>
          </tr>
        </thead>
        <tbody>
          {types.map((type) => {
            const inApp = rows.find((r) => r.type === type && r.channel === "in_app");
            const email = rows.find((r) => r.type === type && r.channel === "email");
            return (
              <tr key={type} className="border-b border-border">
                <td className="py-2 text-fg">{TYPE_LABELS[type] ?? type}</td>
                <td className="py-2 text-center">
                  {inApp && (
                    <input
                      type="checkbox"
                      checked={inApp.enabled}
                      onChange={() => toggle(inApp)}
                      aria-label={`${TYPE_LABELS[type] ?? type} in-app`}
                    />
                  )}
                </td>
                <td className="py-2 text-center">
                  {email && (
                    <input
                      type="checkbox"
                      checked={email.enabled}
                      onChange={() => toggle(email)}
                      aria-label={`${TYPE_LABELS[type] ?? type} email`}
                    />
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
