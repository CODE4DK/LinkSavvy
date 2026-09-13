/**
 * The Profile Hub's "Apply to profile" flow: takes a piece of text a
 * tool produced (a chosen headline variant, a generated About section,
 * a rewritten experience description) and commits it into a new
 * ProfileSnapshot version as a plain manual edit -- the same `PUT
 * /api/v1/profile/snapshot` path the onboarding wizard's manual review
 * step uses. This is deliberately Profile-Hub-specific, not part of the
 * generic Tool Framework: only this page knows what "accept this text"
 * should mean for a LinkSavvy profile field.
 */

import { useEffect, useState } from "react";
import type { ProfileSnapshot, SnapshotDetail, SnapshotSummary } from "@linksavvy/contracts";
import { profileSnapshotSchema } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";

export interface ApplyToProfileRequest {
  assetType: string;
  text: string;
}

export interface ApplyToProfileModalProps {
  request: ApplyToProfileRequest | null;
  onClose: () => void;
  onApplied: () => void;
}

interface FieldPatch {
  label: string;
  before: string;
  apply: (snapshot: ProfileSnapshot) => ProfileSnapshot;
}

const PROVENANCE = { source: "manual" as const, confidence: 1 };

function patchFor(assetType: string, text: string, snapshot: ProfileSnapshot): FieldPatch | null {
  switch (assetType) {
    case "headline":
      return {
        label: "Headline",
        before: snapshot.identity?.headline ?? "",
        apply: (current) => ({
          ...current,
          identity: { ...current.identity, headline: text },
          field_provenance: { ...current.field_provenance, "/identity/headline": PROVENANCE },
        }),
      };
    case "about":
      return {
        label: "About section",
        before: snapshot.about ?? "",
        apply: (current) => ({
          ...current,
          about: text,
          field_provenance: { ...current.field_provenance, "/about": PROVENANCE },
        }),
      };
    case "experience_bullets": {
      const experiences = snapshot.experiences ?? [];
      const index = experiences.findIndex((experience) => experience.is_current);
      const targetIndex = index === -1 ? 0 : index;
      const target = experiences[targetIndex];
      if (!target) return null;
      return {
        label: `Experience: ${[target.title, target.company].filter(Boolean).join(" at ") || "current role"}`,
        before: target.description ?? "",
        apply: (current) => {
          const next = [...(current.experiences ?? [])];
          const existing = next[targetIndex];
          if (existing) next[targetIndex] = { ...existing, description: text };
          return {
            ...current,
            experiences: next,
            field_provenance: {
              ...current.field_provenance,
              [`/experiences/${targetIndex}/description`]: PROVENANCE,
            },
          };
        },
      };
    }
    default:
      return null;
  }
}

export function ApplyToProfileModal({ request, onClose, onApplied }: ApplyToProfileModalProps) {
  const [snapshot, setSnapshot] = useState<ProfileSnapshot | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (!request) return;
    setSnapshot(null);
    setLoadError(null);
    setSaveError(null);
    apiFetch<SnapshotDetail>("/api/v1/profile/snapshot")
      .then((detail) => setSnapshot(profileSnapshotSchema.parse(detail.payload)))
      .catch((err) =>
        setLoadError(
          err instanceof ApiError && err.status === 404
            ? "You don't have a profile yet -- complete onboarding first."
            : "Couldn't load your current profile.",
        ),
      );
  }, [request]);

  if (!request) return null;

  const patch = snapshot ? patchFor(request.assetType, request.text, snapshot) : null;

  async function handleConfirm() {
    if (!snapshot || !patch) return;
    setSaving(true);
    setSaveError(null);
    try {
      await apiFetch<SnapshotSummary>("/api/v1/profile/snapshot", {
        method: "PUT",
        body: patch.apply(snapshot),
      });
      onApplied();
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Couldn't update your profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Apply to profile">
      {loadError && <p className="text-sm text-danger">{loadError}</p>}
      {!snapshot && !loadError && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-16 w-full" />
        </div>
      )}
      {snapshot && !patch && (
        <p className="text-sm text-danger">
          Couldn't find a profile section to update for this result.
        </p>
      )}
      {snapshot && patch && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-fg-muted">
            This updates <span className="font-medium text-fg">{patch.label}</span> on your
            LinkSavvy profile. LinkSavvy never writes to LinkedIn itself -- you'll still need to
            copy this into LinkedIn yourself.
          </p>
          <div>
            <p className="mb-1 text-xs font-medium uppercase text-fg-muted">Current</p>
            <p className="whitespace-pre-wrap rounded-md bg-bg-subtle p-3 text-sm text-fg-muted">
              {patch.before || "(empty)"}
            </p>
          </div>
          <div>
            <p className="mb-1 text-xs font-medium uppercase text-fg-muted">New</p>
            <p className="whitespace-pre-wrap rounded-md border border-primary/40 bg-primary/5 p-3 text-sm text-fg">
              {request.text}
            </p>
          </div>
          {saveError && <p className="text-sm text-danger">{saveError}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleConfirm} loading={saving}>
              Apply to profile
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
