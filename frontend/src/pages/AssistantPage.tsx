/**
 * The full-page Assistant view: a conversation list on the left, the
 * shared ChatView on the right. Shares its active conversation with the
 * dockable side panel via AssistantContext -- switching between the two
 * surfaces never loses your place.
 */

import { useState } from "react";
import { useAssistant } from "@/lib/assistant-context";
import { ConversationList } from "@/assistant/ConversationList";
import { ChatView } from "@/assistant/ChatView";

export function AssistantPage() {
  const {
    activeConversationId,
    setActiveConversationId,
    pendingFirstMessage,
    consumePendingFirstMessage,
  } = useAssistant();
  const [refreshToken, setRefreshToken] = useState(0);

  function handleConversationCreated(id: string) {
    setActiveConversationId(id);
    setRefreshToken((value) => value + 1);
  }

  return (
    <div className="flex h-full gap-4">
      <ConversationList
        activeConversationId={activeConversationId}
        onSelect={setActiveConversationId}
        onCreateNew={() => setActiveConversationId(null)}
        refreshToken={refreshToken}
      />
      <div className="flex-1">
        <ChatView
          conversationId={activeConversationId}
          onConversationCreated={handleConversationCreated}
          initialMessage={pendingFirstMessage}
          onInitialMessageConsumed={consumePendingFirstMessage}
        />
      </div>
    </div>
  );
}
