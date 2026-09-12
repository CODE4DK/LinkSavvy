import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { Badge } from "@/components/ui/Badge";
import { useOnClickOutside } from "@/lib/use-on-click-outside";

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useOnClickOutside(containerRef, () => setOpen(false));

  if (!user) return null;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-bg-subtle"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
          {user.full_name.charAt(0).toUpperCase()}
        </span>
        <span className="hidden text-left sm:block">
          <span className="block font-medium text-fg">{user.full_name}</span>
        </span>
        <Badge variant={user.plan === "pro" ? "primary" : "default"}>{user.plan}</Badge>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-2 w-48 rounded-md border border-border bg-card p-1 shadow-md"
        >
          <button
            role="menuitem"
            type="button"
            className="block w-full rounded-md px-3 py-2 text-left text-sm text-fg hover:bg-bg-subtle"
            onClick={() => {
              setOpen(false);
              navigate("/settings");
            }}
          >
            Settings
          </button>
          <button
            role="menuitem"
            type="button"
            className="block w-full rounded-md px-3 py-2 text-left text-sm text-danger hover:bg-danger/10"
            onClick={() => {
              setOpen(false);
              void logout();
            }}
          >
            Log out
          </button>
        </div>
      )}
    </div>
  );
}
