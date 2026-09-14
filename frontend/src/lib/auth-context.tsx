import type { LoginResponse, MeResponse, UserPublic } from "@/contracts";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ApiError, apiFetch, setAccessToken } from "./api";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: UserPublic | null;
  featureFlags: Record<string, boolean>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Silently refreshes the access token from the refresh cookie. */
  refresh: () => Promise<boolean>;
  refetchMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function performRefresh(): Promise<boolean> {
  const maxAttempts = 3;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const data = await apiFetch<{ access_token: string; expires_in: number }>(
        "/api/v1/auth/refresh",
        { method: "POST", skipAuth: true },
      );
      setAccessToken(data.access_token);
      return true;
    } catch (error) {
      // A 429 here means the auth-endpoint rate limiter fired, not that
      // the refresh-token cookie is invalid -- treating the two the same
      // used to log a user with a perfectly valid session out. Wait out
      // the limiter's own suggested backoff and retry a bounded number
      // of times before actually giving up.
      if (attempt < maxAttempts && error instanceof ApiError && error.status === 429) {
        const retryAfter = Number(error.details.retry_after_seconds) || 2;
        await new Promise((resolve) => setTimeout(resolve, Math.min(retryAfter, 10) * 1000));
        continue;
      }
      setAccessToken(null);
      return false;
    }
  }
  setAccessToken(null);
  return false;
}

// Refresh tokens rotate and are single-use (see app/services/sessions.py):
// presenting an already-rotated token is treated as theft and burns every
// session in its family. Two /auth/refresh calls in flight at once for the
// same tab -- e.g. React StrictMode's dev-only double invocation of this
// component's mount effect -- would both read the same not-yet-rotated
// token, and whichever finishes second would trip that reuse check and log
// the user out of every device. A single module-level in-flight promise
// makes every caller in this tab share one real request instead.
let inFlightRefresh: Promise<boolean> | null = null;

function sharedRefresh(): Promise<boolean> {
  if (!inFlightRefresh) {
    inFlightRefresh = performRefresh().finally(() => {
      inFlightRefresh = null;
    });
  }
  return inFlightRefresh;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<UserPublic | null>(null);
  const [featureFlags, setFeatureFlags] = useState<Record<string, boolean>>({});

  const loadMe = useCallback(async () => {
    const me = await apiFetch<MeResponse>("/api/v1/me");
    setUser(me.user);
    setFeatureFlags(me.feature_flags);
  }, []);

  const refresh = useCallback((): Promise<boolean> => sharedRefresh(), []);

  useEffect(() => {
    (async () => {
      const refreshed = await refresh();
      if (!refreshed) {
        setStatus("unauthenticated");
        return;
      }
      try {
        await loadMe();
        setStatus("authenticated");
      } catch {
        setAccessToken(null);
        setStatus("unauthenticated");
      }
    })();
  }, [refresh, loadMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const data = await apiFetch<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        skipAuth: true,
        body: { email, password },
      });
      setAccessToken(data.access_token);
      setUser(data.user);
      try {
        await loadMe();
      } catch {
        // Non-fatal — we already have the user from the login response.
      }
      setStatus("authenticated");
    },
    [loadMe],
  );

  const logout = useCallback(async () => {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
    }
    setAccessToken(null);
    setUser(null);
    setFeatureFlags({});
    setStatus("unauthenticated");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, featureFlags, login, logout, refresh, refetchMe: loadMe }),
    [status, user, featureFlags, login, logout, refresh, loadMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
