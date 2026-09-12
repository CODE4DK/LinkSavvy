import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import type { UpdateProfileRequest, UserPublic } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";

const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Berlin",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Australia/Sydney",
];

export function ProfileSection() {
  const { user, refetchMe } = useAuth();
  const { push } = useToast();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [timezone, setTimezone] = useState(user?.timezone ?? "UTC");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (body: UpdateProfileRequest) =>
      apiFetch<UserPublic>("/api/v1/me", { method: "PATCH", body }),
    onSuccess: async () => {
      await refetchMe();
      push({ variant: "success", title: "Profile updated" });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Could not update profile.");
    },
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    mutation.mutate({ full_name: fullName, timezone });
  };

  if (!user) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription>Your name and timezone, used across LinkSavvy.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <p role="alert" className="rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
            {error}
          </p>
        )}
        <Input label="Email" value={user.email} disabled readOnly />
        <Input
          label="Full name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          disabled={mutation.isPending}
        />
        <Select
          label="Timezone"
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          disabled={mutation.isPending}
        >
          {COMMON_TIMEZONES.map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </Select>
        <div>
          <Button type="submit" loading={mutation.isPending}>
            Save changes
          </Button>
        </div>
      </form>
    </Card>
  );
}
