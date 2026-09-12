import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";

export interface TopBarProps {
  onOpenMobileNav: () => void;
}

export function TopBar({ onOpenMobileNav }: TopBarProps) {
  return (
    <header className="flex h-topbar items-center gap-4 border-b border-border bg-bg px-4">
      <button
        type="button"
        onClick={onOpenMobileNav}
        aria-label="Open navigation menu"
        className="rounded-md p-2 text-fg hover:bg-bg-subtle md:hidden"
      >
        ☰
      </button>

      <div className="flex-1">
        <input
          type="search"
          placeholder="Search LinkSavvy… (coming soon)"
          disabled
          aria-label="Search"
          className="hidden h-9 w-full max-w-md rounded-md border border-border bg-bg-subtle px-3 text-sm text-fg-muted placeholder:text-fg-muted sm:block"
        />
      </div>

      <ThemeToggle />
      <UserMenu />
    </header>
  );
}
