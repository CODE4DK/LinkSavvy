import { beforeEach, describe, expect, it, vi } from "vitest";
import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";

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
  return {
    apiFetch: vi.fn(),
    ApiError,
    setAccessToken: vi.fn(),
    getAccessToken: () => null,
  };
});

import { apiFetch, ApiError } from "@/lib/api";
import { AuthProvider, useAuth } from "./auth-context";

const mockedApiFetch = vi.mocked(apiFetch);

function StatusProbe() {
  const { status } = useAuth();
  return <div data-testid="status">{status}</div>;
}

function rateLimited(): InstanceType<typeof ApiError> {
  return new ApiError(429, {
    code: "RATE_LIMITED",
    message: "Too many requests. Please slow down and try again shortly.",
    details: { retry_after_seconds: 1 },
  });
}

function invalidRefreshToken(): InstanceType<typeof ApiError> {
  return new ApiError(401, {
    code: "INVALID_CREDENTIALS",
    message: "Invalid or expired refresh token.",
    details: {},
  });
}

describe("AuthProvider mount-time refresh", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
  });

  it(
    "retries a 429 from /auth/refresh instead of treating it as logged out",
    async () => {
      // Regression test: a transient rate-limit response used to be caught
      // by the same generic `catch` as an actually-invalid refresh token,
      // clearing the access token and forcing the user back to the login
      // screen even though their refresh cookie was perfectly valid --
      // e.g. a couple of tabs mounting AuthProvider at once. It should
      // instead wait out the limiter's own retry_after_seconds (1s here)
      // and retry once before giving up.
      mockedApiFetch.mockImplementationOnce(() => Promise.reject(rateLimited()));
      mockedApiFetch.mockImplementationOnce(() =>
        Promise.resolve({ access_token: "tok-1", expires_in: 900 }),
      );
      mockedApiFetch.mockImplementationOnce(() =>
        Promise.resolve({
          user: { id: "u1", email: "a@b.com", full_name: "A B", plan: "free" },
          feature_flags: {},
        }),
      );

      render(
        <AuthProvider>
          <StatusProbe />
        </AuthProvider>,
      );

      expect(screen.getByTestId("status").textContent).toBe("loading");

      await waitFor(() => expect(screen.getByTestId("status").textContent).toBe("authenticated"), {
        timeout: 3000,
      });
      expect(mockedApiFetch).toHaveBeenCalledTimes(3);
      expect(mockedApiFetch.mock.calls[0]?.[0]).toBe("/api/v1/auth/refresh");
      expect(mockedApiFetch.mock.calls[1]?.[0]).toBe("/api/v1/auth/refresh");
    },
    5000,
  );

  it("still ends up unauthenticated on a genuine invalid refresh token", async () => {
    mockedApiFetch.mockImplementationOnce(() => Promise.reject(invalidRefreshToken()));

    render(
      <AuthProvider>
        <StatusProbe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("status").textContent).toBe("unauthenticated"));
    expect(mockedApiFetch).toHaveBeenCalledTimes(1);
  });

  it(
    "survives two consecutive 429s in a row (bounded retry, not a single try)",
    async () => {
      // React StrictMode's dev-only double effect invocation can stack
      // with a run of full-page reloads to burn through the rate
      // limiter's burst allowance fast enough that a single retry isn't
      // always enough -- the retry needs to be bounded but more than one.
      mockedApiFetch.mockImplementationOnce(() => Promise.reject(rateLimited()));
      mockedApiFetch.mockImplementationOnce(() => Promise.reject(rateLimited()));
      mockedApiFetch.mockImplementationOnce(() =>
        Promise.resolve({ access_token: "tok-1", expires_in: 900 }),
      );
      mockedApiFetch.mockImplementationOnce(() =>
        Promise.resolve({
          user: { id: "u1", email: "a@b.com", full_name: "A B", plan: "free" },
          feature_flags: {},
        }),
      );

      render(
        <AuthProvider>
          <StatusProbe />
        </AuthProvider>,
      );

      await waitFor(() => expect(screen.getByTestId("status").textContent).toBe("authenticated"), {
        timeout: 5000,
      });
      expect(mockedApiFetch).toHaveBeenCalledTimes(4);
    },
    8000,
  );

  it("de-dupes concurrent refresh() calls into a single request", async () => {
    // Regression test for a race with the backend's single-use rotating
    // refresh token (app/services/sessions.py::rotate_refresh_token): two
    // independent calls presenting the same not-yet-rotated token would
    // both try to rotate it, and whichever request the server processes
    // second looks like token reuse and burns every session in the
    // family. React StrictMode's dev-only double invocation of this
    // component's own mount effect is exactly this shape -- it fires
    // `refresh()` twice back to back. A shared in-flight promise must
    // collapse every caller in the tab into one real request.
    let resolveRefresh: ((value: { access_token: string; expires_in: number }) => void) | undefined;
    mockedApiFetch.mockImplementation(() =>
      Promise.resolve({
        user: { id: "u1", email: "a@b.com", full_name: "A B", plan: "free" },
        feature_flags: {},
      }),
    );
    mockedApiFetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve;
        }),
    );

    const results: boolean[] = [];
    function DoubleCaller() {
      const { refresh } = useAuth();
      useEffect(() => {
        void Promise.all([refresh(), refresh()]).then((r) => results.push(...r));
      }, [refresh]);
      return null;
    }

    render(
      <AuthProvider>
        <DoubleCaller />
      </AuthProvider>,
    );

    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalled());
    // AuthProvider's own mount effect calls refresh() once, and
    // DoubleCaller calls it twice more -- three logical calls, but only
    // one should have actually reached the network.
    const refreshCalls = mockedApiFetch.mock.calls.filter((c) => c[0] === "/api/v1/auth/refresh");
    expect(refreshCalls).toHaveLength(1);

    resolveRefresh?.({ access_token: "tok-shared", expires_in: 900 });
    await waitFor(() => expect(results).toEqual([true, true]));
  });

  it(
    "gives up after exhausting its retry budget on repeated 429s",
    async () => {
      mockedApiFetch.mockImplementation(() => Promise.reject(rateLimited()));

      render(
        <AuthProvider>
          <StatusProbe />
        </AuthProvider>,
      );

      await waitFor(() => expect(screen.getByTestId("status").textContent).toBe("unauthenticated"), {
        timeout: 5000,
      });
      // 3 attempts total, not an unbounded retry loop.
      expect(mockedApiFetch).toHaveBeenCalledTimes(3);
    },
    8000,
  );
});
