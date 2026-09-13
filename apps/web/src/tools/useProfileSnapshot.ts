import { useEffect, useState } from "react";
import type { ProfileSnapshot, SnapshotDetail } from "@linksavvy/contracts";
import { profileSnapshotSchema } from "@linksavvy/contracts";
import { apiFetch } from "@/lib/api";

/** Lazily loads the user's active profile snapshot -- only fetched when a
 * tool's input schema actually needs it (a field with `x-default-source`
 * or a `profile_section` picker), so a tool with no profile-backed
 * fields never pays for the request. Resolves to `null`, not an error,
 * when the user has no snapshot yet -- callers just fall back to a blank
 * field in that case. */
export function useProfileSnapshot(enabled: boolean): {
  snapshot: ProfileSnapshot | null;
  loading: boolean;
} {
  const [snapshot, setSnapshot] = useState<ProfileSnapshot | null>(null);
  const [loading, setLoading] = useState(enabled);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    setLoading(true);
    apiFetch<SnapshotDetail>("/api/v1/profile/snapshot")
      .then((detail) => {
        if (!cancelled) setSnapshot(profileSnapshotSchema.parse(detail.payload));
      })
      .catch(() => {
        // No snapshot yet, or the request failed -- either way there's
        // nothing to prefill from, so fields fall back to blank.
        if (!cancelled) setSnapshot(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return { snapshot, loading };
}
