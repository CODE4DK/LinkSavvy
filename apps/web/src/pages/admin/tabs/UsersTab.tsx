import { useState } from "react";
import type { AdminUserDetailResponse, AdminUserResponse } from "@linksavvy/contracts";
import {
  adjustPlan,
  forcePasswordReset,
  getUserDetail,
  reinstateUser,
  searchUsers,
  suspendUser,
} from "@/lib/admin-api";
import { useImpersonation } from "@/lib/impersonation-context";

export function UsersTab() {
  const [query, setQuery] = useState("");
  const [plan, setPlan] = useState("");
  const [status, setStatus] = useState("");
  const [results, setResults] = useState<AdminUserResponse[] | null>(null);
  const [detail, setDetail] = useState<AdminUserDetailResponse | null>(null);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const impersonation = useImpersonation();

  async function runSearch() {
    const page = await searchUsers({ q: query || undefined, plan: plan || undefined, status: status || undefined });
    setResults(page.items);
  }

  async function openDetail(userId: string) {
    setResetToken(null);
    setDetail(await getUserDetail(userId));
  }

  async function refreshDetail() {
    if (detail) setDetail(await getUserDetail(detail.user.id));
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div>
        <div className="flex flex-wrap gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by email or name"
            className="rounded-md border border-border bg-bg px-3 py-1.5 text-sm text-fg"
          />
          <select
            value={plan}
            onChange={(e) => setPlan(e.target.value)}
            className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-fg"
          >
            <option value="">Any plan</option>
            <option value="free">Free</option>
            <option value="pro">Pro</option>
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-fg"
          >
            <option value="">Any status</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
          </select>
          <button
            type="button"
            onClick={runSearch}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground"
          >
            Search
          </button>
        </div>

        <table className="mt-4 w-full text-sm">
          <tbody>
            {results?.map((user) => (
              <tr key={user.id} className="border-t border-border">
                <td className="py-2">
                  <button
                    type="button"
                    onClick={() => openDetail(user.id)}
                    className="text-left text-primary underline"
                  >
                    {user.email}
                  </button>
                </td>
                <td className="py-2 text-fg-muted">{user.plan}</td>
                <td className="py-2 text-fg-muted">{user.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {detail && (
        <div className="rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-fg">{detail.user.email}</h3>
          <p className="text-xs text-fg-muted">
            {detail.user.plan} · {detail.user.status} · joined{" "}
            {new Date(detail.user.created_at).toLocaleDateString()}
          </p>
          {detail.subscription && (
            <p className="mt-1 text-xs text-fg-muted">
              Subscription: {detail.subscription.provider} / {detail.subscription.status}
            </p>
          )}
          <p className="mt-1 text-xs text-fg-muted">
            AI spend this month: {(detail.ai_spend_minor_this_month / 100).toFixed(2)} (
            {detail.ai_run_count_this_month} runs)
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {detail.user.status === "active" ? (
              <button
                type="button"
                onClick={async () => {
                  const reason = window.prompt("Reason for suspending this user?");
                  if (!reason) return;
                  await suspendUser(detail.user.id, { reason });
                  await refreshDetail();
                  await runSearch();
                }}
                className="rounded-md px-2 py-1 text-xs font-medium text-danger"
              >
                Suspend
              </button>
            ) : (
              <button
                type="button"
                onClick={async () => {
                  await reinstateUser(detail.user.id);
                  await refreshDetail();
                  await runSearch();
                }}
                className="rounded-md px-2 py-1 text-xs font-medium text-primary"
              >
                Reinstate
              </button>
            )}
            <button
              type="button"
              onClick={async () => {
                const res = await forcePasswordReset(detail.user.id);
                setResetToken(res.reset_token);
              }}
              className="rounded-md border border-border px-2 py-1 text-xs font-medium text-fg"
            >
              Force password reset
            </button>
            <button
              type="button"
              onClick={async () => {
                const targetPlan = detail.user.plan === "pro" ? "free" : "pro";
                const reason = window.prompt(`Reason for moving this user to ${targetPlan}?`);
                if (!reason) return;
                await adjustPlan(detail.user.id, { plan: targetPlan, reason });
                await refreshDetail();
              }}
              className="rounded-md border border-border px-2 py-1 text-xs font-medium text-fg"
            >
              {detail.user.plan === "pro" ? "Move to free" : "Move to pro"}
            </button>
            <button
              type="button"
              onClick={() => impersonation.start(detail.user.id, detail.user.email)}
              className="rounded-md border border-border px-2 py-1 text-xs font-medium text-fg"
            >
              Impersonate
            </button>
          </div>

          {resetToken && (
            <p className="mt-2 rounded-md bg-bg-subtle p-2 text-xs text-fg-muted">
              Reset token (share out of band): <code>{resetToken}</code>
            </p>
          )}

          <h4 className="mt-4 text-xs font-semibold uppercase text-fg-muted">
            Recent tool runs
          </h4>
          <ul className="mt-1 space-y-1 text-xs text-fg-muted">
            {detail.recent_tool_runs.map((run) => (
              <li key={run.id}>
                {run.tool_id} — {run.status} — {new Date(run.created_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
