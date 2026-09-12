import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "@/lib/api";
import {
  forgotPasswordSchema,
  fieldErrors,
  type ForgotPasswordFormValues,
} from "@/lib/auth-schemas";
import { AuthLayout } from "./AuthLayout";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function ForgotPasswordPage() {
  const [values, setValues] = useState<ForgotPasswordFormValues>({ email: "" });
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = forgotPasswordSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    setLoading(true);
    try {
      await apiFetch("/api/v1/auth/forgot-password", {
        method: "POST",
        skipAuth: true,
        body: parsed.data,
      });
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <AuthLayout title="Check your inbox">
        <p className="text-sm text-fg-muted">
          If that email has an account, we&apos;ve sent a password reset link.
        </p>
        <Link to="/login" className="mt-6 block text-center text-sm text-primary hover:underline">
          Back to log in
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Forgot your password?" description="We'll email you a reset link.">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          disabled={loading}
          onChange={(e) => setValues({ email: e.target.value })}
        />
        <Button type="submit" loading={loading} className="w-full">
          Send reset link
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-fg-muted">
        <Link to="/login" className="text-primary hover:underline">
          Back to log in
        </Link>
      </p>
    </AuthLayout>
  );
}
