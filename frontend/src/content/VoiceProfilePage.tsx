/**
 * Voice profile capture for the Content Hub: paste or upload 5-20 of the
 * user's own past posts, separated by a line containing exactly `---`.
 * A deterministic pass measures style signals, then one AI call turns
 * those signals plus the posts into a descriptor every content tool's
 * prompt can read (`voice_profile` context key). Nothing here ever
 * touches LinkedIn -- the user brings their own text (CLAUDE.md's parity
 * path: this works identically whether or not LinkedIn is connected).
 */

import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";
import type { VoiceDescriptorResponse } from "@/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/lib/toast-context";

const MIN_SAMPLES = 5;
const MAX_SAMPLES = 20;
const SEPARATOR_HELP = "Separate each post with its own line containing exactly three dashes: ---";

type Mode = "paste" | "upload";

function splitOnSeparator(blob: string): string[] {
  return blob
    .split(/\n\s*---\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function SourceBadge({ source }: { source: VoiceDescriptorResponse["source"] }) {
  if (source === "default") return <Badge>Neutral default</Badge>;
  if (source === "derived") return <Badge variant="success">Derived from your posts</Badge>;
  return <Badge variant="primary">Supplied</Badge>;
}

function DescriptorList({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="text-sm font-medium text-fg">{label}</p>
      <ul className="mt-1 flex flex-wrap gap-1.5">
        {items.map((item) => (
          <li key={item}>
            <Badge>{item}</Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CurrentDescriptorCard({ descriptor }: { descriptor: VoiceDescriptorResponse }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle>Your current voice profile</CardTitle>
          <SourceBadge source={descriptor.source} />
        </div>
        <CardDescription>
          {descriptor.source === "default"
            ? "We don't know your voice yet -- every content tool will use this neutral, professional default until you add your own posts below."
            : `Derived from ${descriptor.sample_count} of your own posts.`}
        </CardDescription>
      </CardHeader>
      <div className="flex flex-col gap-4">
        <DescriptorList label="Tone" items={descriptor.tone_adjectives} />
        <DescriptorList label="Recurring themes" items={descriptor.recurring_themes} />
        <DescriptorList label="Signature structures" items={descriptor.signature_structures} />
        <DescriptorList label="Vocabulary preferences" items={descriptor.vocabulary_preferences} />
        <DescriptorList label="Never does" items={descriptor.never_does} />
      </div>
    </Card>
  );
}

export function VoiceProfilePage() {
  const [descriptor, setDescriptor] = useState<VoiceDescriptorResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("paste");
  const [pasteText, setPasteText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { push: pushToast } = useToast();

  const loadDescriptor = useCallback(() => {
    setLoadError(null);
    apiFetch<VoiceDescriptorResponse>("/api/v1/content/voice")
      .then(setDescriptor)
      .catch((err) => {
        setLoadError(err instanceof ApiError ? err.message : "Failed to load your voice profile.");
      });
  }, []);

  useEffect(() => {
    loadDescriptor();
  }, [loadDescriptor]);

  const pastedCount = splitOnSeparator(pasteText).length;

  const submitPaste = async (event: FormEvent) => {
    event.preventDefault();
    const texts = splitOnSeparator(pasteText);
    if (texts.length < MIN_SAMPLES || texts.length > MAX_SAMPLES) {
      setSubmitError(
        `Provide between ${MIN_SAMPLES} and ${MAX_SAMPLES} posts (found ${texts.length}).`,
      );
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await apiFetch<VoiceDescriptorResponse>("/api/v1/content/voice/samples", {
        method: "POST",
        body: { texts },
      });
      setDescriptor(result);
      setPasteText("");
      pushToast({ title: "Voice profile updated", variant: "success" });
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : "Could not derive a voice profile from that text.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const submitUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setSubmitError("Choose a PDF or DOCX file first.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await apiFetch<VoiceDescriptorResponse>(
        "/api/v1/content/voice/samples/upload",
        {
          method: "POST",
          body: formData,
        },
      );
      setDescriptor(result);
      setFile(null);
      pushToast({ title: "Voice profile updated", variant: "success" });
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Could not read that file.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <Link to="/content" className="text-sm text-fg-muted hover:text-fg">
          ← Back to Content Hub
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-fg">Voice profile</h1>
        <p className="text-sm text-fg-muted">
          Paste or upload 5-20 of your own past LinkedIn posts. We measure your style, then describe
          your voice so every content tool can sound like you -- we never invent a trait your posts
          don&apos;t actually show.
        </p>
      </div>

      {loadError && <p className="text-sm text-danger">{loadError}</p>}
      {!descriptor && !loadError && <Skeleton className="h-40 w-full" />}
      {descriptor && <CurrentDescriptorCard descriptor={descriptor} />}

      <Card>
        <CardHeader>
          <CardTitle>Add your posts</CardTitle>
          <CardDescription>{SEPARATOR_HELP}</CardDescription>
        </CardHeader>

        <div className="mb-4 flex gap-2">
          <Button
            type="button"
            variant={mode === "paste" ? "primary" : "secondary"}
            size="sm"
            onClick={() => setMode("paste")}
          >
            Paste text
          </Button>
          <Button
            type="button"
            variant={mode === "upload" ? "primary" : "secondary"}
            size="sm"
            onClick={() => setMode("upload")}
          >
            Upload a file
          </Button>
        </div>

        {submitError && (
          <p role="alert" className="mb-4 rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
            {submitError}
          </p>
        )}

        {mode === "paste" && (
          <form onSubmit={submitPaste} className="flex flex-col gap-3">
            <textarea
              value={pasteText}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setPasteText(e.target.value)}
              rows={16}
              placeholder={`First post here...\n\n---\n\nSecond post here...`}
              className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg placeholder:text-fg-muted"
            />
            <div className="flex items-center justify-between">
              <p className="text-sm text-fg-muted">
                {pastedCount} post{pastedCount === 1 ? "" : "s"} detected (need {MIN_SAMPLES}-
                {MAX_SAMPLES})
              </p>
              <Button type="submit" loading={submitting}>
                Derive my voice
              </Button>
            </div>
          </form>
        )}

        {mode === "upload" && (
          <form onSubmit={submitUpload} className="flex flex-col gap-3">
            <input
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e: ChangeEvent<HTMLInputElement>) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm text-fg"
            />
            <p className="text-sm text-fg-muted">
              Put each post on its own paragraph, with a paragraph containing exactly `---` between
              posts.
            </p>
            <div>
              <Button type="submit" loading={submitting}>
                Upload and derive my voice
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
