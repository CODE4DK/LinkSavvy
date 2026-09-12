import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { apiFetch, ApiError } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";

export function DeleteAccountSection() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!user) return null;

  const emailMatches = confirmEmail.trim().toLowerCase() === user.email.toLowerCase();

  const handleDelete = async () => {
    if (!emailMatches) return;
    setLoading(true);
    setError(null);
    try {
      await apiFetch("/api/v1/me", {
        method: "DELETE",
        body: { current_password: currentPassword || undefined },
      });
      await logout();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-danger/30">
      <CardHeader>
        <CardTitle className="text-danger">Delete account</CardTitle>
        <CardDescription>
          This deactivates your account. This action cannot be undone from the app.
        </CardDescription>
      </CardHeader>
      <div>
        <Button variant="danger" onClick={() => setOpen(true)}>
          Delete my account
        </Button>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Delete your account?">
        <p className="text-sm text-fg-muted">
          Type <span className="font-medium text-fg">{user.email}</span> to confirm. This will sign
          you out of every device.
        </p>
        <div className="mt-4 flex flex-col gap-3">
          {error && (
            <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </p>
          )}
          <Input
            label="Confirm email"
            value={confirmEmail}
            onChange={(e) => setConfirmEmail(e.target.value)}
            disabled={loading}
          />
          {user.email && (
            <Input
              label="Current password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              disabled={loading}
              hint="Leave blank if you signed up with LinkedIn only."
            />
          )}
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant="danger"
            disabled={!emailMatches}
            loading={loading}
            onClick={handleDelete}
          >
            Delete account
          </Button>
        </div>
      </Modal>
    </Card>
  );
}
