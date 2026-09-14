import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { apiFetch, ApiError } from "@/lib/api";
import { registerSchema, fieldErrors, type RegisterFormValues } from "@/lib/auth-schemas";
import { AuthLayout } from "./AuthLayout";
import { LinkedInButton } from "./LinkedInButton";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordStrengthMeter } from "@/components/PasswordStrengthMeter";

export function RegisterPage() {
  const [values, setValues] = useState<RegisterFormValues>({
    fullName: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = registerSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      await apiFetch("/api/v1/auth/register", {
        method: "POST",
        skipAuth: true,
        body: {
          email: parsed.data.email,
          password: parsed.data.password,
          full_name: parsed.data.fullName,
        },
      });
      setSubmitted(true);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors({ form: error.message });
      } else {
        setErrors({ form: "Something went wrong. Please try again." });
      }
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <AuthLayout title="Check your inbox">
        <p className="text-sm text-fg-muted">
          If that email is new to us, we&apos;ve sent a verification link. Click it to activate your
          account, then come back and log in.
        </p>
        <Link to="/login" className="mt-6 block text-center text-sm text-primary hover:underline">
          Back to log in
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Create your account" description="Optimize your LinkedIn presence with AI.">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        {errors.form && (
          <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <Input
          label="Full name"
          autoComplete="name"
          value={values.fullName}
          error={errors.fullName}
          disabled={loading}
          onChange={(e) => setValues((v) => ({ ...v, fullName: e.target.value }))}
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          disabled={loading}
          onChange={(e) => setValues((v) => ({ ...v, email: e.target.value }))}
        />
        <div>
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            value={values.password}
            error={errors.password}
            disabled={loading}
            onChange={(e) => setValues((v) => ({ ...v, password: e.target.value }))}
          />
          <div className="mt-2">
            <PasswordStrengthMeter password={values.password} />
          </div>
        </div>
        <Button type="submit" loading={loading} className="w-full">
          Create account
        </Button>
      </form>

      <div className="my-4 flex items-center gap-3 text-xs text-fg-muted">
        <div className="h-px flex-1 bg-border" />
        or
        <div className="h-px flex-1 bg-border" />
      </div>
      <LinkedInButton label="Continue with LinkedIn" />

      <p className="mt-6 text-center text-sm text-fg-muted">
        Already have an account?{" "}
        <Link to="/login" className="text-primary hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
