import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Composer } from "./Composer";

vi.mock("@/lib/api", () => {
  class ApiError extends Error {
    status: number;
    constructor(status: number, envelope: { message: string }) {
      super(envelope.message);
      this.status = status;
    }
  }
  return { apiFetch: vi.fn(), ApiError };
});

const pushToast = vi.fn();
vi.mock("@/lib/toast-context", () => ({
  useToast: () => ({ toasts: [], push: pushToast, dismiss: vi.fn() }),
}));

import { apiFetch } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);

function renderComposer(
  initialEntries: { pathname: string; state?: unknown }[] = [{ pathname: "/content/composer" }],
) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Composer />
    </MemoryRouter>,
  );
}

describe("Composer", () => {
  it("shows the character count against the LinkedIn limit", () => {
    renderComposer();
    expect(screen.getByText("0 / 3000")).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText("Write your post here..."), {
      target: { value: "hello" },
    });
    expect(screen.getByText("5 / 3000")).toBeInTheDocument();
  });

  it("prefills from router state", () => {
    renderComposer([{ pathname: "/content/composer", state: { prefill: "Prefilled text" } }]);
    expect(screen.getByDisplayValue("Prefilled text")).toBeInTheDocument();
  });

  it("saves to Workspace via the generic assets endpoint", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      id: "asset-1",
      type: "post",
      title: "Draft",
      body: "hi",
      body_format: "text",
      source_tool_run_id: null,
      folder_id: null,
      metadata: {},
      created_at: new Date().toISOString(),
    });
    renderComposer();
    fireEvent.change(screen.getByPlaceholderText("Write your post here..."), {
      target: { value: "hi" },
    });
    fireEvent.click(screen.getByText("Save to Workspace"));
    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/api/v1/assets",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    await waitFor(() =>
      expect(pushToast).toHaveBeenCalledWith({ title: "Saved to Workspace", variant: "success" }),
    );
  });

  it("shows an accessibility warning before applying fake bold styling", () => {
    renderComposer();
    const textarea = screen.getByPlaceholderText("Write your post here...") as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "hello world" } });
    textarea.setSelectionRange(0, 5);
    fireEvent.click(screen.getByText("Bold (fake)"));
    expect(screen.getByText(/hurts accessibility/i)).toBeInTheDocument();
  });

  it("never shows a publish button and says LinkSavvy does not post", () => {
    renderComposer();
    expect(screen.queryByText(/^publish$/i)).not.toBeInTheDocument();
    expect(screen.getByText(/does not post to linkedin/i)).toBeInTheDocument();
  });
});
