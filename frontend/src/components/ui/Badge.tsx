import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "default" | "primary" | "success" | "warning" | "danger";

const VARIANT_CLASSES: Record<Variant, string> = {
  default: "bg-bg-subtle text-fg-muted",
  primary: "bg-primary/15 text-primary",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  danger: "bg-danger/15 text-danger",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ variant = "default", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
}
