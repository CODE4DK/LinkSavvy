import { useToast } from "@/lib/toast-context";
import { cn } from "@/lib/cn";

const VARIANT_CLASSES = {
  default: "border-border bg-card text-fg",
  success: "border-success/30 bg-success/10 text-success",
  danger: "border-danger/30 bg-danger/10 text-danger",
};

export function ToastViewport() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={cn(
            "flex items-start justify-between gap-3 rounded-md border p-4 shadow-md",
            VARIANT_CLASSES[toast.variant],
          )}
        >
          <div>
            <p className="text-sm font-medium">{toast.title}</p>
            {toast.description && <p className="mt-1 text-sm opacity-80">{toast.description}</p>}
          </div>
          <button
            type="button"
            onClick={() => dismiss(toast.id)}
            className="text-sm opacity-60 hover:opacity-100"
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
