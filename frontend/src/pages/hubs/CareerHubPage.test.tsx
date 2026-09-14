import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { JobDescriptionResponse, ResumeResponse, ToolSummary } from "@/contracts";
import { CareerHubPage } from "./CareerHubPage";

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

import { apiFetch } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);

const TOOLS: ToolSummary[] = [
  {
    id: "career.resume_analyzer",
    hub: "career",
    name: "Resume Analyzer",
    short_description: "Scores your resume.",
    input_schema: { type: "object", properties: {} },
    output_schema: { type: "object", properties: {} },
    required_context: [],
    optional_context: [],
    min_plan: "free",
    quota_metric: "tool_runs",
    result_renderer: "analysis",
    save_as: "analysis",
    free_daily_cap: null,
    supports_streaming: false,
    counts_as_outreach: false,
  } as unknown as ToolSummary,
];

beforeEach(() => {
  mockedApiFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function renderPage() {
  return render(
    <MemoryRouter initialEntries={[{ pathname: "/career" }]}>
      <CareerHubPage />
    </MemoryRouter>,
  );
}

describe("CareerHubPage", () => {
  it("shows the three panels and defaults to Resumes", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/career/resumes") return Promise.resolve([] as ResumeResponse[]);
      if (path === "/api/v1/career/job-descriptions")
        return Promise.resolve([] as JobDescriptionResponse[]);
      return Promise.resolve([]);
    });

    renderPage();

    expect(await screen.findByText("Career Hub")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resumes" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Job Descriptions" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tools" })).toBeInTheDocument();
    expect(await screen.findByText("No resumes yet")).toBeInTheDocument();
  });

  it("switches to the Tools panel and lists career tools", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/career/resumes") return Promise.resolve([] as ResumeResponse[]);
      if (path === "/api/v1/career/job-descriptions")
        return Promise.resolve([] as JobDescriptionResponse[]);
      if (path === "/api/v1/tools?hub=career") return Promise.resolve(TOOLS);
      return Promise.resolve([]);
    });

    renderPage();
    await screen.findByText("Career Hub");

    fireEvent.click(screen.getByRole("button", { name: "Tools" }));

    expect(await screen.findByText("Resume Analyzer")).toBeInTheDocument();
  });

  it("lets a saved job description open a resume match picker", async () => {
    const jobDescription: JobDescriptionResponse = {
      id: "jd-1",
      title: "Senior Backend Engineer",
      company: "Acme Corp",
      source: "paste",
      raw_text: "...",
      parsed: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const resume: ResumeResponse = {
      id: "resume-1",
      title: "My Resume",
      source: "upload",
      parsed: { version: 1, source: "upload" },
      version: 1,
      is_active: true,
      ats_score: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    } as unknown as ResumeResponse;

    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/career/resumes") return Promise.resolve([resume]);
      if (path === "/api/v1/career/job-descriptions") return Promise.resolve([jobDescription]);
      return Promise.resolve([]);
    });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Job Descriptions" }));

    await waitFor(() => expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Match against a resume" }));

    expect(await screen.findByRole("button", { name: "My Resume" })).toBeInTheDocument();
  });
});
