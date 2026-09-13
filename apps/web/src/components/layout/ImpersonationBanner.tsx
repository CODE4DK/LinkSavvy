import { useImpersonation } from "@/lib/impersonation-context";

export function ImpersonationBanner() {
  const { active, targetLabel, expiresAt, stop } = useImpersonation();
  if (!active) return null;

  return (
    <div className="flex items-center justify-between gap-4 bg-danger px-4 py-2 text-sm text-danger-foreground">
      <span>
        Viewing as <strong>{targetLabel}</strong> (read-only)
        {expiresAt && <> — ends {new Date(expiresAt).toLocaleTimeString()}</>}
      </span>
      <button
        type="button"
        onClick={() => stop()}
        className="rounded-md border border-current px-3 py-1 text-xs font-medium"
      >
        Stop impersonating
      </button>
    </div>
  );
}
