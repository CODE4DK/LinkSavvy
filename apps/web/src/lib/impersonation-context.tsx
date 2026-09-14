/**
 * Tracks an active admin impersonation session in the browser. The
 * server enforces the actual read-only restriction (see
 * app/middleware/impersonation_guard.py) regardless of anything here --
 * this context only drives the persistent banner and the "stop
 * impersonating" action, which restores the admin's own session by
 * refreshing from their still-valid refresh-token cookie (impersonation
 * never touches that cookie at all, only the in-memory access token).
 */

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { useAuth } from "./auth-context";
import { setAccessToken } from "./api";
import { impersonateUser } from "./admin-api";

interface ImpersonationState {
  active: boolean;
  targetLabel: string | null;
  expiresAt: string | null;
}

interface ImpersonationContextValue extends ImpersonationState {
  start: (userId: string, label: string) => Promise<void>;
  stop: () => Promise<void>;
}

const ImpersonationContext = createContext<ImpersonationContextValue | null>(null);

export function ImpersonationProvider({ children }: { children: ReactNode }) {
  const { refresh, refetchMe } = useAuth();
  const [state, setState] = useState<ImpersonationState>({
    active: false,
    targetLabel: null,
    expiresAt: null,
  });

  async function start(userId: string, label: string) {
    const response = await impersonateUser(userId);
    setAccessToken(response.access_token);
    await refetchMe();
    setState({ active: true, targetLabel: label, expiresAt: response.expires_at });
  }

  async function stop() {
    await refresh();
    await refetchMe();
    setState({ active: false, targetLabel: null, expiresAt: null });
  }

  const value = useMemo(
    () => ({ ...state, start, stop }),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- start/stop close over stable useAuth callbacks, not state that should retrigger this memo
    [state],
  );

  return (
    <ImpersonationContext.Provider value={value}>{children}</ImpersonationContext.Provider>
  );
}

export function useImpersonation(): ImpersonationContextValue {
  const ctx = useContext(ImpersonationContext);
  if (!ctx) throw new Error("useImpersonation must be used within an ImpersonationProvider");
  return ctx;
}
