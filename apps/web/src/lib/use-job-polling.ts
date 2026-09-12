import { useQuery } from "@tanstack/react-query";
import type { JobStatusResponse } from "@linksavvy/contracts";
import { apiFetch } from "./api";

const TERMINAL_STATUSES = new Set(["succeeded", "failed", "dead"]);
const POLL_INTERVAL_MS = 2000;

/** Polls GET /api/v1/jobs/{id} every 2s until the job reaches a terminal
 * status. Pass `null` to disable polling (no job running). */
export function useJobPolling(jobId: string | null) {
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => apiFetch<JobStatusResponse>(`/api/v1/jobs/${jobId}`),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && TERMINAL_STATUSES.has(status) ? false : POLL_INTERVAL_MS;
    },
  });
}

export function isTerminalJobStatus(status: string): boolean {
  return TERMINAL_STATUSES.has(status);
}
