import { useState } from "react";
import type { LinkedInStartResponse } from "@/contracts";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/toast-context";

export function LinkedInButton({ label }: { label: string }) {
  const [loading, setLoading] = useState(false);
  const { push } = useToast();

  const handleClick = async () => {
    setLoading(true);
    try {
      const { authorization_url } = await apiFetch<LinkedInStartResponse>(
        "/api/v1/auth/linkedin/start",
        { skipAuth: true },
      );
      window.location.href = authorization_url;
    } catch {
      push({
        variant: "danger",
        title: "LinkedIn sign-in is unavailable",
        description: "Please use email and password, or try again shortly.",
      });
      setLoading(false);
    }
  };

  return (
    <Button
      type="button"
      variant="secondary"
      className="w-full"
      loading={loading}
      onClick={handleClick}
    >
      {label}
    </Button>
  );
}
