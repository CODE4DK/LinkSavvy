import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import type { RecommendationResponse } from "@linksavvy/contracts";
import { apiFetch } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/toast-context";

export interface RecommendationCardProps {
  recommendation: RecommendationResponse;
}

/** One top-recommendation card: what to do, why, an estimated impact,
 * and mark-done/dismiss actions that update the dashboard in place. */
export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const updateStatus = useMutation({
    mutationFn: (status: "done" | "dismissed") =>
      apiFetch<RecommendationResponse>(`/api/v1/recommendations/${recommendation.id}`, {
        method: "PATCH",
        body: { status },
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: () => {
      toast.push({
        title: "Couldn't update that recommendation",
        description: "Please try again.",
        variant: "danger",
      });
    },
  });

  return (
    <div className="flex flex-col gap-2 rounded-md border border-border p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-fg">{recommendation.title}</h3>
        <Badge variant="primary">+{recommendation.estimated_impact_points} pts</Badge>
      </div>
      <p className="text-sm text-fg-muted">{recommendation.why}</p>
      <div className="mt-2 flex items-center gap-2">
        <Link to={recommendation.action_route}>
          <Button size="sm" variant="secondary">
            {recommendation.action_label}
          </Button>
        </Link>
        <Button
          size="sm"
          variant="ghost"
          loading={updateStatus.isPending && updateStatus.variables === "done"}
          onClick={() => updateStatus.mutate("done")}
        >
          Mark done
        </Button>
        <Button
          size="sm"
          variant="ghost"
          loading={updateStatus.isPending && updateStatus.variables === "dismissed"}
          onClick={() => updateStatus.mutate("dismissed")}
        >
          Dismiss
        </Button>
      </div>
    </div>
  );
}
