import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiFetch, ApiError } from "@/lib/api";
import { AuthLayout } from "./AuthLayout";
import { Skeleton } from "@/components/ui/Skeleton";

type VerifyState = "verifying" | "success" | "error";

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [state, setState] = useState<VerifyState>("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setState("error");
      setMessage("This verification link is missing its token.");
      return;
    }
    (async () => {
      try {
        await apiFetch("/api/v1/auth/verify-email", {
          method: "POST",
          skipAuth: true,
          body: { token },
        });
        setState("success");
      } catch (error) {
        setState("error");
        setMessage(
          error instanceof ApiError ? error.message : "This link is invalid or has expired.",
        );
      }
    })();
  }, [token]);

  return (
    <AuthLayout title="Email verification">
      {state === "verifying" && (
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}
      {state === "success" && (
        <>
          <p className="text-sm text-fg-muted">
            Your email is verified. You can now log in to LinkSavvy.
          </p>
          <Link to="/login" className="mt-6 block text-center text-sm text-primary hover:underline">
            Go to log in
          </Link>
        </>
      )}
      {state === "error" && (
        <>
          <p className="text-sm text-danger">{message}</p>
          <Link to="/login" className="mt-6 block text-center text-sm text-primary hover:underline">
            Back to log in
          </Link>
        </>
      )}
    </AuthLayout>
  );
}
