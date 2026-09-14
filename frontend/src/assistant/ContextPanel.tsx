/**
 * The "what I can see" chip above the composer: opens a small panel
 * listing every context item the Assistant could use for this
 * conversation, with a per-item toggle. Toggling calls the same
 * endpoint the orchestrator reads from on every turn, so an excluded
 * item is genuinely left out of context assembly, not just hidden here.
 */

import { useEffect, useState } from "react";
import type { ContextItemResponse } from "@/contracts";
import { getContextSettings, updateContextSettings } from "./api";

export function ContextPanel({ conversationId }: { conversationId: string }) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<ContextItemResponse[] | null>(null);

  useEffect(() => {
    if (!open || items) return;
    getContextSettings(conversationId).then((response) => setItems(response.items));
  }, [open, items, conversationId]);

  async function toggle(key: string) {
    if (!items) return;
    const nextExcluded = items
      .map((item) => (item.key === key ? { ...item, excluded: !item.excluded } : item))
      .filter((item) => item.excluded)
      .map((item) => item.key);
    setItems(items.map((item) => (item.key === key ? { ...item, excluded: !item.excluded } : item)));
    const response = await updateContextSettings(conversationId, {
      excluded_context_keys: nextExcluded,
    });
    setItems(response.items);
  }

  const includedCount = items ? items.filter((item) => !item.excluded).length : null;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="rounded-full border border-border bg-bg-subtle px-3 py-1 text-xs text-fg-muted hover:text-fg"
      >
        👁 What I can see{includedCount !== null ? ` (${includedCount})` : ""}
      </button>
      {open && (
        <div className="absolute bottom-full left-0 z-10 mb-2 w-72 rounded-md border border-border bg-bg p-3 shadow-lg">
          <p className="mb-2 text-xs font-medium text-fg-muted">
            Context the Assistant can use for this conversation
          </p>
          {!items && <p className="text-xs text-fg-muted">Loading…</p>}
          <ul className="flex flex-col gap-2">
            {items?.map((item) => (
              <li key={item.key} className="flex items-center justify-between gap-2 text-sm">
                <span className={item.excluded ? "text-fg-muted line-through" : "text-fg"}>
                  {item.label}
                </span>
                <input
                  type="checkbox"
                  checked={!item.excluded}
                  onChange={() => toggle(item.key)}
                  aria-label={`Include ${item.label}`}
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
