import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PaywallProvider } from "./paywall-context";
import { apiFetch } from "./api";

vi.mock("./billing-api", () => ({
  createCheckout: vi.fn().mockResolvedValue({ checkout_url: "https://checkout.test/abc" }),
}));

function mockQuotaExceededResponse() {
  return {
    ok: false,
    status: 402,
    json: async () => ({
      error: {
        code: "QUOTA_EXCEEDED",
        message: "quota exceeded for tool_runs: 20/20 per day",
        details: {
          metric: "tool_runs",
          used: 20,
          limit: 20,
          window: "day",
          resets_at: "2026-01-01T00:00:00Z",
          upgrade_required: true,
        },
      },
    }),
  } as unknown as Response;
}

describe("PaywallProvider", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the contextual paywall when any apiFetch call hits QUOTA_EXCEEDED", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockQuotaExceededResponse()));

    render(
      <MemoryRouter>
        <PaywallProvider>
          <div>app content</div>
        </PaywallProvider>
      </MemoryRouter>,
    );

    // Something elsewhere in the app makes a call that gets a 402 --
    // the provider should surface it without that caller needing to
    // know about the paywall at all.
    await expect(apiFetch("/api/v1/tools/some-tool/run")).rejects.toThrow();

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(screen.getByText(/tool runs limit/i)).toBeInTheDocument();
    expect(screen.getByText(/used 20 of 20/i)).toBeInTheDocument();
  });

  it("starts checkout and redirects when the user clicks upgrade", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockQuotaExceededResponse()));
    delete (window as unknown as { location?: unknown }).location;
    (window as unknown as { location: { href: string } }).location = { href: "" };

    render(
      <MemoryRouter>
        <PaywallProvider>
          <div>app content</div>
        </PaywallProvider>
      </MemoryRouter>,
    );

    await expect(apiFetch("/api/v1/tools/some-tool/run")).rejects.toThrow();
    await waitFor(() => screen.getByRole("dialog"));

    fireEvent.click(screen.getByRole("button", { name: /upgrade to pro/i }));

    await waitFor(() => {
      expect(window.location.href).toBe("https://checkout.test/abc");
    });
  });
});
