import type { LoginResponse, MeResponse, UserPublic } from "@linksavvy/contracts";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<UserPublic | null>(null);
  const [featureFlags, setFeatureFlags] = useState<Record<string, boolean>>({});

  const loadMe = useCallback(async () => {
    const me = await apiFetch<MeResponse>("/api/v1/me");
    setUser(me.user);
    setFeatureFlags(me.feature_flags);
  }, []);

  const refresh = useCallback(async (): Promise<boolean> => {
    try {
      const data = await apiFetch<{ access_token: string; expires_in: number }>(
        "/api/v1/auth/refresh",
        { method: "POST", skipAuth: true },
      );
      setAccessToken(data.access_token);
      return true;
    } catch {
      setAccessToken(null);
      return false;
    }
  }, []);

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
