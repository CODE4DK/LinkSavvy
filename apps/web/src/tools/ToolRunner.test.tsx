import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ToolSummary } from "@linksavvy/contracts";
import { ToolRunner } from "./ToolRunner";

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

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { plan: "free", role: "user" } }),
}));

const pushToast = vi.fn();
vi.mock("@/lib/toast-context", () => ({
  useToast: () => ({ toasts: [], push: pushToast, dismiss: vi.fn() }),
}));

import { apiFetch, streamSSE } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);
const mockedStreamSSE = vi.mocked(streamSSE);

const FIXTURE_TOOL: ToolSummary = {
  id: "test.fixture",
  hub: "profile",
  name: "Fixture Tool",
  short_description: "A tool for ToolRunner tests.",
  input_schema: {
    type: "object",
    properties: {
      user_supplied_text: { type: "string", format: "textarea", title: "Your text" },
      target_role: { type: "string", title: "Target role" },
    },
    required: ["user_supplied_text"],
  },
  output_schema: { type: "object", properties: {} },
  required_context: ["user_supplied_text"],
  optional_context: [],
  min_plan: "free",
  quota_metric: "tool_runs",
  result_renderer: "document",
  save_as: "analysis",
  free_daily_cap: null,
  supports_streaming: false,
} as unknown as ToolSummary;

const STREAMING_TOOL: ToolSummary = {
  ...FIXTURE_TOOL,
  id: "test.stream",
  supports_streaming: true,
};

function documentOutput(text: string) {
  return { sections: [{ body: text }] };
}

function typeInto(element: HTMLElement, value: string) {
  fireEvent.change(element, { target: { value } });
}

beforeEach(() => {
  localStorage.clear();
  mockedApiFetch.mockReset();
  mockedStreamSSE.mockReset();
  pushToast.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ToolRunner", () => {
  it("shows a not-found state for an unknown tool id", async () => {
    mockedApiFetch.mockResolvedValueOnce([FIXTURE_TOOL]);
    render(<ToolRunner toolId="no.such.tool" />);
    expect(await screen.findByText(/tool not found/i)).toBeInTheDocument();
  });

  it("renders a generic form from the tool's input schema", async () => {
    mockedApiFetch.mockResolvedValueOnce([FIXTURE_TOOL]);
    render(<ToolRunner toolId="test.fixture" />);

    expect(await screen.findByText("Fixture Tool")).toBeInTheDocument();
    expect(screen.getByText("Your text")).toBeInTheDocument();
    expect(screen.getByText("Target role")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run" })).toBeInTheDocument();
  });

  it("blocks the run and shows a field error when a required field is blank", async () => {
    mockedApiFetch.mockResolvedValueOnce([FIXTURE_TOOL]);
    render(<ToolRunner toolId="test.fixture" />);

    await screen.findByText("Fixture Tool");
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/is required/i)).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledTimes(1); // only the initial tool list fetch
  });

  it("runs the tool, renders the result, and shows the context-used panel", async () => {
    mockedApiFetch.mockResolvedValueOnce([FIXTURE_TOOL]).mockResolvedValueOnce({
      run_id: "run-1",
      output: documentOutput("Generated output text"),
      context_used: ["user_supplied_text"],
      quota: { metric: "tool_runs", used: 1, limit: 15 },
    });

    render(<ToolRunner toolId="test.fixture" />);

    await screen.findByText("Fixture Tool");
    typeInto(screen.getByLabelText("Your text"), "hello there");
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText("Generated output text")).toBeInTheDocument();
    expect(screen.getByText(/1 \/ 15 tool_runs used/)).toBeInTheDocument();

    expect(mockedApiFetch).toHaveBeenLastCalledWith(
      "/api/v1/tools/test.fixture/run",
      expect.objectContaining({
        method: "POST",
        body: { input: { user_supplied_text: "hello there" } },
      }),
    );

    fireEvent.click(screen.getByText(/what this used/i));
    expect(screen.getByText("user_supplied_text")).toBeInTheDocument();
  });

  it("streams a tool that supports_streaming and finalizes into a persisted run", async () => {
    mockedApiFetch.mockResolvedValueOnce([STREAMING_TOOL]);
    mockedStreamSSE.mockImplementation(async (_path, _body, onFrame) => {
      onFrame({ type: "meta", correlation_id: "c1", model: "m", provider: "fake", cached: false });
      onFrame({ type: "delta", text: '{"sections": [{"body": "streamed' });
      onFrame({ type: "delta", text: ' text"}]}' });
      onFrame({ type: "done", tokens_in: 1, tokens_out: 1, cost_minor: 0 });
      onFrame({
        type: "tool_run",
        run_id: "run-stream-1",
        context_used: ["user_supplied_text"],
        quota: { metric: "tool_runs", used: 2, limit: 15 },
      });
    });

    render(<ToolRunner toolId="test.stream" />);

    await screen.findByText("Fixture Tool");
    typeInto(screen.getByLabelText("Your text"), "hi");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Run" }));
    });

    expect(await screen.findByText("streamed text")).toBeInTheDocument();
    expect(mockedStreamSSE).toHaveBeenCalledWith(
      "/api/v1/tools/test.stream/run?stream=true",
      { input: { user_supplied_text: "hi" } },
      expect.any(Function),
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it("regenerates with a nudge against the run that produced the result", async () => {
    mockedApiFetch
      .mockResolvedValueOnce([FIXTURE_TOOL])
      .mockResolvedValueOnce({
        run_id: "run-1",
        output: documentOutput("first"),
        context_used: ["user_supplied_text"],
        quota: { metric: "tool_runs", used: 1, limit: 15 },
      })
      .mockResolvedValueOnce({
        run_id: "run-2",
        output: documentOutput("shorter"),
        context_used: ["user_supplied_text"],
        quota: { metric: "tool_runs", used: 2, limit: 15 },
      });

    render(<ToolRunner toolId="test.fixture" />);
    await screen.findByText("Fixture Tool");
    typeInto(screen.getByLabelText("Your text"), "hello");
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    await screen.findByText("first");

    typeInto(screen.getByPlaceholderText(/nudge for regeneration/i), "make it shorter");
    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));

    expect(await screen.findByText("shorter")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenLastCalledWith(
      "/api/v1/tools/runs/run-1/regenerate",
      expect.objectContaining({ method: "POST", body: { nudge: "make it shorter" } }),
    );
  });

  it("rates a run with a thumbs-up", async () => {
    mockedApiFetch
      .mockResolvedValueOnce([FIXTURE_TOOL])
      .mockResolvedValueOnce({
        run_id: "run-1",
        output: documentOutput("first"),
        context_used: [],
        quota: { metric: "tool_runs", used: 1, limit: 15 },
      })
      .mockResolvedValueOnce({ run_id: "run-1", rating: "up", feedback_text: null });

    render(<ToolRunner toolId="test.fixture" />);
    await screen.findByText("Fixture Tool");
    typeInto(screen.getByLabelText("Your text"), "hello");
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    await screen.findByText("first");

    fireEvent.click(screen.getByRole("button", { name: "👍" }));

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/v1/tools/runs/run-1/rate",
        expect.objectContaining({ method: "POST", body: { rating: "up", feedback_text: null } }),
      ),
    );
  });

  it("saves a run to the workspace", async () => {
    mockedApiFetch
      .mockResolvedValueOnce([FIXTURE_TOOL])
      .mockResolvedValueOnce({
        run_id: "run-1",
        output: documentOutput("first"),
        context_used: [],
        quota: { metric: "tool_runs", used: 1, limit: 15 },
      })
      .mockResolvedValueOnce({
        id: "asset-1",
        type: "analysis",
        title: "Fixture Tool",
        body: "first",
        body_format: "text",
        source_tool_run_id: "run-1",
        folder_id: null,
        created_at: new Date().toISOString(),
      });

    render(<ToolRunner toolId="test.fixture" />);
    await screen.findByText("Fixture Tool");
    typeInto(screen.getByLabelText("Your text"), "hello");
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    await screen.findByText("first");

    fireEvent.click(screen.getByRole("button", { name: "Save to Workspace" }));

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/v1/tools/runs/run-1/save",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(await screen.findByText("Saved")).toBeInTheDocument();
  });

  it("loads and lists run history", async () => {
    mockedApiFetch.mockResolvedValueOnce([FIXTURE_TOOL]).mockResolvedValueOnce([
      {
        id: "run-9",
        input: { user_supplied_text: "old" },
        output: documentOutput("old output"),
        context_used: ["user_supplied_text"],
        status: "succeeded",
        rating: null,
        feedback_text: null,
        parent_run_id: null,
        created_at: new Date().toISOString(),
      },
    ]);

    render(<ToolRunner toolId="test.fixture" />);
    await screen.findByText("Fixture Tool");

    fireEvent.click(screen.getByRole("button", { name: "Show history" }));

    const historyLabel = await screen.findByText("succeeded");
    const historyButton = historyLabel.closest("button");
    expect(historyButton).not.toBeNull();
    expect(within(historyButton as HTMLElement).getByText("succeeded")).toBeInTheDocument();
  });
});
