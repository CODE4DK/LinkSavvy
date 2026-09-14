/**
 * The state a full-page `/assistant` view and the dockable side panel
 * (available from every hub) share: which conversation is open, whether
 * the panel is docked open, and a one-shot "first message" the dashboard
 * prompt bar hands off when it opens a brand new conversation.
 */

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

interface AssistantContextValue {
  panelOpen: boolean;
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  pendingFirstMessage: string | null;
  consumePendingFirstMessage: () => string | null;
  startConversationWithMessage: (text: string) => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [panelOpen, setPanelOpen] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [pendingFirstMessage, setPendingFirstMessage] = useState<string | null>(null);

  const openPanel = useCallback(() => setPanelOpen(true), []);
  const closePanel = useCallback(() => setPanelOpen(false), []);
  const togglePanel = useCallback(() => setPanelOpen((value) => !value), []);

  const consumePendingFirstMessage = useCallback(() => {
    let value: string | null = null;
    setPendingFirstMessage((current) => {
      value = current;
      return null;
    });
    return value;
  }, []);

  const startConversationWithMessage = useCallback((text: string) => {
    setActiveConversationId(null);
    setPendingFirstMessage(text);
  }, []);

  const value = useMemo(
    () => ({
      panelOpen,
      openPanel,
      closePanel,
      togglePanel,
      activeConversationId,
      setActiveConversationId,
      pendingFirstMessage,
      consumePendingFirstMessage,
      startConversationWithMessage,
    }),
    [
      panelOpen,
      openPanel,
      closePanel,
      togglePanel,
      activeConversationId,
      pendingFirstMessage,
      consumePendingFirstMessage,
      startConversationWithMessage,
    ],
  );

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant(): AssistantContextValue {
  const ctx = useContext(AssistantContext);
  if (!ctx) throw new Error("useAssistant must be used within an AssistantProvider");
  return ctx;
}
