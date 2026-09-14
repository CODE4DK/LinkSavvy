import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { apiFetch, ApiError } from "@/lib/api";
import { resetPasswordSchema, fieldErrors, type ResetPasswordFormValues } from "@/lib/auth-schemas";
import { AuthLayout } from "./AuthLayout";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordStrengthMeter } from "@/components/PasswordStrengthMeter";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  const [values, setValues] = useState<ResetPasswordFormValues>({ password: "" });
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) {
      setErrors({ form: "This reset link is missing its token." });
      return;
    }
    const parsed = resetPasswordSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    setLoading(true);
    try {
      await apiFetch("/api/v1/auth/reset-password", {
        method: "POST",
        skipAuth: true,
        body: { token, new_password: parsed.data.password },
      });
      navigate("/login", { replace: true });
    } catch (error) {
      setErrors({
        form: error instanceof ApiError ? error.message : "This link is invalid or has expired.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Choose a new password">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        {errors.form && (
          <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <div>
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            value={values.password}
            error={errors.password}
            disabled={loading}
            onChange={(e) => setValues({ password: e.target.value })}
          />
          <div className="mt-2">
            <PasswordStrengthMeter password={values.password} />
          </div>
        </div>
        <Button type="submit" loading={loading} className="w-full">
          Reset password
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
