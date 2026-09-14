import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Calendar } from "./Calendar";

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

function planFixture(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "plan-1",
    asset_id: null,
    title: "My idea",
    body_preview: "",
    content_type: "post",
    status: "idea",
    planned_for: new Date().toISOString().slice(0, 10),
    planned_time: null,
    posted_at: null,
    reminder_at: null,
    recurrence_rule: null,
    tags: [],
    performance: {},
    notes: "",
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    ...overrides,
  };
}

function setupDefaultFetches(plans: unknown[] = [planFixture()]) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path.startsWith("/api/v1/content-plans/consistency")) {
      return Promise.resolve(
        Array.from({ length: 12 }, (_, i) => ({
          week_start: `2026-01-${String(i + 1).padStart(2, "0")}`,
          posted_count: 0,
        })),
      );
    }
    if (path.startsWith("/api/v1/content-plans?")) {
      return Promise.resolve(plans);
    }
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

describe("Calendar", () => {
  it("renders plans loaded for the visible range", async () => {
    setupDefaultFetches();
    render(
      <MemoryRouter initialEntries={[{ pathname: "/content/calendar" }]}>
        <Calendar />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("My idea")).toBeInTheDocument());
  });

  it("switches to list view", async () => {
    setupDefaultFetches();
    render(
      <MemoryRouter initialEntries={[{ pathname: "/content/calendar" }]}>
        <Calendar />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("My idea")).toBeInTheDocument());
    fireEvent.click(screen.getByText("List"));
    expect(screen.getByText("My idea")).toBeInTheDocument();
  });

  it("opens the create modal prefilled from Composer's draftBody handoff", async () => {
    setupDefaultFetches([]);
    render(
      <MemoryRouter
        initialEntries={[{ pathname: "/content/calendar", state: { draftBody: "Handoff text" } }]}
      >
        <Calendar />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByDisplayValue("Handoff text")).toBeInTheDocument());
  });

  it("shows the consistency strip once loaded", async () => {
    setupDefaultFetches();
    render(
      <MemoryRouter initialEntries={[{ pathname: "/content/calendar" }]}>
        <Calendar />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Consistency, last 12 weeks")).toBeInTheDocument());
  });

  it("opens plan detail and shows status options", async () => {
    setupDefaultFetches();
    render(
      <MemoryRouter initialEntries={[{ pathname: "/content/calendar" }]}>
        <Calendar />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("My idea")).toBeInTheDocument());
    fireEvent.click(screen.getByText("My idea"));
    expect(screen.getByText("Mark as posted")).toBeInTheDocument();
  });
});
