import type { ReactNode } from "react";

export function AuthLayout({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-subtle px-4 py-12">
      <div className="w-full max-w-sm rounded-lg border border-border bg-card p-8 shadow-md">
        <h1 className="text-2xl font-semibold text-fg">{title}</h1>
        {description && <p className="mt-1 text-sm text-fg-muted">{description}</p>}
        <div className="mt-6">{children}</div>
      </div>
    </div>
  );
}
