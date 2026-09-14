import { useState, type ChangeEvent, type FormEvent } from "react";
import type { ImportResponse, ProfileSnapshot, SyncResponse } from "@/contracts";
import { profileSnapshotSchema } from "@/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import type { WizardSource } from "./wizard-state";

export interface StepImportProps {
  source: WizardSource;
  onImported: (result: { importId: string | null; draft: ProfileSnapshot; warnings: string[] }) => void;
  onBack: () => void;
}

export function StepImport({ source, onImported, onBack }: StepImportProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pasteText, setPasteText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const startLinkedIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const { authorization_url } = await apiFetch<{ authorization_url: string }>(
        "/api/v1/profile/connect",
        { method: "POST" },
      );
      window.location.href = authorization_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start LinkedIn connection.");
      setLoading(false);
    }
  };

  const submitPaste = async (event: FormEvent) => {
    event.preventDefault();
    if (!pasteText.trim()) {
      setError("Paste your profile text first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<ImportResponse>("/api/v1/profile/imports", {
        method: "POST",
        body: { text: pasteText },
      });
      if (!response.draft) throw new Error("No draft returned");
      onImported({
        importId: response.import_id,
        draft: profileSnapshotSchema.parse(response.draft),
        warnings: response.parse_warnings,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not parse that text.");
    } finally {
      setLoading(false);
    }
  };

  const submitUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF or DOCX file first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await apiFetch<ImportResponse>("/api/v1/profile/imports/upload", {
        method: "POST",
        body: formData,
      });
      if (!response.draft) throw new Error("No draft returned");
      onImported({
        importId: response.import_id,
        draft: profileSnapshotSchema.parse(response.draft),
        warnings: response.parse_warnings,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not read that file.");
    } finally {
      setLoading(false);
    }
  };

  const startManual = () => {
    onImported({
      importId: null,
      draft: profileSnapshotSchema.parse({
        source: "manual",
        captured_at: new Date().toISOString(),
      }),
      warnings: [],
    });
  };

  const startSync = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<SyncResponse>("/api/v1/profile/sync", { method: "POST" });
      onImported({
        importId: null,
        draft: profileSnapshotSchema.parse(response.draft),
        warnings: [],
      });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not sync from LinkedIn. Try connecting again.",
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <p className="text-sm text-fg-muted">
          {source === "linkedin_api" ? "Talking to LinkedIn…" : "Reading your profile…"}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl">
      <button type="button" onClick={onBack} className="mb-4 text-sm text-fg-muted hover:text-fg">
        ← Back
      </button>

      {error && (
        <p role="alert" className="mb-4 rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}

      {source === "linkedin_api" && (
        <div className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold text-fg">Connect LinkedIn</h2>
          <p className="text-sm text-fg-muted">
            You&apos;ll be sent to LinkedIn to approve access, then back here to review what we
            got.
          </p>
          <div className="flex gap-2">
            <Button onClick={startLinkedIn}>Connect LinkedIn</Button>
            <Button variant="secondary" onClick={startSync}>
              Already connected? Sync now
            </Button>
          </div>
        </div>
      )}

      {source === "paste" && (
        <form onSubmit={submitPaste} className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold text-fg">Paste your profile</h2>
          <textarea
            value={pasteText}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setPasteText(e.target.value)}
            rows={14}
            placeholder="Paste your profile text here…"
            className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg placeholder:text-fg-muted"
          />
          <div>
            <Button type="submit">Parse this text</Button>
          </div>
        </form>
      )}

      {source === "upload" && (
        <form onSubmit={submitUpload} className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold text-fg">Upload a resume</h2>
          <input
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={(e: ChangeEvent<HTMLInputElement>) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm text-fg"
          />
          <div>
            <Button type="submit">Upload and parse</Button>
          </div>
        </form>
      )}

      {source === "manual" && (
        <div className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold text-fg">Enter your profile yourself</h2>
          <p className="text-sm text-fg-muted">
            You&apos;ll fill in a short guided form on the next step, at your own pace.
          </p>
          <div>
            <Button onClick={startManual}>Start</Button>
          </div>
        </div>
      )}

      {loading && <Skeleton className="h-4 w-full" />}
    </div>
  );
}
