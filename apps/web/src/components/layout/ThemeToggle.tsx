import { useTheme, type ThemePreference } from "@/lib/theme-context";
import { cn } from "@/lib/cn";

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
];

export function ThemeToggle() {
  const { preference, setPreference } = useTheme();

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="inline-flex rounded-md border border-border p-0.5"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={preference === option.value}
          onClick={() => setPreference(option.value)}
          className={cn(
            "rounded-[calc(theme(borderRadius.md)-2px)] px-2.5 py-1 text-xs font-medium transition-colors",
            preference === option.value
              ? "bg-primary text-primary-foreground"
              : "text-fg-muted hover:text-fg",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
