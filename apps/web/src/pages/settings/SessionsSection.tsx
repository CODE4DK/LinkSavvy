import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { SessionOut } from "@linksavvy/contracts";
import { apiFetch } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";

export function SessionsSection() {
  const queryClient = useQueryClient();

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["auth", "sessions"],
    queryFn: () => apiFetch<SessionOut[]>("/api/v1/auth/sessions"),
  });

  const revoke = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/auth/sessions/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["auth", "sessions"] }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active sessions</CardTitle>
        <CardDescription>Devices currently signed in to your account.</CardDescription>
      </CardHeader>

      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {!isLoading && sessions?.length === 0 && (
        <p className="text-sm text-fg-muted">No active sessions found.</p>
      )}

      <ul className="flex flex-col divide-y divide-border">
        {sessions?.map((session) => (
          <li key={session.id} className="flex items-center justify-between gap-4 py-3">
            <div>
              <p className="text-sm text-fg">{session.user_agent ?? "Unknown device"}</p>
              <p className="text-xs text-fg-muted">
                Signed in {new Date(session.issued_at).toLocaleString()}
              </p>
            </div>
            {session.current ? (
              <Badge variant="primary">This device</Badge>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                loading={revoke.isPending && revoke.variables === session.id}
                onClick={() => revoke.mutate(session.id)}
              >
                Revoke
              </Button>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
