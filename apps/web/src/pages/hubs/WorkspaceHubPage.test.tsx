import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type {
  AssetFolderResponse,
  AssetListResponse,
  WorkspaceAssetResponse,
} from "@linksavvy/contracts";
import { WorkspaceHubPage } from "./WorkspaceHubPage";

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

const NO_FOLDERS: AssetFolderResponse[] = [];

function assetPage(items: WorkspaceAssetResponse[]): AssetListResponse {
  return { items, next_cursor: null };
}

function makeAsset(overrides: Partial<WorkspaceAssetResponse> = {}): WorkspaceAssetResponse {
  return {
    id: "asset-1",
    type: "post",
    title: "My saved post",
    body: "Here is the opening line.\nMore text.",
    body_format: "text",
    metadata: {},
    source_tool_run_id: null,
    tags: [],
    is_favourite: false,
    folder_id: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    deleted_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function renderPage() {
  return render(
    <MemoryRouter initialEntries={[{ pathname: "/workspace" }]}>
      <WorkspaceHubPage />
    </MemoryRouter>,
  );
}

describe("WorkspaceHubPage", () => {
  it("shows the collections rail and an empty state with no assets", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/asset-folders") return Promise.resolve(NO_FOLDERS);
      if (path.startsWith("/api/v1/assets?")) return Promise.resolve(assetPage([]));
      return Promise.resolve(null);
    });

    renderPage();

    expect(await screen.findByText("Workspace")).toBeInTheDocument();
    expect(screen.getByText("Saved Posts")).toBeInTheDocument();
    expect(screen.getByText("Favourites")).toBeInTheDocument();
    expect(await screen.findByText("Nothing here yet")).toBeInTheDocument();
  });

  it("renders a saved asset as a card with its preview text", async () => {
    const asset = makeAsset();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/asset-folders") return Promise.resolve(NO_FOLDERS);
      if (path.startsWith("/api/v1/assets?")) return Promise.resolve(assetPage([asset]));
      return Promise.resolve(null);
    });

    renderPage();

    expect(await screen.findByText("My saved post")).toBeInTheDocument();
    expect(screen.getByText(/Here is the opening line/)).toBeInTheDocument();
  });

  it("selects an asset and shows the bulk action bar", async () => {
    const asset = makeAsset();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/asset-folders") return Promise.resolve(NO_FOLDERS);
      if (path.startsWith("/api/v1/assets?")) return Promise.resolve(assetPage([asset]));
      return Promise.resolve(null);
    });

    renderPage();
    await screen.findByText("My saved post");

    fireEvent.click(screen.getByRole("checkbox", { name: "Select My saved post" }));

    expect(await screen.findByText("1 selected")).toBeInTheDocument();
  });

  it("switches to the trash collection and lists trashed assets", async () => {
    const trashed = makeAsset({ title: "Old post", deleted_at: new Date().toISOString() });
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/asset-folders") return Promise.resolve(NO_FOLDERS);
      if (path.startsWith("/api/v1/assets?")) return Promise.resolve(assetPage([]));
      if (path === "/api/v1/assets/trash") return Promise.resolve([trashed]);
      return Promise.resolve(null);
    });

    renderPage();
    await screen.findByText("Nothing here yet");

    fireEvent.click(screen.getByText("🗑 Trash"));

    expect(await screen.findByText("Old post")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Restore" })).toBeInTheDocument();
  });

  it("filters assets by search query", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/api/v1/asset-folders") return Promise.resolve(NO_FOLDERS);
      if (path.includes("q=reliability")) {
        return Promise.resolve(assetPage([makeAsset({ title: "Backend reliability post" })]));
      }
      if (path.startsWith("/api/v1/assets?")) return Promise.resolve(assetPage([]));
      return Promise.resolve(null);
    });

    renderPage();
    await screen.findByText("Nothing here yet");

    fireEvent.change(screen.getByPlaceholderText(/Search your workspace/), {
      target: { value: "reliability" },
    });

    await waitFor(
      () =>
        expect(
          screen.getByRole("checkbox", { name: "Select Backend reliability post" }),
        ).toBeInTheDocument(),
      { timeout: 1000 },
    );
  });
});
