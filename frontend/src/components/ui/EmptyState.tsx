import type { ReactNode } from "react";

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border px-6 py-16 text-center">
      {icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-bg-subtle text-fg-muted">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-fg">{title}</h3>
      <p className="max-w-sm text-sm text-fg-muted">{description}</p>
      {action}
    </div>
  );
}
