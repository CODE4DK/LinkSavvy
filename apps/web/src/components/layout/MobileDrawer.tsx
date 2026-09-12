import { NavLink } from "react-router-dom";
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { useAuth } from "@/lib/auth-context";
import { PRIMARY_NAV_ITEMS } from "@/lib/nav-items";
import { cn } from "@/lib/cn";

export interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function MobileDrawer({ open, onClose }: MobileDrawerProps) {
  const { featureFlags } = useAuth();

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-40 md:hidden">
      <div className="absolute inset-0 bg-overlay/50" onClick={onClose} aria-hidden="true" />
      <nav
        aria-label="Primary"
        className="relative z-10 flex h-full w-72 flex-col bg-bg-subtle p-2 shadow-lg"
      >
        <div className="flex h-topbar items-center justify-between px-2">
          <span className="text-lg font-semibold text-fg">LinkSavvy</span>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="rounded-md p-1.5 text-fg-muted hover:bg-border/30"
          >
            ✕
          </button>
        </div>
        <ul className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
          {PRIMARY_NAV_ITEMS.map((item) => {
            const enabled = item.flag === undefined || featureFlags[item.flag];
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center rounded-md px-3 py-2 text-sm font-medium",
                      isActive ? "bg-primary/10 text-primary" : "text-fg-muted hover:bg-border/30",
                      !enabled && "opacity-60",
                    )
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>,
    document.body,
  );
}
