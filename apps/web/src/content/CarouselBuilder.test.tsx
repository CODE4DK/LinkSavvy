import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CarouselBuilder } from "./CarouselBuilder";

vi.mock("@/lib/api", () => {
  class ApiError extends Error {
    status: number;
    constructor(status: number, envelope: { message: string }) {
      super(envelope.message);
      this.status = status;
    }
  }
  return { apiFetch: vi.fn(), ApiError, getAccessToken: () => "token" };
});

const pushToast = vi.fn();
vi.mock("@/lib/toast-context", () => ({
  useToast: () => ({ toasts: [], push: pushToast, dismiss: vi.fn() }),
}));

import { apiFetch } from "@/lib/api";

const mockedApiFetch = vi.mocked(apiFetch);

function renderAt(path: string, state?: unknown) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: path, state }]}>
      <Routes>
        <Route path="/content/carousel/:carouselId" element={<CarouselBuilder />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("CarouselBuilder", () => {
  it("starts with one blank slide when creating a new carousel", () => {
    renderAt("/content/carousel/new");
    expect(screen.getByText("Slide 1")).toBeInTheDocument();
  });

  it("prefills from a tool run's raw output", () => {
    renderAt("/content/carousel/new", {
      fromToolOutput: {
        cover: { headline: "Cover from tool", subhead: "Sub" },
        slides: [{ index: 1, headline: "Slide from tool", body: "Body", visual_note: "" }],
        closing: { cta: "CTA" },
        caption: "Caption",
      },
    });
    expect(screen.getAllByDisplayValue("Cover from tool").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue("Slide from tool")).toBeInTheDocument();
  });

  it("adds and removes slides", () => {
    renderAt("/content/carousel/new");
    fireEvent.click(screen.getByText("Add slide"));
    expect(screen.getByText("Slide 2")).toBeInTheDocument();
    const [firstRemoveButton] = screen.getAllByText("Remove");
    expect(firstRemoveButton).toBeDefined();
    fireEvent.click(firstRemoveButton as HTMLElement);
    expect(screen.queryByText("Slide 2")).not.toBeInTheDocument();
  });

  it("loads an existing carousel by id", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      id: "carousel-1",
      title: "Existing carousel",
      data: {
        template: "bold",
        cover: { headline: "Existing cover", subhead: "" },
        slides: [{ headline: "Existing slide", body: "Body", visual_note: "" }],
        closing: { cta: "" },
        caption: "",
      },
    });
    renderAt("/content/carousel/carousel-1");
    await waitFor(() => expect(screen.getByDisplayValue("Existing carousel")).toBeInTheDocument());
    expect(screen.getByDisplayValue("Existing cover")).toBeInTheDocument();
  });

  it("saves a new carousel via POST", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      id: "new-id",
      title: "Untitled carousel",
      data: {
        template: "clean",
        cover: { headline: "", subhead: "" },
        slides: [{ headline: "", body: "", visual_note: "" }],
        closing: { cta: "" },
        caption: "",
      },
    });
    renderAt("/content/carousel/new");
    fireEvent.click(screen.getByText("Save carousel"));
    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/api/v1/carousels",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    await waitFor(() =>
      expect(pushToast).toHaveBeenCalledWith({ title: "Carousel saved", variant: "success" }),
    );
  });
});
