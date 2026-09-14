import { useEffect, useState } from "react";
import type { AiInvocationResponse, AiOpsOverviewResponse } from "@linksavvy/contracts";
import { getAiOpsOverview, getPromptDrilldown } from "@/lib/admin-api";

export function AiOpsTab() {
  const [overview, setOverview] = useState<AiOpsOverviewResponse | null>(null);
  const [drilldown, setDrilldown] = useState<AiInvocationResponse[] | null>(null);
  const [drilldownPrompt, setDrilldownPrompt] = useState<string | null>(null);

  useEffect(() => {
    getAiOpsOverview().then(setOverview);
  }, []);

  if (!overview) return <p className="text-sm text-fg-muted">Loading…</p>;

  const totalCost = overview.cost_by_day.reduce((sum, day) => sum + day.cost_minor, 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-4">
        <Stat label="Total cost (30d)" value={`$${(totalCost / 100).toFixed(2)}`} />
        <Stat label="Invalid output rate" value={pct(overview.outcome_rates.invalid_output_rate)} />
        <Stat label="Fallback rate" value={pct(overview.outcome_rates.fallback_rate)} />
        <Stat label="Policy blocked rate" value={pct(overview.outcome_rates.policy_blocked_rate)} />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-fg">Cost by model</h3>
          <Table
            rows={overview.cost_by_model}
            render={(row) => [row.key, `$${(row.cost_minor / 100).toFixed(2)}`, row.invocation_count]}
          />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-fg">Cost by prompt</h3>
          <Table
            rows={overview.cost_by_prompt}
            render={(row) => [row.key, `$${(row.cost_minor / 100).toFixed(2)}`, row.invocation_count]}
            onRowClick={async (row) => {
              setDrilldownPrompt(row.key);
              setDrilldown(await getPromptDrilldown(row.key));
            }}
          />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-fg">
          Slowest prompts (avg latency; p95 is a 1.5x estimate, not an exact percentile)
        </h3>
        <Table
          rows={overview.slowest_prompts}
          render={(row) => [
            row.prompt_id,
            `${Math.round(row.avg_latency_ms)}ms avg`,
            `${Math.round(row.p95_latency_ms)}ms p95 (est.)`,
          ]}
        />
      </div>

      {drilldown && (
        <div>
          <h3 className="text-sm font-semibold text-fg">Drilldown: {drilldownPrompt}</h3>
          <table className="mt-2 w-full text-xs">
            <tbody>
              {drilldown.map((invocation) => (
                <tr key={invocation.id} className="border-t border-border">
                  <td className="py-1">{invocation.model}</td>
                  <td className="py-1">{invocation.outcome}</td>
                  <td className="py-1">{invocation.latency_ms}ms</td>
                  <td className="py-1">${(invocation.cost_minor / 100).toFixed(3)}</td>
                  <td className="py-1 text-fg-muted">
                    {new Date(invocation.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <p className="text-xs text-fg-muted">{label}</p>
      <p className="text-lg font-semibold text-fg">{value}</p>
    </div>
  );
}

function Table<T>({
  rows,
  render,
  onRowClick,
}: {
  rows: T[];
  render: (row: T) => (string | number)[];
  onRowClick?: (row: T) => void;
}) {
  return (
    <table className="mt-2 w-full text-xs">
      <tbody>
        {rows.map((row, index) => (
          <tr
            key={index}
            className={`border-t border-border ${onRowClick ? "cursor-pointer hover:bg-bg-subtle" : ""}`}
            onClick={() => onRowClick?.(row)}
          >
            {render(row).map((cell, i) => (
              <td key={i} className="py-1 text-fg">
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
