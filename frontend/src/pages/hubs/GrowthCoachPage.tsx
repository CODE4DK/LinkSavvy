/**
 * The AI Growth Coach: the shared Assistant chat surface (ChatView) in
 * `mode="coach"`, with the growth context pre-loaded server-side (see
 * app.growth.coach). Absorbed into the Phase 9 Assistant's conversation
 * store -- this route just points ChatView at the user's one ongoing
 * coach conversation rather than the general Assistant's conversation
 * list.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { ChatView } from "@/assistant/ChatView";

export function GrowthCoachPage() {
  // Deliberately local, not the shared AssistantContext state: the
  // coach conversation is a distinct thread from the general
  // Assistant's, so opening this page must never overwrite what the
  // side panel or /assistant currently has active.
  const [conversationId, setConversationId] = useState<string | null>(null);

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

      <div className="flex-1">
        <ChatView conversationId={conversationId} onConversationCreated={setConversationId} mode="coach" />
      </div>
    </div>
  );
}
