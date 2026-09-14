import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import type { SyncResponse } from "@/contracts";
import { profileSnapshotSchema } from "@/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Skeleton } from "@/components/ui/Skeleton";
import { loadWizardState, saveWizardState } from "./onboarding/wizard-state";

export function ProfileConnectCallbackPage() {
  const { status } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  const code = searchParams.get("code");
  const state = searchParams.get("state");

  useEffect(() => {
    if (status === "loading") return;

    if (status === "unauthenticated") {
      const next = window.location.pathname + window.location.search;
      navigate(`/login?next=${encodeURIComponent(next)}`, { replace: true });
      return;
    }

    if (!code || !state) {
      setError("LinkedIn didn't return the expected information.");
      return;
    }

    (async () => {
      try {
        await apiFetch(
          `/api/v1/profile/connect/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
        );
        const sync = await apiFetch<SyncResponse>("/api/v1/profile/sync", { method: "POST" });
        const wizard = loadWizardState();
        saveWizardState({
          ...wizard,
          source: "linkedin_api",
          draft: profileSnapshotSchema.parse(sync.draft),
          warnings: [],
          importId: null,
          step: 3,
        });
        navigate("/onboarding", { replace: true });
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not finish connecting LinkedIn.");
      }
    })();
  }, [status, code, state, navigate]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-bg-subtle px-4 text-center">
        <p className="text-sm text-danger">{error}</p>
        <Link to="/onboarding" className="text-sm text-primary hover:underline">
          Back to onboarding
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-subtle px-4">
      <div className="w-full max-w-sm space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
        <p className="text-center text-sm text-fg-muted">Finishing up with LinkedIn…</p>
      </div>
    </div>
  );
}
