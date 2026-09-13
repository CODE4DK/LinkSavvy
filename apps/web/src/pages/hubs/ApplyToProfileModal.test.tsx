import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { SnapshotDetail } from "@linksavvy/contracts";
import { ApplyToProfileModal, type ApplyToProfileRequest } from "./ApplyToProfileModal";

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
  return { apiFetch: vi.fn(), ApiError };
});

import { apiFetch } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);

const SNAPSHOT: SnapshotDetail = {
  version: 3,
  source: "manual",
  captured_at: new Date().toISOString(),
  completeness_score: 70,
  is_active: true,
  payload: {
    version: 3,
    source: "manual",
    captured_at: new Date().toISOString(),
    field_provenance: {},
    identity: { full_name: "Jamie Rivera", headline: "Old headline" },
    about: "Old about text.",
    experiences: [
      {
        title: "Senior Backend Engineer",
        company: "Acme Corp",
        is_current: true,
        description: "Old description.",
      },
    ],
  },
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ApplyToProfileModal", () => {
  it("renders nothing when there is no request", () => {
    const { container } = render(
      <ApplyToProfileModal request={null} onClose={vi.fn()} onApplied={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the current and new headline before applying", async () => {
    mockedApiFetch.mockResolvedValueOnce(SNAPSHOT);
    const request: ApplyToProfileRequest = { assetType: "headline", text: "New headline" };
    render(<ApplyToProfileModal request={request} onClose={vi.fn()} onApplied={vi.fn()} />);

    expect(await screen.findByText("Old headline")).toBeInTheDocument();
    expect(screen.getByText("New headline")).toBeInTheDocument();
  });

  it("applies a headline by PUTting the patched snapshot", async () => {
    mockedApiFetch.mockResolvedValueOnce(SNAPSHOT).mockResolvedValueOnce({
      version: 4,
      source: "manual",
      captured_at: new Date().toISOString(),
      completeness_score: 72,
      is_active: true,
    });
    const onApplied = vi.fn();
    const request: ApplyToProfileRequest = { assetType: "headline", text: "New headline" };
    render(<ApplyToProfileModal request={request} onClose={vi.fn()} onApplied={onApplied} />);

    await screen.findByText("New headline");
    fireEvent.click(screen.getByRole("button", { name: "Apply to profile" }));

    await waitFor(() => expect(onApplied).toHaveBeenCalled());
    expect(mockedApiFetch).toHaveBeenLastCalledWith(
      "/api/v1/profile/snapshot",
      expect.objectContaining({
        method: "PUT",
        body: expect.objectContaining({
          identity: expect.objectContaining({ headline: "New headline" }),
        }),
      }),
    );
  });

  it("updates the current experience's description for experience_bullets", async () => {
    mockedApiFetch.mockResolvedValueOnce(SNAPSHOT).mockResolvedValueOnce({
      version: 4,
      source: "manual",
      captured_at: new Date().toISOString(),
      completeness_score: 72,
      is_active: true,
    });
    const request: ApplyToProfileRequest = {
      assetType: "experience_bullets",
      text: "New description",
    };
    render(<ApplyToProfileModal request={request} onClose={vi.fn()} onApplied={vi.fn()} />);

    await screen.findByText("New description");
    fireEvent.click(screen.getByRole("button", { name: "Apply to profile" }));

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/v1/profile/snapshot",
        expect.objectContaining({
          method: "PUT",
          body: expect.objectContaining({
            experiences: [expect.objectContaining({ description: "New description" })],
          }),
        }),
      ),
    );
  });
});
