/**
 * The conversation list: search, rename, archive, delete. Used by the
 * full-page /assistant view's sidebar; the dockable side panel doesn't
 * render this (it stays scoped to one conversation at a time).
 */

import { useEffect, useState } from "react";
import type { ConversationSummary } from "@/contracts";
import { ApiError } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { Button } from "@/components/ui/Button";
import { archiveConversation, deleteConversation, listConversations, renameConversation } from "./api";

export interface ConversationListProps {
  activeConversationId: string | null;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
  refreshToken: number;
}

export function ConversationList({
  activeConversationId,
  onSelect,
  onCreateNew,
  refreshToken,
}: ConversationListProps) {
  const { push: pushToast } = useToast();
  const [query, setQuery] = useState("");
  const [conversations, setConversations] = useState<ConversationSummary[] | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");

  useEffect(() => {
    listConversations({ q: query || undefined }).then(setConversations);
  }, [query, refreshToken]);

  async function handleArchive(id: string) {
    try {
      await archiveConversation(id, { archived: true });
      setConversations((current) => current?.filter((c) => c.id !== id) ?? null);
    } catch (err) {
      pushToast({
        title: "Couldn't archive this conversation",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteConversation(id);
      setConversations((current) => current?.filter((c) => c.id !== id) ?? null);
      if (id === activeConversationId) onCreateNew();
    } catch (err) {
      pushToast({
        title: "Couldn't delete this conversation",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  }

  async function submitRename(id: string) {
    const title = renameDraft.trim();
    setRenamingId(null);
    if (!title) return;
    try {
      const updated = await renameConversation(id, { title });
      setConversations(
        (current) => current?.map((c) => (c.id === id ? updated : c)) ?? null,
      );
    } catch (err) {
      pushToast({
        title: "Couldn't rename this conversation",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  }

  return (
    <div className="flex h-full w-64 flex-col gap-2 border-r border-border p-3">
      <Button size="sm" onClick={onCreateNew}>
        New conversation
      </Button>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search conversations…"
        aria-label="Search conversations"
        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-fg"
      />
      <div className="flex-1 overflow-y-auto">
        {conversations === null && <p className="text-sm text-fg-muted">Loading…</p>}
        {conversations?.length === 0 && (
          <p className="text-sm text-fg-muted">No conversations yet.</p>
        )}
        <ul className="flex flex-col gap-1">
          {conversations?.map((conversation) => (
            <li key={conversation.id}>
              <div
                className={`group flex items-center justify-between gap-1 rounded-md px-2 py-1.5 text-sm ${
                  conversation.id === activeConversationId
                    ? "bg-bg-subtle text-fg"
                    : "text-fg-muted hover:bg-bg-subtle hover:text-fg"
                }`}
              >
                {renamingId === conversation.id ? (
                  <input
                    autoFocus
                    value={renameDraft}
                    onChange={(e) => setRenameDraft(e.target.value)}
                    onBlur={() => submitRename(conversation.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") submitRename(conversation.id);
                      if (e.key === "Escape") setRenamingId(null);
                    }}
                    className="flex-1 rounded border border-border bg-bg px-1 text-sm"
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => onSelect(conversation.id)}
                    className="flex-1 truncate text-left"
                  >
                    {conversation.title ?? "New conversation"}
                  </button>
                )}
                <div className="hidden gap-1 group-hover:flex">
                  <button
                    type="button"
                    aria-label="Rename conversation"
                    onClick={() => {
                      setRenamingId(conversation.id);
                      setRenameDraft(conversation.title ?? "");
                    }}
                  >
                    ✏️
                  </button>
                  <button
                    type="button"
                    aria-label="Archive conversation"
                    onClick={() => handleArchive(conversation.id)}
                  >
                    🗄
                  </button>
                  <button
                    type="button"
                    aria-label="Delete conversation"
                    onClick={() => handleDelete(conversation.id)}
                  >
                    🗑
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
