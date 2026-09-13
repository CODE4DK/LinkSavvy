import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { GrowthCoachPage } from "./GrowthCoachPage";

vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(),
  streamSSE: vi.fn(),
  ApiError: class extends Error {},
}));

vi.mock("@/lib/toast-context", () => ({
  useToast: () => ({ toasts: [], push: vi.fn(), dismiss: vi.fn() }),
}));

import { apiFetch } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockedApiFetch.mockImplementation(async (path: string) => {
    if (path === "/api/v1/growth/coach/conversation") {
      return {
        id: "coach-conv-1",
        title: null,
        mode: "coach",
        message_count: 0,
        last_message_at: null,
        is_archived: false,
        asset_id: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      };
    }
    if (path.includes("/conversations/coach-conv-1")) {
      return {
        conversation: {
          id: "coach-conv-1",
          title: null,
          mode: "coach",
          message_count: 0,
          last_message_at: null,
          is_archived: false,
          asset_id: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
        messages: [],
      };
    }
    return { prompts: [] };
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("GrowthCoachPage", () => {
  it("fetches the coach conversation and shows the coach's own empty state", async () => {
    render(
      <MemoryRouter>
        <GrowthCoachPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Growth Coach")).toBeInTheDocument();
    expect(await screen.findByText("Say hello to get started.")).toBeInTheDocument();
    expect(await screen.findByPlaceholderText("Message the Growth Coach...")).toBeInTheDocument();
  });
});
