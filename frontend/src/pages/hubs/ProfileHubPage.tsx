/**
 * Profile Hub: lists the profile.* tools as cards, and -- deep-linked as
 * `/profile/:toolId` -- renders the generic `<ToolRunner>` for one of
 * them. The only Profile-Hub-specific behaviour layered on top of the
 * framework is "Apply to profile" (see ApplyToProfileModal): everything
 * else about running a tool, showing its result, and saving it to the
 * Workspace is identical to any other hub's tools.
 */

import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import type { ToolSummary } from "@/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/lib/toast-context";
import { ToolRunner } from "@/tools/ToolRunner";
import { ApplyToProfileModal, type ApplyToProfileRequest } from "./ApplyToProfileModal";

function ToolCard({ tool }: { tool: ToolSummary }) {
  return (
    <Link to={`/profile/${tool.id}`}>
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
    apiFetch<ToolSummary[]>("/api/v1/tools?hub=profile")
      .then((result) => {
        if (!cancelled) setTools(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message : "Failed to load Profile Hub tools.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Profile Hub</h1>
        <p className="text-sm text-fg-muted">
          AI tools grounded in your real profile -- nothing here ever posts to or edits LinkedIn for
          you.
        </p>
      </div>

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
          description="Profile Hub tools will appear here once they're enabled for your account."
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
  const [searchParams] = useSearchParams();
  const [applyRequest, setApplyRequest] = useState<ApplyToProfileRequest | null>(null);
  const { push: pushToast } = useToast();

  const initialValues = useMemo(() => {
    const why = searchParams.get("why");
    return why ? { user_supplied_text: why } : undefined;
  }, [searchParams]);

  function handleApplied() {
    setApplyRequest(null);
    pushToast({ title: "Profile updated", variant: "success" });
  }

  return (
    <div className="flex flex-col gap-4">
      <Link to="/profile" className="text-sm text-fg-muted hover:text-fg">
        ← Back to Profile Hub
      </Link>
      <ToolRunner
        key={toolId}
        toolId={toolId}
        initialValues={initialValues}
        onApplyToProfile={setApplyRequest}
      />
      <ApplyToProfileModal
        request={applyRequest}
        onClose={() => setApplyRequest(null)}
        onApplied={handleApplied}
      />
    </div>
  );
}

export function ProfileHubPage() {
  const { toolId } = useParams<{ toolId: string }>();
  return toolId ? <ToolDetail toolId={toolId} /> : <ToolList />;
}
