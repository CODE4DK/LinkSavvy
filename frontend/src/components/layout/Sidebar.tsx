import { NavLink } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { PRIMARY_NAV_ITEMS } from "@/lib/nav-items";
import { cn } from "@/lib/cn";

export interface SidebarProps {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  className?: string;
}

export function Sidebar({ collapsed, onToggleCollapsed, className }: SidebarProps) {
  const { featureFlags, user } = useAuth();

  return (
    <nav
      aria-label="Primary"
      className={cn(
        "flex h-full flex-col border-r border-border bg-bg-subtle transition-[width]",
        collapsed ? "w-sidebar-collapsed" : "w-sidebar",
        className,
      )}
    >
      <div className="flex h-topbar items-center justify-between px-4">
        {!collapsed && <span className="text-lg font-semibold text-fg">LinkSavvy</span>}
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="rounded-md p-1.5 text-fg-muted hover:bg-border/30 hover:text-fg"
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>

      <ul className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
        {PRIMARY_NAV_ITEMS.map((item) => {
          const enabled = item.flag === undefined || featureFlags[item.flag];
          return (
            <li key={item.path}>
              <NavLink
                to={item.path}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  cn(
                    "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-fg-muted hover:bg-border/30 hover:text-fg",
                    !enabled && "opacity-60",
                  )
                }
              >
                <span className={cn("truncate", collapsed && "sr-only")}>{item.label}</span>
                {collapsed && <span aria-hidden="true">{item.label.charAt(0)}</span>}
                {!enabled && !collapsed && (
                  <span className="ml-auto rounded-full bg-bg px-1.5 py-0.5 text-[10px] text-fg-muted">
                    Soon
                  </span>
                )}
              </NavLink>
            </li>
          );
        })}
        {user?.role === "admin" && (
          <li>
            <NavLink
              to="/admin"
              title={collapsed ? "Admin" : undefined}
              className={({ isActive }) =>
                cn(
                  "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-fg-muted hover:bg-border/30 hover:text-fg",
                )
              }
            >
              <span className={cn("truncate", collapsed && "sr-only")}>Admin</span>
              {collapsed && <span aria-hidden="true">A</span>}
            </NavLink>
          </li>
        )}
      </ul>
    </nav>
  );
}
