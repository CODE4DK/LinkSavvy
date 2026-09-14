import { forwardRef, useId, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;
    const errorId = error ? `${inputId}-error` : undefined;
    const hintId = hint ? `${inputId}-hint` : undefined;

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-fg">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={cn(errorId, hintId) || undefined}
          className={cn(
            "h-10 w-full rounded-md border bg-bg px-3 text-sm text-fg placeholder:text-fg-muted",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error ? "border-danger" : "border-border",
            className,
          )}
          {...props}
        />
        {error && (
          <p id={errorId} className="text-sm text-danger">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={hintId} className="text-sm text-fg-muted">
            {hint}
          </p>
        )}
      </div>
    );
  },
);
Input.displayName = "Input";
