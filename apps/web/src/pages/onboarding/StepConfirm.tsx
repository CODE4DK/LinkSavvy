import { useState } from "react";
import type { ProfileSnapshot, SnapshotSummary } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

export interface StepConfirmProps {
  draft: ProfileSnapshot;
  importId: string | null;
  onBack: () => void;
  onCommitted: (summary: SnapshotSummary) => void;
}

function commitEndpointFor(draft: ProfileSnapshot, importId: string | null): string {
  if (draft.source === "manual") return "/api/v1/profile/snapshot";
  if (draft.source === "linkedin_api") return "/api/v1/profile/sync/commit";
  if (importId) return `/api/v1/profile/imports/${importId}/commit`;
  return "/api/v1/profile/snapshot";
}

export function StepConfirm({ draft, importId, onBack, onCommitted }: StepConfirmProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const experienceCount = draft.experiences?.length ?? 0;
  const educationCount = draft.education?.length ?? 0;
  const skillCount = draft.skills?.length ?? 0;

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = commitEndpointFor(draft, importId);
      const summary =
        draft.source === "manual"
          ? await apiFetch<SnapshotSummary>(endpoint, { method: "PUT", body: draft })
          : await apiFetch<SnapshotSummary>(endpoint, {
              method: "POST",
              body: { payload: draft },
            });
      onCommitted(summary);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your profile.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <button type="button" onClick={onBack} className="mb-4 text-sm text-fg-muted hover:text-fg">
        ← Back
      </button>

      <h1 className="text-2xl font-semibold text-fg">Ready to save?</h1>
      <p className="mt-1 text-sm text-fg-muted">
        This becomes version 1 of your profile. You can always import again later — nothing is
        overwritten without a new version.
      </p>

      {error && (
        <p role="alert" className="mt-4 rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{draft.identity?.full_name || "Your profile"}</CardTitle>
          <CardDescription>{draft.identity?.headline}</CardDescription>
        </CardHeader>
        <ul className="text-sm text-fg-muted">
          <li>{experienceCount} experience entries</li>
          <li>{educationCount} education entries</li>
          <li>{skillCount} skills</li>
        </ul>
      </Card>

      <div className="mt-8 flex justify-end">
        <Button onClick={handleConfirm} loading={loading}>
          Confirm and finish
        </Button>
      </div>
    </div>
  );
}
