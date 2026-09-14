/**
 * The Assistant's core chat surface -- shared by the full-page /assistant
 * view and the dockable side panel (see AssistantSidePanel.tsx) and, in
 * `mode="coach"`, by the Growth Coach page. One component, one state
 * machine: load or create a conversation, stream a reply with a visible
 * thinking state and a stop button, and expose copy/retry/edit-and-
 * branch/rate on every message.
 */

import { useEffect, useRef, useState } from "react";
import type {
  AssistantMessageResponse,
  AssistantStreamFrame,
  ConversationCreate,
} from "@/contracts";
import { ApiError } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { ToolProposalCard } from "./ToolProposalCard";
import { ContextPanel } from "./ContextPanel";
import {
  createConversation,
  editMessage,
  getConversation,
  getCoachConversation,
  rateMessage,
  retryMessage,
  saveConversation,
  streamMessage,
  suggestedPrompts,
} from "./api";

export interface ChatViewProps {
  conversationId: string | null;
  onConversationCreated: (id: string) => void;
  mode?: ConversationCreate["mode"] | "coach";
  toolId?: string;
  initialMessage?: string | null;
  onInitialMessageConsumed?: () => void;
  compact?: boolean;
}

interface StreamingState {
  text: string;
  thinking: boolean;
}

function ProposedTool(message: AssistantMessageResponse): {
  toolId: string;
  reasoning: string;
  prefilledInput: Record<string, unknown>;
} | null {
  const proposed = message.tool_call?.proposed_tool as
    | { tool_id: string; reasoning: string; prefilled_input: Record<string, unknown> }
    | null
    | undefined;
  if (!proposed) return null;
  return { toolId: proposed.tool_id, reasoning: proposed.reasoning, prefilledInput: proposed.prefilled_input };
}

function MessageBubble({
  conversationId,
  message,
  onEdit,
  onRetry,
  onRate,
}: {
  conversationId: string;
  message: AssistantMessageResponse;
  onEdit: (id: string, text: string) => void;
  onRetry: (id: string) => void;
  onRate: (id: string, rating: "up" | "down") => void;
}) {
  const { push: pushToast } = useToast();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(message.content);
  const isUser = message.role === "user";
  const isTool = message.role === "tool";
  const proposedTool = ProposedTool(message);
  const rating = message.tool_call?.rating as "up" | "down" | undefined;

  if (isTool) {
    return (
      <div className="flex justify-start">
        <p className="max-w-[80%] rounded-md border border-border bg-bg-subtle px-3 py-2 text-xs text-fg-muted">
          🔧 {message.content}
        </p>
      </div>
    );
  }

  if (editing) {
    return (
      <div className="flex justify-end">
        <div className="flex w-[80%] flex-col gap-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="rounded-md border border-border bg-bg p-2 text-sm text-fg"
            rows={3}
          />
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="secondary" onClick={() => setEditing(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setEditing(false);
                onEdit(message.id, draft);
              }}
            >
              Save & resend
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className="flex max-w-[80%] flex-col gap-1">
        <div
          className={`rounded-lg px-4 py-2 text-sm ${
            isUser ? "bg-primary text-primary-foreground" : "bg-bg-subtle text-fg"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        {proposedTool && (
          <ToolProposalCard
            conversationId={conversationId}
            proposingMessageId={message.id}
            toolId={proposedTool.toolId}
            reasoning={proposedTool.reasoning}
            prefilledInput={proposedTool.prefilledInput}
          />
        )}
        <div className="flex gap-2 text-xs text-fg-muted">
          <button
            type="button"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(message.content);
                pushToast({ title: "Copied", variant: "success" });
              } catch {
                pushToast({ title: "Couldn't copy", variant: "danger" });
              }
            }}
          >
            Copy
          </button>
          {isUser && <button onClick={() => setEditing(true)}>Edit</button>}
          {!isUser && <button onClick={() => onRetry(message.id)}>Retry</button>}
          {!isUser && (
            <>
              <button
                aria-label="Rate this reply up"
                onClick={() => onRate(message.id, "up")}
                className={rating === "up" ? "text-fg" : undefined}
              >
                👍
              </button>
              <button
                aria-label="Rate this reply down"
                onClick={() => onRate(message.id, "down")}
                className={rating === "down" ? "text-fg" : undefined}
              >
                👎
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChatView({
  conversationId,
  onConversationCreated,
  mode = "auto",
  toolId,
  initialMessage,
  onInitialMessageConsumed,
  compact = false,
}: ChatViewProps) {
  const { push: pushToast } = useToast();
  const [messages, setMessages] = useState<AssistantMessageResponse[] | null>(null);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState<StreamingState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [quotaWarning, setQuotaWarning] = useState<string | null>(null);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [savingConversation, setSavingConversation] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, streaming?.text]);

  useEffect(() => {
    if (conversationId) {
      getConversation(conversationId).then((detail) => setMessages(detail.messages));
    } else if (mode !== "coach" && !initialMessage) {
      setMessages([]);
    }
  }, [conversationId, mode, initialMessage]);

  useEffect(() => {
    if (messages !== null && messages.length === 0) {
      suggestedPrompts().then((response) => setPrompts(response.prompts));
    }
  }, [messages]);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    async function bootstrap() {
      if (conversationId) return;
      if (mode === "coach") {
        const conversation = await getCoachConversation();
        onConversationCreated(conversation.id);
        return;
      }
      if (initialMessage) {
        const payload: ConversationCreate =
          mode === "tool" && toolId ? { mode: "tool", tool_id: toolId } : { mode: "auto" };
        const conversation = await createConversation(payload);
        onConversationCreated(conversation.id);
        onInitialMessageConsumed?.();
        setMessages([]);
        await sendText(conversation.id, initialMessage);
      }
    }
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function sendText(targetConversationId: string, text: string) {
    setError(null);
    setStreaming({ text: "", thinking: true });
    setMessages((current) => [
      ...(current ?? []),
      {
        id: `optimistic-${Date.now()}`,
        role: "user",
        content: text,
        tool_call: null,
        tool_run_id: null,
        parent_message_id: null,
        created_at: new Date().toISOString(),
      },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamMessage(
        targetConversationId,
        { text },
        (frame: AssistantStreamFrame) => {
          if (frame.type === "delta") {
            setStreaming((current) => ({ text: (current?.text ?? "") + frame.text, thinking: false }));
          } else if (frame.type === "message") {
            setStreaming(null);
            setQuotaWarning(frame.quota_warning);
            getConversation(targetConversationId).then((detail) => setMessages(detail.messages));
          } else if (frame.type === "error") {
            setStreaming(null);
            setError(frame.message);
          }
        },
        { signal: controller.signal },
      );
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setStreaming(null);
        setError(err instanceof ApiError ? err.message : "The Assistant couldn't respond.");
      }
    } finally {
      abortRef.current = null;
    }
  }

  async function handleSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    setDraft("");

    if (!conversationId) {
      const payload: ConversationCreate =
        mode === "tool" && toolId ? { mode: "tool", tool_id: toolId } : { mode: "auto" };
      const conversation = await createConversation(payload);
      onConversationCreated(conversation.id);
      await sendText(conversation.id, trimmed);
      return;
    }
    await sendText(conversationId, trimmed);
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  async function handleEdit(messageId: string, text: string) {
    if (!conversationId) return;
    setError(null);
    setStreaming({ text: "", thinking: true });
    try {
      const response = await editMessage(conversationId, messageId, { text });
      setStreaming(null);
      setQuotaWarning(response.quota_warning ?? null);
      const detail = await getConversation(conversationId);
      setMessages(detail.messages);
    } catch (err) {
      setStreaming(null);
      pushToast({
        title: "Couldn't save the edit",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  }

  async function handleRetry(messageId: string) {
    if (!conversationId || !messages) return;
    const target = messages.find((m) => m.id === messageId);
    const userMessageId = target?.parent_message_id;
    if (!userMessageId) return;
    setError(null);
    setStreaming({ text: "", thinking: true });
    try {
      const response = await retryMessage(conversationId, userMessageId);
      setStreaming(null);
      setQuotaWarning(response.quota_warning ?? null);
      const detail = await getConversation(conversationId);
      setMessages(detail.messages);
    } catch (err) {
      setStreaming(null);
      pushToast({
        title: "Couldn't retry",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  }

  async function handleRate(messageId: string, rating: "up" | "down") {
    if (!conversationId) return;
    try {
      const updated = await rateMessage(conversationId, messageId, { rating });
      setMessages((current) => current?.map((m) => (m.id === messageId ? updated : m)) ?? null);
    } catch {
      pushToast({ title: "Couldn't save your rating", variant: "danger" });
    }
  }

  async function handleSaveConversation() {
    if (!conversationId) return;
    setSavingConversation(true);
    try {
      await saveConversation(conversationId, {});
      pushToast({ title: "Saved to Workspace", variant: "success" });
    } catch (err) {
      pushToast({
        title: "Couldn't save this conversation",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    } finally {
      setSavingConversation(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex-1 overflow-y-auto rounded-md border border-border bg-bg p-4">
        {messages === null && <Skeleton className="h-24 w-full" />}

        {messages?.length === 0 && !streaming && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <p className="text-sm text-fg-muted">
              {mode === "coach"
                ? "Say hello to get started."
                : "Ask me anything about your LinkedIn profile, content, or growth."}
            </p>
            {prompts.length > 0 && (
              <div className="flex flex-wrap justify-center gap-2">
                {prompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => handleSend(prompt)}
                    className="rounded-full border border-border bg-bg-subtle px-3 py-1.5 text-sm text-fg hover:bg-bg"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex flex-col gap-4">
          {messages?.map((message) => (
            <MessageBubble
              key={message.id}
              conversationId={conversationId ?? ""}
              message={message}
              onEdit={handleEdit}
              onRetry={handleRetry}
              onRate={handleRate}
            />
          ))}
          {streaming && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-bg-subtle px-4 py-2 text-sm text-fg">
                {streaming.thinking ? (
                  <span className="text-fg-muted">Thinking…</span>
                ) : (
                  <p className="whitespace-pre-wrap">{streaming.text}</p>
                )}
              </div>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {quotaWarning && <p className="text-sm text-warning">{quotaWarning}</p>}

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {conversationId && mode !== "coach" && <ContextPanel conversationId={conversationId} />}
        </div>
        {conversationId && !compact && (
          <Button size="sm" variant="secondary" onClick={handleSaveConversation} loading={savingConversation}>
            Save conversation
          </Button>
        )}
      </div>

      <div className="flex gap-2">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !streaming) {
              e.preventDefault();
              handleSend(draft);
            }
          }}
          placeholder={mode === "coach" ? "Message the Growth Coach..." : "Ask the Assistant..."}
          rows={compact ? 2 : 3}
          className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-fg"
        />
        {streaming ? (
          <Button variant="secondary" onClick={handleStop}>
            Stop
          </Button>
        ) : (
          <Button onClick={() => handleSend(draft)} disabled={!draft.trim()}>
            Send
          </Button>
        )}
      </div>
    </div>
  );
}
