import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type {
  AssistantMessageResponse,
  AssistantStreamFrame,
  ConversationDetailResponse,
} from "@linksavvy/contracts";
import { ChatView } from "./ChatView";

vi.mock("@/lib/api", () => {
  class ApiError extends Error {
    status: number;
    code: string;
    details: Record<string, unknown>;
    constructor(
      status: number,
      envelope: { code: string; message: string; details: Record<string, unknown> },
    ) {
      super(envelope.message);
      this.status = status;
      this.code = envelope.code;
      this.details = envelope.details;
    }
  }
  return { apiFetch: vi.fn(), streamSSE: vi.fn(), ApiError };
});

const pushToast = vi.fn();
vi.mock("@/lib/toast-context", () => ({
  useToast: () => ({ toasts: [], push: pushToast, dismiss: vi.fn() }),
}));

import { apiFetch, streamSSE } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);
const mockedStreamSSE = vi.mocked(streamSSE);

function detailWith(messages: AssistantMessageResponse[]): ConversationDetailResponse {
  return {
    conversation: {
      id: "conv-1",
      title: null,
      mode: "auto",
      message_count: messages.length,
      last_message_at: null,
      is_archived: false,
      asset_id: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
    messages,
  };
}

function typeInto(element: HTMLElement, value: string) {
  fireEvent.change(element, { target: { value } });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockedStreamSSE.mockReset();
  pushToast.mockReset();
  mockedApiFetch.mockImplementation(async (path: string) => {
    if (path.includes("suggested-prompts")) return { prompts: [] };
    return detailWith([]);
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ChatView", () => {
  it("shows suggested prompts for an empty conversation", async () => {
    mockedApiFetch.mockImplementation(async (path: string) => {
      if (path.includes("suggested-prompts")) {
        return { prompts: ["Fix my headline for a Product Manager role"] };
      }
      return detailWith([]);
    });

    render(<ChatView conversationId="conv-1" onConversationCreated={vi.fn()} />);

    expect(await screen.findByText("Fix my headline for a Product Manager role")).toBeInTheDocument();
  });

  it("renders an existing conversation's messages", async () => {
    mockedApiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/v1/assistant/conversations/conv-1") {
        return detailWith([
          {
            id: "m1",
            role: "user",
            content: "How can I improve my profile?",
            tool_call: null,
            tool_run_id: null,
            parent_message_id: null,
            created_at: "2026-01-01T00:00:00Z",
          },
          {
            id: "m2",
            role: "assistant",
            content: "Start with your headline.",
            tool_call: { intent: "explain", proposed_tool: null },
            tool_run_id: null,
            parent_message_id: "m1",
            created_at: "2026-01-01T00:00:01Z",
          },
        ]);
      }
      return detailWith([]);
    });

    render(<ChatView conversationId="conv-1" onConversationCreated={vi.fn()} />);

    expect(await screen.findByText("How can I improve my profile?")).toBeInTheDocument();
    expect(await screen.findByText("Start with your headline.")).toBeInTheDocument();
  });

  it("shows a thinking state before any content arrives, then streams in the reply", async () => {
    let sendFrame: (frame: AssistantStreamFrame) => void = () => {};
    let serverMessages: AssistantMessageResponse[] = [];
    mockedApiFetch.mockImplementation(async (path: string) => {
      if (path.includes("suggested-prompts")) return { prompts: [] };
      return detailWith(serverMessages);
    });
    mockedStreamSSE.mockImplementation(
      (_path, _body, onFrame) =>
        new Promise<void>(() => {
          sendFrame = onFrame;
        }),
    );

    render(<ChatView conversationId="conv-1" onConversationCreated={vi.fn()} />);

    const textarea = await screen.findByPlaceholderText("Ask the Assistant...");
    typeInto(textarea, "Help me with my headline");
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Thinking…")).toBeInTheDocument();
    expect(mockedStreamSSE).toHaveBeenCalledWith(
      "/api/v1/assistant/conversations/conv-1/messages?stream=true",
      { text: "Help me with my headline" },
      expect.any(Function),
      expect.anything(),
    );

    act(() => sendFrame({ type: "delta", text: '{"reply": "Sure, here is a draft."}' }));
    expect(await screen.findByText('{"reply": "Sure, here is a draft."}')).toBeInTheDocument();

    const assistantMessage: AssistantMessageResponse = {
      id: "m2",
      role: "assistant",
      content: "Sure, here is a draft.",
      tool_call: { intent: "explain", proposed_tool: null },
      tool_run_id: null,
      parent_message_id: "m1",
      created_at: "2026-01-01T00:00:01Z",
    };
    serverMessages = [
      {
        id: "m1",
        role: "user",
        content: "Help me with my headline",
        tool_call: null,
        tool_run_id: null,
        parent_message_id: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      assistantMessage,
    ];
    act(() =>
      sendFrame({
        type: "message",
        message: assistantMessage,
        quota: { metric: "assistant_messages", used: 1, limit: 30 },
        quota_warning: null,
      }),
    );
    expect(await screen.findByText("Sure, here is a draft.")).toBeInTheDocument();
  });

  it("shows a quota warning when it comes back from the server", async () => {
    mockedStreamSSE.mockImplementation(async (_path, _body, onFrame) => {
      onFrame({
        type: "message",
        message: {
          id: "m2",
          role: "assistant",
          content: "Here you go.",
          tool_call: { intent: "explain", proposed_tool: null },
          tool_run_id: null,
          parent_message_id: "m1",
          created_at: "2026-01-01T00:00:01Z",
        },
        quota: { metric: "assistant_messages", used: 28, limit: 30 },
        quota_warning:
          "You're approaching your daily assistant message limit (28/30) -- 2 left before it resets.",
      });
    });

    render(<ChatView conversationId="conv-1" onConversationCreated={vi.fn()} />);
    const textarea = await screen.findByPlaceholderText("Ask the Assistant...");
    typeInto(textarea, "One more question");
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(
      await screen.findByText(/approaching your daily assistant message limit/),
    ).toBeInTheDocument();
  });

  it("shows a stop button while streaming and lets the user abort", async () => {
    let resolveStream: () => void = () => {};
    mockedStreamSSE.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveStream = resolve;
        }),
    );

    render(<ChatView conversationId="conv-1" onConversationCreated={vi.fn()} />);
    const textarea = await screen.findByPlaceholderText("Ask the Assistant...");
    typeInto(textarea, "Hello");
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    const stopButton = await screen.findByRole("button", { name: "Stop" });
    fireEvent.click(stopButton);

    resolveStream();
    await waitFor(() => expect(mockedStreamSSE).toHaveBeenCalledTimes(1));
  });
});
