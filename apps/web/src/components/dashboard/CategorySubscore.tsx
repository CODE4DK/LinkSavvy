import { useState } from "react";
import type { AuditCategoryResultResponse } from "@linksavvy/contracts";
import { Badge } from "@/components/ui/Badge";

const CATEGORY_LABELS: Record<string, string> = {
  profile: "Profile",
  content: "Content",
  engagement: "Engagement",
  career: "Career",
  visibility: "Visibility",
};

const STATUS_BADGE_VARIANT: Record<string, "success" | "warning" | "default" | "danger"> = {
  ok: "success",
  partial: "warning",
  skipped: "default",
  failed: "danger",
};

const SEVERITY_BADGE_VARIANT: Record<string, "danger" | "warning" | "default"> = {
  critical: "danger",
  important: "warning",
  opportunity: "default",
};

function unlockMessage(result: AuditCategoryResultResponse): string | null {
  const unlock = result.inputs_available["unlock"];
  return typeof unlock === "string" ? unlock : null;
}

export interface CategorySubscoreProps {
  result: AuditCategoryResultResponse;
}

/** One category's row in the Health Score card: score/status at a
 * glance, expandable into a "drawer" of its top findings. A skipped
 * category gets its own distinct empty state (why, and how to unlock
 * it) rather than looking like a plain zero. */
export function CategorySubscore({ result }: CategorySubscoreProps) {
  const [expanded, setExpanded] = useState(false);
  const label = CATEGORY_LABELS[result.category] ?? result.category;
  const unlock = unlockMessage(result);

  return (
    <div className="border-b border-border py-3 last:border-b-0">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between gap-3 text-left"
        aria-expanded={expanded}
      >
        <span className="text-sm font-medium text-fg">{label}</span>
        <span className="flex items-center gap-2">
          <span className="text-sm text-fg-muted">
            {result.score !== null ? result.score : "—"}
          </span>
          <Badge variant={STATUS_BADGE_VARIANT[result.status] ?? "default"}>{result.status}</Badge>
        </span>
      </button>

      {expanded && (
        <div className="mt-3 flex flex-col gap-2 pl-1">
          {result.status === "skipped" && (
            <p className="text-sm text-fg-muted">
              {unlock ?? "Not enough data yet to score this category."}
            </p>
          )}
          {result.findings.length === 0 && result.status !== "skipped" && (
            <p className="text-sm text-fg-muted">Nothing to flag here right now.</p>
          )}
          {result.findings.map((finding) => (
            <div key={finding.id} className="flex items-start justify-between gap-3">
              <span className="text-sm text-fg">{finding.title}</span>
              <Badge variant={SEVERITY_BADGE_VARIANT[finding.severity] ?? "default"}>
                {finding.severity}
              </Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
