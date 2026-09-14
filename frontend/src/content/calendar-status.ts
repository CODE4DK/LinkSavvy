import type { ContentPlanStatus } from "@/contracts";

/** Status is always shown as colour plus a distinct shape/glyph --
 * never colour alone, so it reads for colour-blind users and in
 * black-and-white printouts alike. */
export const STATUS_META: Record<
  ContentPlanStatus,
  {
    label: string;
    glyph: string;
    badgeVariant: "default" | "primary" | "success" | "warning" | "danger";
  }
> = {
  idea: { label: "Idea", glyph: "○", badgeVariant: "default" },
  drafted: { label: "Drafted", glyph: "◻", badgeVariant: "default" },
  ready: { label: "Ready", glyph: "△", badgeVariant: "primary" },
  scheduled: { label: "Scheduled", glyph: "◇", badgeVariant: "warning" },
  posted: { label: "Posted", glyph: "✓", badgeVariant: "success" },
  skipped: { label: "Skipped", glyph: "✕", badgeVariant: "danger" },
};

export const ALL_STATUSES: ContentPlanStatus[] = [
  "idea",
  "drafted",
  "ready",
  "scheduled",
  "posted",
  "skipped",
];
