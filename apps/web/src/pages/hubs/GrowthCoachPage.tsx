/**
 * The AI Growth Coach: a simple chat surface at /growth/coach. Built
 * directly against the gateway-backed conversation in
 * app.growth.coach, not the Phase 9 assistant (kept separate per the
 * Phase 8 spec). Each assistant message carries a `phase` and, when the
 * coach proposes running a specific tool, a `proposed_tool_id` rendered
 * as an actionable card.
 */

import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { CoachMessageResponse, CoachSessionResponse } from "@linksavvy/contracts";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

function MessageBubble({ message }: { message: CoachMessageResponse }) {
  const isUser = message.role === "user";
  const proposedToolId = message.metadata.proposed_tool_id as string | null | undefined;
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
          isUser ? "bg-primary text-primary-foreground" : "bg-bg-subtle text-fg"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {proposedToolId && (
          <Link to={`/${proposedToolId.split(".")[0]}/${proposedToolId}`} className="mt-2 block">
            <Button size="sm" variant="secondary">
              Run {proposedToolId}
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}

export function GrowthCoachPage() {
  const [session, setSession] = useState<CoachSessionResponse | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiFetch<CoachSessionResponse>("/api/v1/growth/coach/session").then(setSession);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages.length]);

  const send = () => {
    const text = draft.trim();
    if (!text || !session) return;
    setSending(true);
    setError(null);
    setSession({
      ...session,
      messages: [
        ...session.messages,
        {
          id: `optimistic-${Date.now()}`,
          role: "user",
          content: text,
          metadata: {},
          created_at: new Date().toISOString(),
        },
      ],
    });
    setDraft("");
    apiFetch<CoachMessageResponse>("/api/v1/growth/coach/messages", {
      method: "POST",
      body: { text },
    })
      .then((reply) => {
        setSession((current) =>
          current ? { ...current, messages: [...current.messages, reply] } : current,
        );
      })
      .catch(() => setError("The coach couldn't respond -- try again."))
      .finally(() => setSending(false));
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <Link to="/growth" className="text-sm text-fg-muted hover:text-fg">
          ← Back to Growth Hub
        </Link>
        <h1 className="mt-1 text-xl font-semibold text-fg">Growth Coach</h1>
        <p className="text-sm text-fg-muted">
          A conversation grounded in your real scores and history -- never generic encouragement.
        </p>
      </div>

      <Card className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
        {!session && <Skeleton className="h-24 w-full" />}
        {session?.messages.length === 0 && (
          <p className="text-sm text-fg-muted">Say hello to get started.</p>
        )}
        {session?.messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </Card>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-2">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !sending) send();
          }}
          placeholder="Message the Growth Coach..."
          className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-fg"
        />
        <Button onClick={send} loading={sending} disabled={!draft.trim()}>
          Send
        </Button>
      </div>
    </div>
  );
}
