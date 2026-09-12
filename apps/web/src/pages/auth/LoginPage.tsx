import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { loginSchema, fieldErrors, type LoginFormValues } from "@/lib/auth-schemas";
import { AuthLayout } from "./AuthLayout";
import { LinkedInButton } from "./LinkedInButton";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [values, setValues] = useState<LoginFormValues>({ email: "", password: "" });
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = loginSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      await login(parsed.data.email, parsed.data.password);
      const next = searchParams.get("next") ?? "/";
      navigate(next, { replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.code === "EMAIL_NOT_VERIFIED") {
        setErrors({ form: "Please verify your email before logging in." });
      } else if (error instanceof ApiError && error.code === "RATE_LIMITED") {
        setErrors({ form: "Too many attempts. Please wait a moment and try again." });
      } else {
        setErrors({ form: "Incorrect email or password." });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" description="Log in to your LinkSavvy command center.">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        {errors.form && (
          <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          disabled={loading}
          onChange={(e) => setValues((v) => ({ ...v, email: e.target.value }))}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={values.password}
          error={errors.password}
          disabled={loading}
          onChange={(e) => setValues((v) => ({ ...v, password: e.target.value }))}
        />
        <div className="text-right">
          <Link to="/forgot-password" className="text-sm text-primary hover:underline">
            Forgot password?
          </Link>
        </div>
        <Button type="submit" loading={loading} className="w-full">
          Log in
        </Button>
      </form>

      <div className="my-4 flex items-center gap-3 text-xs text-fg-muted">
        <div className="h-px flex-1 bg-border" />
        or
        <div className="h-px flex-1 bg-border" />
      </div>
      <LinkedInButton label="Continue with LinkedIn" />

      <p className="mt-6 text-center text-sm text-fg-muted">
        New to LinkSavvy?{" "}
        <Link to="/register" className="text-primary hover:underline">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
