/**
 * Engagement Hub: lists the engagement.* tools as cards, and -- deep-
 * linked as `/engagement/:toolId` -- renders the generic `<ToolRunner>`
 * for one of them, exactly like Content Hub. Below the tool list, a
 * "recent outreach" panel pulls together the most recent runs across
 * every tool flagged `counts_as_outreach` (never Engagement
 * Recommendations, which isn't outreach) so a user can see what they've
 * already sent someone before generating something new for them.
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { ToolRunSummary, ToolSummary } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ToolRunner } from "@/tools/ToolRunner";

function ToolCard({ tool }: { tool: ToolSummary }) {
  return (
    <Link to={`/engagement/${tool.id}`}>
      <Card className="h-full transition-colors hover:border-primary">
        <CardHeader>
          <CardTitle>{tool.name}</CardTitle>
          <CardDescription>{tool.short_description}</CardDescription>
        </CardHeader>
        <div className="flex flex-wrap gap-1.5">
          <Badge>{tool.result_renderer}</Badge>
          {tool.counts_as_outreach && <Badge variant="warning">review before sending</Badge>}
          {tool.min_plan !== "free" && <Badge variant="primary">{tool.min_plan}</Badge>}
        </div>
      </Card>
    </Link>
  );
}

/** The longest string field on a run's own input -- the same heuristic
 * `renderers.tsx`'s `primaryTextField` uses for a variant's primary
 * text -- is almost always the pasted post, profile, or prior context
 * a tool was run against, which is exactly what makes a "recent
 * outreach" row recognizable at a glance without any per-tool field
 * name special-casing. */
function primaryInputSnippet(input: Record<string, unknown>): string {
  let best = "";
  for (const value of Object.values(input)) {
    if (typeof value === "string" && value.length > best.length) best = value;
  }
  return best.length > 140 ? `${best.slice(0, 140)}…` : best;
}

interface RecentOutreachRow {
  toolId: string;
  toolName: string;
  snippet: string;
  createdAt: string;
}

function RecentOutreach({ tools }: { tools: ToolSummary[] }) {
  const [rows, setRows] = useState<RecentOutreachRow[] | null>(null);

  useEffect(() => {
    const outreachTools = tools.filter((tool) => tool.counts_as_outreach);
    if (outreachTools.length === 0) {
      setRows([]);
      return;
    }
    let cancelled = false;
    Promise.all(
      outreachTools.map((tool) =>
        apiFetch<ToolRunSummary[]>(`/api/v1/tools/${tool.id}/runs?limit=5`)
          .then((runs) => runs.map((run) => ({ tool, run })))
          .catch(() => []),
      ),
    ).then((groups) => {
      if (cancelled) return;
      const merged = groups
        .flat()
        .sort((a, b) => (a.run.created_at < b.run.created_at ? 1 : -1))
        .slice(0, 10)
        .map(({ tool, run }) => ({
          toolId: tool.id,
          toolName: tool.name,
          snippet: primaryInputSnippet(run.input),
          createdAt: run.created_at,
        }));
      setRows(merged);
    });
    return () => {
      cancelled = true;
    };
  }, [tools]);

  return (
    <div>
      <h2 className="mb-2 text-sm font-semibold text-fg">Recent outreach</h2>
      {rows === null && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      )}
      {rows?.length === 0 && (
        <p className="text-sm text-fg-muted">
          Nothing generated yet -- outreach you create will show up here so you can check what
          you've already sent someone.
        </p>
      )}
      {rows && rows.length > 0 && (
        <ul className="flex flex-col gap-2">
          {rows.map((row, index) => (
            <li key={index}>
              <Link
                to={`/engagement/${row.toolId}`}
                className="block rounded-md border border-border bg-bg p-3 transition-colors hover:border-primary"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-fg-muted">{row.toolName}</span>
                  <span className="text-xs text-fg-muted">
                    {new Date(row.createdAt).toLocaleString()}
                  </span>
                </div>
                {row.snippet && <p className="mt-1 text-sm text-fg">{row.snippet}</p>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ToolList() {
  const [tools, setTools] = useState<ToolSummary[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<ToolSummary[]>("/api/v1/tools?hub=engagement")
      .then((result) => {
        if (!cancelled) setTools(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message : "Failed to load Engagement Hub tools.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Engagement Hub</h1>
        <p className="text-sm text-fg-muted">
          Draft comments, replies, and messages worth sending -- LinkSavvy never posts, comments,
          connects, or messages on LinkedIn for you. Every message here is yours to review and
          personalise before you send it.
        </p>
      </div>

      {loadError && <p className="text-sm text-danger">{loadError}</p>}

      {!tools && !loadError && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 7 }, (_, index) => (
            <Skeleton key={index} className="h-32 w-full" />
          ))}
        </div>
      )}

      {tools && tools.length === 0 && (
        <EmptyState
          title="No tools available yet"
          description="Engagement Hub tools will appear here once they're enabled for your account."
        />
      )}

      {tools && tools.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {tools.map((tool) => (
              <ToolCard key={tool.id} tool={tool} />
            ))}
          </div>
          <RecentOutreach tools={tools} />
        </div>
      )}
    </div>
  );
}

function ToolDetail({ toolId }: { toolId: string }) {
  return (
    <div className="flex flex-col gap-4">
      <Link to="/engagement" className="text-sm text-fg-muted hover:text-fg">
        ← Back to Engagement Hub
      </Link>
      <ToolRunner key={toolId} toolId={toolId} />
    </div>
  );
}

export function EngagementHubPage() {
  const { toolId } = useParams<{ toolId: string }>();
  return toolId ? <ToolDetail toolId={toolId} /> : <ToolList />;
}
