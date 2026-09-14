import { useEffect, useState } from "react";
import type { PlatformHealthResponse } from "@linksavvy/contracts";
import { getPlatformHealth, retryDeadJob } from "@/lib/admin-api";

export function PlatformHealthTab() {
  const [health, setHealth] = useState<PlatformHealthResponse | null>(null);

  async function refresh() {
    setHealth(await getPlatformHealth());
  }

  useEffect(() => {
    refresh();
  }, []);

  if (!health) return <p className="text-sm text-fg-muted">Loading…</p>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-4">
        <Stat label="Queued" value={health.queue_depth.queued} />
        <Stat label="Leased" value={health.queue_depth.leased} />
        <Stat label="Dead" value={health.queue_depth.dead} />
        <Stat label="Failed (last hour)" value={health.queue_depth.failed_last_hour} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-fg">Circuit breakers</h3>
        {Object.keys(health.circuit_breakers).length === 0 ? (
          <p className="mt-1 text-xs text-fg-muted">No provider has recorded a failure yet.</p>
        ) : (
          <ul className="mt-1 space-y-1 text-xs">
            {Object.entries(health.circuit_breakers).map(([provider, state]) => {
              const open = Boolean(state.open);
              const failures = Number(state.failures ?? 0);
              return (
                <li key={provider} className={open ? "text-danger" : "text-fg-muted"}>
                  {provider}: {open ? "open (tripped)" : "closed"} — {failures} recent failures
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div>
        <h3 className="text-sm font-semibold text-fg">Dead-lettered jobs</h3>
        {health.dead_jobs.length === 0 ? (
          <p className="mt-1 text-xs text-fg-muted">None.</p>
        ) : (
          <ul className="mt-2 space-y-2 text-xs">
            {health.dead_jobs.map((job) => (
              <li key={job.id} className="rounded-md border border-border p-2">
                <p className="text-fg">{job.type}</p>
                <p className="text-fg-muted">{job.error}</p>
                <button
                  type="button"
                  onClick={async () => {
                    await retryDeadJob(job.id);
                    await refresh();
                  }}
                  className="mt-1 rounded-md border border-border px-2 py-0.5 text-fg"
                >
                  Retry
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <p className="text-xs text-fg-muted">{label}</p>
      <p className="text-lg font-semibold text-fg">{value}</p>
    </div>
  );
}
