import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { AuditRunResponse, DashboardRunAuditState } from "@/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { useJobPolling, isTerminalJobStatus } from "@/lib/use-job-polling";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/toast-context";

const REASON_MESSAGES: Record<string, string> = {
  no_active_snapshot: "Set up your profile before running your first audit.",
  audit_in_progress: "An audit is already running.",
  cooldown_active: "You can run another audit once the cooldown period has passed.",
  quota_exceeded: "You've used all your audits for this period.",
};

function formatRetryAfter(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.ceil((seconds % 3600) / 60);
  if (hours > 0) return `about ${hours}h ${minutes}m`;
  return `about ${minutes}m`;
}

export interface RunAuditControlProps {
  runAudit: DashboardRunAuditState;
}

/** The dashboard's run-audit button: reflects cooldown/quota/in-flight
 * state from the aggregate load, and once started, polls the job's real
 * per-category progress until it completes. */
export function RunAuditControl({ runAudit }: RunAuditControlProps) {
  const [jobId, setJobId] = useState<string | null>(runAudit.in_flight_job_id);
  const queryClient = useQueryClient();
  const toast = useToast();
  const jobQuery = useJobPolling(jobId);

  useEffect(() => {
    setJobId(runAudit.in_flight_job_id);
  }, [runAudit.in_flight_job_id]);

  useEffect(() => {
    const status = jobQuery.data?.status;
    if (!status || !isTerminalJobStatus(status)) return;
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    if (status === "succeeded") {
      toast.push({
        title: "Audit complete",
        description: "Your Health Score is up to date.",
        variant: "success",
      });
    } else {
      toast.push({
        title: "Audit didn't finish",
        description: jobQuery.data?.error ?? "Something went wrong. Please try again.",
        variant: "danger",
      });
    }
    setJobId(null);
  }, [jobQuery.data?.status, jobQuery.data?.error, queryClient, toast]);

  const startAudit = useMutation({
    mutationFn: () => apiFetch<AuditRunResponse>("/api/v1/audits", { method: "POST", body: {} }),
    onSuccess: (data) => setJobId(data.job_id),
    onError: (error) => {
      const description =
        error instanceof ApiError ? error.message : "Please try again in a moment.";
      toast.push({ title: "Couldn't start the audit", description, variant: "danger" });
    },
  });

  if (jobId !== null) {
    const progress = jobQuery.data?.progress_percent ?? 0;
    return (
      <div className="flex flex-col gap-2">
        <div className="h-2 w-48 overflow-hidden rounded-full bg-bg-subtle">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-xs text-fg-muted">Running your audit... {progress}%</span>
      </div>
    );
  }

  const blockedMessage = runAudit.reason ? REASON_MESSAGES[runAudit.reason] : null;
  const retryMessage =
    runAudit.reason === "cooldown_active" && runAudit.retry_after_seconds !== null
      ? ` Try again in ${formatRetryAfter(runAudit.retry_after_seconds)}.`
      : "";

  return (
    <div className="flex flex-col gap-1">
      <Button
        onClick={() => startAudit.mutate()}
        disabled={!runAudit.can_run}
        loading={startAudit.isPending}
      >
        Run audit
      </Button>
      {blockedMessage && (
        <span className="text-xs text-fg-muted">
          {blockedMessage}
          {retryMessage}
        </span>
      )}
      {runAudit.can_run && (
        <span className="text-xs text-fg-muted">
          {runAudit.quota_used}/{runAudit.quota_limit} audits used this period
        </span>
      )}
    </div>
  );
}
