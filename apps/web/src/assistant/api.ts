/**
 * Typed wrappers over the Assistant's REST + SSE surface
 * (/api/v1/assistant/...). Nothing here holds state -- see
 * AssistantContext.tsx for the shared conversation state the full page
 * and the dockable side panel both read from.
 */

import type {
  ArchiveConversationRequest,
  AssistantStreamFrame,
  ConfirmToolRunRequest,
  ConversationCreate,
  ConversationDetailResponse,
  ConversationSummary,
  ContextSettingsResponse,
  ContextTogglesRequest,
  EditMessageRequest,
  AssistantMessageResponse,
  RateMessageRequest,
  RenameConversationRequest,
  SaveConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
  SuggestedPromptsResponse,
} from "@linksavvy/contracts";
import { apiFetch, streamSSE } from "@/lib/api";

const BASE = "/api/v1/assistant";

export function listConversations(params: {
  q?: string;
  includeArchived?: boolean;
}): Promise<ConversationSummary[]> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.includeArchived) query.set("include_archived", "true");
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ConversationSummary[]>(`${BASE}/conversations${suffix}`);
}

export function createConversation(payload: ConversationCreate): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`${BASE}/conversations`, { method: "POST", body: payload });
}

export function getConversation(id: string): Promise<ConversationDetailResponse> {
  return apiFetch<ConversationDetailResponse>(`${BASE}/conversations/${id}`);
}

export function renameConversation(
  id: string,
  payload: RenameConversationRequest,
): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`${BASE}/conversations/${id}/rename`, {
    method: "POST",
    body: payload,
  });
}

export function archiveConversation(
  id: string,
  payload: ArchiveConversationRequest,
): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`${BASE}/conversations/${id}/archive`, {
    method: "POST",
    body: payload,
  });
}

export function deleteConversation(id: string): Promise<void> {
  return apiFetch<void>(`${BASE}/conversations/${id}`, { method: "DELETE" });
}

export function saveConversation(
  id: string,
  payload: SaveConversationRequest,
): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`${BASE}/conversations/${id}/save`, {
    method: "POST",
    body: payload,
  });
}

export function getContextSettings(conversationId: string): Promise<ContextSettingsResponse> {
  return apiFetch<ContextSettingsResponse>(`${BASE}/conversations/${conversationId}/context`);
}

export function updateContextSettings(
  conversationId: string,
  payload: ContextTogglesRequest,
): Promise<ContextSettingsResponse> {
  return apiFetch<ContextSettingsResponse>(`${BASE}/conversations/${conversationId}/context`, {
    method: "PATCH",
    body: payload,
  });
}

export function sendMessage(
  conversationId: string,
  payload: SendMessageRequest,
): Promise<SendMessageResponse> {
  return apiFetch<SendMessageResponse>(`${BASE}/conversations/${conversationId}/messages`, {
    method: "POST",
    body: payload,
  });
}

export function streamMessage(
  conversationId: string,
  payload: SendMessageRequest,
  onFrame: (frame: AssistantStreamFrame) => void,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  return streamSSE<AssistantStreamFrame>(
    `${BASE}/conversations/${conversationId}/messages?stream=true`,
    payload,
    onFrame,
    options,
  );
}

export function retryMessage(
  conversationId: string,
  messageId: string,
): Promise<SendMessageResponse> {
  return apiFetch<SendMessageResponse>(
    `${BASE}/conversations/${conversationId}/messages/${messageId}/retry`,
    { method: "POST" },
  );
}

export function editMessage(
  conversationId: string,
  messageId: string,
  payload: EditMessageRequest,
): Promise<SendMessageResponse> {
  return apiFetch<SendMessageResponse>(
    `${BASE}/conversations/${conversationId}/messages/${messageId}/edit`,
    { method: "POST", body: payload },
  );
}

export function rateMessage(
  conversationId: string,
  messageId: string,
  payload: RateMessageRequest,
): Promise<AssistantMessageResponse> {
  return apiFetch<AssistantMessageResponse>(
    `${BASE}/conversations/${conversationId}/messages/${messageId}/rate`,
    { method: "POST", body: payload },
  );
}

export function confirmTool(
  conversationId: string,
  payload: ConfirmToolRunRequest,
): Promise<AssistantMessageResponse> {
  return apiFetch<AssistantMessageResponse>(`${BASE}/conversations/${conversationId}/confirm-tool`, {
    method: "POST",
    body: payload,
  });
}

export function suggestedPrompts(): Promise<SuggestedPromptsResponse> {
  return apiFetch<SuggestedPromptsResponse>(`${BASE}/suggested-prompts`);
}

export function getCoachConversation(): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>("/api/v1/growth/coach/conversation");
}
