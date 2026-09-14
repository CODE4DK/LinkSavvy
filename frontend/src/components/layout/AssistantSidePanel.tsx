/**
 * The dockable Assistant panel, available from every hub. Shares state
 * with the full-page /assistant view via AssistantContext -- opening the
 * panel and later visiting /assistant (or vice versa) shows the same
 * conversation, not two independent ones.
 */

import { Link } from "react-router-dom";
import { useAssistant } from "@/lib/assistant-context";
import { ChatView } from "@/assistant/ChatView";
import { Button } from "@/components/ui/Button";

export function AssistantSidePanel() {
  const {
    panelOpen,
    closePanel,
    activeConversationId,
    setActiveConversationId,
    pendingFirstMessage,
    consumePendingFirstMessage,
  } = useAssistant();

  if (!panelOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 flex w-full max-w-sm flex-col gap-3 border-l border-border bg-bg p-4 shadow-xl sm:w-96">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-fg">AI Assistant</h2>
        <div className="flex items-center gap-2">
          <Link to="/assistant" className="text-xs text-fg-muted hover:text-fg" onClick={closePanel}>
            Open full page
          </Link>
          <Button size="sm" variant="ghost" onClick={closePanel} aria-label="Close assistant panel">
            ✕
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        <ChatView
          conversationId={activeConversationId}
          onConversationCreated={setActiveConversationId}
          initialMessage={pendingFirstMessage}
          onInitialMessageConsumed={consumePendingFirstMessage}
          compact
        />
      </div>
    </div>
  );
}
