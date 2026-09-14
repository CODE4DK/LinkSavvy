import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import type { ExportJobResponse } from "@linksavvy/contracts";
import { apiFetch, ApiError, getAccessToken } from "@/lib/api";
import { useJobPolling, isTerminalJobStatus } from "@/lib/use-job-polling";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/toast-context";

async function downloadExport(exportId: string) {
  const token = getAccessToken();
  const response = await fetch(`/api/v1/me/export/${exportId}`, {
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) throw new Error("Download failed");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "linksavvy-export.zip";
  link.click();
  URL.revokeObjectURL(url);
}

/** "Request my data" (see docs/privacy.md) -- kicks off the /me/export
 * job, polls it with the same job-polling hook the dashboard's audit
 * button uses, and downloads the ZIP client-side once it's ready (the
 * download endpoint needs a bearer token, so a plain <a href> can't
 * authenticate it -- see CareerHubPage's resume export for the same
 * pattern). */
export function PrivacySection() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const toast = useToast();
  const jobQuery = useJobPolling(jobId);

  useEffect(() => {
    const status = jobQuery.data?.status;
    if (!status || !isTerminalJobStatus(status)) return;
    if (status === "succeeded") {
      const exportId = jobQuery.data?.result?.export_id;
      if (typeof exportId === "string") {
        setDownloading(true);
        downloadExport(exportId)
          .catch(() =>
            toast.push({
              title: "Download failed",
              description: "Please try again from the notification once it arrives.",
              variant: "danger",
            }),
          )
          .finally(() => setDownloading(false));
      }
    } else {
      toast.push({
        title: "Export didn't finish",
        description: jobQuery.data?.error ?? "Something went wrong. Please try again.",
        variant: "danger",
      });
    }
    setJobId(null);
  }, [jobQuery.data?.status, jobQuery.data?.error, jobQuery.data?.result, toast]);

  const requestExport = useMutation({
    mutationFn: () =>
      apiFetch<ExportJobResponse>("/api/v1/me/export", { method: "POST", body: {} }),
    onSuccess: (data) => setJobId(data.job_id),
    onError: (error) => {
      const description =
        error instanceof ApiError ? error.message : "Please try again in a moment.";
      toast.push({ title: "Couldn't start the export", description, variant: "danger" });
    },
  });

  const busy = requestExport.isPending || jobId !== null || downloading;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your data</CardTitle>
        <CardDescription>
          Download a copy of everything LinkSavvy has stored for you -- your profile, content,
          audits, and account settings -- as a ZIP file. The download link expires after 7 days.
        </CardDescription>
      </CardHeader>
      <div className="flex flex-col gap-2">
        <Button onClick={() => requestExport.mutate()} disabled={busy} loading={busy}>
          Request my data
        </Button>
        {jobId !== null && (
          <span className="text-xs text-fg-muted">Preparing your export...</span>
        )}
      </div>
    </Card>
  );
}
