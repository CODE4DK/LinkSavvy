import { useState, type FormEvent } from "react";
import { z } from "zod";
import { apiFetch, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { PasswordStrengthMeter } from "@/components/PasswordStrengthMeter";

const schema = z.object({
  currentPassword: z.string().min(1, "Required"),
  newPassword: z
    .string()
    .min(10, "Must be at least 10 characters")
    .regex(/[A-Za-z]/, "Must contain a letter")
    .regex(/[0-9]/, "Must contain a number"),
});

export function ChangePasswordSection() {
  const { logout } = useAuth();
  const { push } = useToast();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = schema.safeParse({ currentPassword, newPassword });
    if (!parsed.success) {
      const next: Partial<Record<string, string>> = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0];
        if (typeof key === "string") next[key] = issue.message;
      }
      setErrors(next);
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      await apiFetch("/api/v1/auth/change-password", {
        method: "POST",
        body: {
          current_password: parsed.data.currentPassword,
          new_password: parsed.data.newPassword,
        },
      });
      push({
        variant: "success",
        title: "Password changed",
        description: "Please log in again with your new password.",
      });
      await logout();
    } catch (error) {
      setErrors({
        form: error instanceof ApiError ? error.message : "Could not change password.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Change password</CardTitle>
        <CardDescription>You&apos;ll be signed out everywhere after this.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {errors.form && (
          <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <Input
          label="Current password"
          type="password"
          autoComplete="current-password"
          value={currentPassword}
          error={errors.currentPassword}
          disabled={loading}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
        <div>
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            error={errors.newPassword}
            disabled={loading}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <div className="mt-2">
            <PasswordStrengthMeter password={newPassword} />
          </div>
        </div>
        <div>
          <Button type="submit" loading={loading}>
            Change password
          </Button>
        </div>
      </form>
    </Card>
  );
}
