import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { MobileDrawer } from "./MobileDrawer";
import { AssistantSidePanel } from "./AssistantSidePanel";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { PaywallProvider } from "@/lib/paywall-context";

const SIDEBAR_COLLAPSED_KEY = "linksavvy.sidebar-collapsed";

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const toggleCollapsed = () => {
    setCollapsed((value) => {
      const next = !value;
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, next ? "1" : "0");
      } catch {
        // Ignore storage failures.
      }
      return next;
    });
  };

  return (
    <PaywallProvider>
      <div className="flex h-screen overflow-hidden bg-bg">
        <div className="hidden md:block">
          <Sidebar collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />
        </div>
        <MobileDrawer open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar onOpenMobileNav={() => setMobileNavOpen(true)} />
          <main className="flex-1 overflow-y-auto p-6">
            <ErrorBoundary>
              <Outlet />
            </ErrorBoundary>
          </main>
        </div>
        <AssistantSidePanel />
      </div>
    </PaywallProvider>
  );
}
