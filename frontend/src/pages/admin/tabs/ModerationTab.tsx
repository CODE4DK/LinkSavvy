import { useEffect, useState } from "react";
import type { ModerationFlagResponse } from "@/contracts";
import { listModerationFlags, reviewModerationFlag } from "@/lib/admin-api";

export function ModerationTab() {
  const [flags, setFlags] = useState<ModerationFlagResponse[]>([]);

  async function refresh() {
    setFlags(await listModerationFlags("pending"));
  }

  useEffect(() => {
    refresh();
  }, []);

  async function review(flag: ModerationFlagResponse, status: "approved" | "removed") {
    const note = window.prompt("Optional note for this decision") || undefined;
    await reviewModerationFlag(flag.id, { status, note });
    await refresh();
  }

  if (flags.length === 0) {
    return <p className="text-sm text-fg-muted">Nothing in the moderation queue.</p>;
  }

  return (
    <ul className="space-y-3">
      {flags.map((flag) => (
        <li key={flag.id} className="rounded-lg border border-border p-4">
          <p className="text-xs uppercase text-fg-muted">
            {flag.source === "ai_policy" ? "Caught by output policy" : "Reported by a user"} ·{" "}
            {flag.target_type}
          </p>
          <p className="mt-1 text-sm text-fg">{flag.reason}</p>
          <p className="mt-1 rounded-md bg-bg-subtle p-2 text-xs text-fg-muted">{flag.excerpt}</p>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              onClick={() => review(flag, "approved")}
              className="rounded-md border border-border px-2 py-1 text-xs text-fg"
            >
              Approve (no action)
            </button>
            <button
              type="button"
              onClick={() => review(flag, "removed")}
              className="rounded-md bg-danger px-2 py-1 text-xs text-danger-foreground"
            >
              Remove
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
