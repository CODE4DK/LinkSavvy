import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminPage } from "./AdminPage";

vi.mock("@/lib/admin-api", () => ({
  searchUsers: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  listFeatureFlags: vi.fn().mockResolvedValue([
    { key: "hub.profile", enabled_globally: false, rollout_percent: 0, description: null },
  ]),
  listSubscriptions: vi.fn().mockResolvedValue([]),
  getAiOpsOverview: vi.fn().mockResolvedValue({
    cost_by_day: [],
    cost_by_model: [],
    cost_by_prompt: [],
    outcome_rates: {
      total: 0,
      invalid_output_rate: 0,
      fallback_rate: 0,
      policy_blocked_rate: 0,
      provider_error_rate: 0,
    },
    slowest_prompts: [],
  }),
  listModerationFlags: vi.fn().mockResolvedValue([]),
  getPlatformHealth: vi.fn().mockResolvedValue({
    queue_depth: { queued: 0, leased: 0, dead: 0, failed_last_hour: 0 },
    dead_jobs: [],
    circuit_breakers: {},
  }),
}));

vi.mock("@/lib/impersonation-context", () => ({
  useImpersonation: () => ({ start: vi.fn(), stop: vi.fn(), active: false }),
}));

describe("AdminPage", () => {
  it("switches between tabs", async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Feature flags" }));
    await waitFor(() => expect(screen.getByText("hub.profile")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Platform health" }));
    await waitFor(() => expect(screen.getByText("Queued")).toBeInTheDocument());
  });
});
