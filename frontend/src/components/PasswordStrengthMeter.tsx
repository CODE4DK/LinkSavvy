import { cn } from "@/lib/cn";

export function scorePassword(password: string): number {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 10) score += 1;
  if (password.length >= 14) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return Math.min(score, 4);
}

const LABELS = ["Too short", "Weak", "Fair", "Good", "Strong"];
const COLORS = ["bg-danger", "bg-danger", "bg-warning", "bg-success", "bg-success"];

export function PasswordStrengthMeter({ password }: { password: string }) {
  const score = scorePassword(password);
  const label = LABELS[score];

  return (
    <div className="flex flex-col gap-1" aria-live="polite">
      <div className="flex gap-1" role="presentation">
        {[0, 1, 2, 3].map((segment) => (
          <div
            key={segment}
            className={cn(
              "h-1.5 flex-1 rounded-full bg-bg-subtle transition-colors",
              segment < score && COLORS[score],
            )}
          />
        ))}
      </div>
      {password && <p className="text-xs text-fg-muted">Password strength: {label}</p>}
    </div>
  );
}
