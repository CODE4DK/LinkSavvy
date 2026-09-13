/**
 * Content Hub: lists the content.* tools as cards, and -- deep-linked as
 * `/content/:toolId` -- renders the generic `<ToolRunner>` for one of
 * them, exactly like Profile Hub. No Profile-Hub-specific "apply back"
 * behaviour here: a content tool's result is meant for the Composer,
 * the calendar, or Save to Workspace (all generic `<ToolRunner>`
 * actions), not for patching a `ProfileSnapshot`.
 */

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { ToolSummary } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ToolRunner } from "@/tools/ToolRunner";

function ToolCard({ tool }: { tool: ToolSummary }) {
  return (
    <Link to={`/content/${tool.id}`}>
      <Card className="h-full transition-colors hover:border-primary">
        <CardHeader>
          <CardTitle>{tool.name}</CardTitle>
          <CardDescription>{tool.short_description}</CardDescription>
        </CardHeader>
        <div className="flex flex-wrap gap-1.5">
          <Badge>{tool.result_renderer}</Badge>
          {tool.min_plan !== "free" && <Badge variant="primary">{tool.min_plan}</Badge>}
        </div>
      </Card>
    </Link>
  );
}

function ToolList() {
  const [tools, setTools] = useState<ToolSummary[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<ToolSummary[]>("/api/v1/tools?hub=content")
      .then((result) => {
        if (!cancelled) setTools(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message : "Failed to load Content Hub tools.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Content Hub</h1>
        <p className="text-sm text-fg-muted">
          Draft, refine, and plan LinkedIn posts with AI assistance -- LinkSavvy never posts to
          LinkedIn for you.
        </p>
      </div>

      <Link to="/content/voice">
        <Card className="transition-colors hover:border-primary">
          <CardHeader>
            <CardTitle>Voice profile</CardTitle>
            <CardDescription>
              Teach every tool below how you actually write, from your own past posts.
            </CardDescription>
          </CardHeader>
        </Card>
      </Link>

      {loadError && <p className="text-sm text-danger">{loadError}</p>}

      {!tools && !loadError && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-32 w-full" />
          ))}
        </div>
      )}

      {tools && tools.length === 0 && (
        <EmptyState
          title="No tools available yet"
          description="Content Hub tools will appear here once they're enabled for your account."
        />
      )}

      {tools && tools.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tools.map((tool) => (
            <ToolCard key={tool.id} tool={tool} />
          ))}
        </div>
      )}
    </div>
  );
}

function ToolDetail({ toolId }: { toolId: string }) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-4">
      <Link to="/content" className="text-sm text-fg-muted hover:text-fg">
        ← Back to Content Hub
      </Link>
      <ToolRunner
        key={toolId}
        toolId={toolId}
        onSendToComposer={(text) => navigate("/content/composer", { state: { prefill: text } })}
      />
    </div>
  );
}

export function ContentHubPage() {
  const { toolId } = useParams<{ toolId: string }>();
  return toolId ? <ToolDetail toolId={toolId} /> : <ToolList />;
}
