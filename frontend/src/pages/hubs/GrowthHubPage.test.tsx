import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type {
  GrowthGoalResponse,
  GrowthScoreHistoryResponse,
  GrowthScoreResponse,
  GrowthScoresResponse,
  WeeklyPlanResponse,
} from "@/contracts";
import { GrowthHubPage } from "./GrowthHubPage";

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
  return { apiFetch: vi.fn(), ApiError, getAccessToken: () => null };
});

vi.mock("@/lib/toast-context", () => ({
  useToast: () => ({ toasts: [], push: vi.fn(), dismiss: vi.fn() }),
}));

import { apiFetch, ApiError } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);

function skippedScore(scoreType: string): GrowthScoreResponse {
  return {
    score_type: scoreType,
    value: null,
    status: "skipped",
    components: [],
    computed_at: new Date().toISOString(),
    scoring_version: "2026.1",
    needed: { reason: "Commit a profile snapshot to unlock this score." },
  } as unknown as GrowthScoreResponse;
}

const EMPTY_SCORES: GrowthScoresResponse = {
  health: skippedScore("health"),
  visibility: skippedScore("visibility"),
  consistency: skippedScore("consistency"),
  personal_branding: skippedScore("personal_branding"),
};

const EMPTY_HISTORY: GrowthScoreHistoryResponse = {
  health: [],
  visibility: [],
  consistency: [],
  personal_branding: [],
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function renderPage() {
  return render(
    <MemoryRouter initialEntries={[{ pathname: "/growth" }]}>
      <GrowthHubPage />
    </MemoryRouter>,
  );
}

describe("GrowthHubPage", () => {
  it("shows all four scores as not-started for a fresh user", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/growth/scores") return Promise.resolve(EMPTY_SCORES);
      if (path === "/api/v1/growth/scores/history") return Promise.resolve(EMPTY_HISTORY);
      if (path === "/api/v1/growth/plan")
        return Promise.reject(
          new ApiError(404, { code: "NOT_FOUND", message: "none", details: {} }),
        );
      if (path === "/api/v1/growth/goal")
        return Promise.reject(
          new ApiError(404, { code: "NOT_FOUND", message: "none", details: {} }),
        );
      return Promise.resolve(null);
    });

    renderPage();

    expect(await screen.findByText("Growth Hub")).toBeInTheDocument();
    expect(await screen.findAllByText("not started")).toHaveLength(4);
    expect(await screen.findByText("No plan yet this week")).toBeInTheDocument();
  });

  it("renders the current weekly plan and toggles an item", async () => {
    const plan: WeeklyPlanResponse = {
      id: "plan-1",
      week_start: "2026-09-14",
      generated_at: new Date().toISOString(),
      focus: "Keep steadily improving your LinkedIn presence this week.",
      items: [
        {
          title: "Sharpen your headline",
          why_now: "It's vague.",
          tool_id: null,
          estimated_minutes: 20,
          expected_impact: 8,
          category: "profile",
          completed: false,
        },
      ],
      status: "active",
      completed_count: 0,
      reflection: null,
    };

    mockedApiFetch.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === "/api/v1/growth/scores") return Promise.resolve(EMPTY_SCORES);
      if (path === "/api/v1/growth/scores/history") return Promise.resolve(EMPTY_HISTORY);
      if (path === "/api/v1/growth/plan" && !options?.method) return Promise.resolve(plan);
      if (path === "/api/v1/growth/plan/plan-1/items/0")
        return Promise.resolve({
          ...plan,
          completed_count: 1,
          items: [{ ...plan.items[0], completed: true }],
        });
      if (path === "/api/v1/growth/goal")
        return Promise.reject(
          new ApiError(404, { code: "NOT_FOUND", message: "none", details: {} }),
        );
      return Promise.resolve(null);
    });

    renderPage();

    expect(await screen.findByText("Sharpen your headline")).toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox");
    fireEvent.click(checkbox);

    await waitFor(() => expect(screen.getByText("1 of 1 done this week")).toBeInTheDocument());
  });

  it("shows the current goal when one is active", async () => {
    const goal: GrowthGoalResponse = {
      id: "goal-1",
      goal_type: "role_change",
      target_role: "Staff Engineer",
      target_description: "",
      horizon_weeks: 12,
      started_at: new Date().toISOString(),
      status: "active",
      baseline_scores: {},
    };

    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/growth/scores") return Promise.resolve(EMPTY_SCORES);
      if (path === "/api/v1/growth/scores/history") return Promise.resolve(EMPTY_HISTORY);
      if (path === "/api/v1/growth/plan")
        return Promise.reject(
          new ApiError(404, { code: "NOT_FOUND", message: "none", details: {} }),
        );
      if (path === "/api/v1/growth/goal") return Promise.resolve(goal);
      return Promise.resolve(null);
    });

    renderPage();

    expect(await screen.findByText(/role_change -- Staff Engineer/)).toBeInTheDocument();
  });
});
