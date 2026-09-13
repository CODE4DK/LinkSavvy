/**
 * The Tool Framework's one and only frontend surface: given a tool id,
 * fetches its definition and renders a working form, run button,
 * streaming/non-streaming execution, a result view, per-result actions,
 * a "what this used" context panel, and a run history rail -- all driven
 * by the tool's own `ToolSummary` (its JSON Schemas and a handful of
 * flags). There is deliberately no `if (toolId === ...)` anywhere in this
 * file: a new tool needs a definition file and a prompt, never a change
 * here. See schema-form.ts for the input-widget conventions and
 * renderers.tsx for the six `result_renderer` views.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type {
  AssetResponse,
  QuotaInfo,
  ToolRunResponse,
  ToolRunStreamFrame,
  ToolRunSummary,
  ToolSummary,
} from "@linksavvy/contracts";
import { apiFetch, streamSSE, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ToolRunnerForm } from "./ToolRunnerForm";
import { ResultView, extractSaveableText } from "./renderers";
import { useProfileSnapshot } from "./useProfileSnapshot";
import {
  buildSubmissionPayload,
  defaultValueFor,
  fieldsForSchema,
  profileDefaultFor,
  usesProfileData,
  zodSchemaForTool,
  type JsonSchemaObject,
} from "./schema-form";

const PLAN_RANK: Record<string, number> = { free: 0, pro: 1 };

function isIdeaRows(output: unknown): boolean {
  if (typeof output !== "object" || output === null) return false;
  const rows = (output as { rows?: unknown }).rows;
  return (
    Array.isArray(rows) &&
    rows.length > 0 &&
    rows.every(
      (row) =>
        typeof row === "object" &&
        row !== null &&
        typeof (row as { title?: unknown }).title === "string",
    )
  );
}

function ideaRowsOf(output: unknown): Record<string, unknown>[] {
  return (output as { rows: Record<string, unknown>[] }).rows ?? [];
}

function lastUsedKey(toolId: string): string {
  return `linksavvy:tool-runner:last-input:${toolId}`;
}

function loadLastUsed(toolId: string): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(lastUsedKey(toolId));
    return raw ? (JSON.parse(raw) as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function saveLastUsed(toolId: string, values: Record<string, unknown>): void {
  try {
    localStorage.setItem(lastUsedKey(toolId), JSON.stringify(values));
  } catch {
    // Best-effort convenience only -- a private-browsing quota error
    // here shouldn't stop the run itself.
  }
}

type LoadState =
  | { status: "loading" }
  | { status: "not-found" }
  | { status: "error"; message: string }
  | { status: "ready"; tool: ToolSummary };

export interface ToolRunnerProps {
  toolId: string;
  /** Optional prefill for the input form -- e.g. a Dashboard
   * recommendation's suggested starting point. Applied once on load,
   * ahead of profile defaults and remembered last-used values. */
  initialValues?: Record<string, unknown>;
  /** When provided, and the current tool's `save_as` is one this
   * callback wants (a hub page's own choice -- the framework doesn't
   * know or care which asset types that is), a result gets an "Apply to
   * profile" action alongside Copy/Edit/Regenerate/Rate/Save: one button
   * for a single-block result, or a per-variant button when the result
   * renderer is `variants`, since only the user can pick which variant
   * to accept. */
  onApplyToProfile?: (params: { assetType: string; text: string }) => void;
  /** When provided, a result gets a "Send to Composer" action -- Content
   * Hub's equivalent of `onApplyToProfile`, handing the extracted text
   * (the same text Save to Workspace would save) to the caller rather
   * than patching a `ProfileSnapshot` field. */
  onSendToComposer?: (text: string) => void;
  /** When provided, and the current tool's `save_as` is `carousel`, a
   * result gets an "Open in Carousel Builder" action handing the raw
   * parsed output (already shaped like `CarouselData` minus `template`)
   * to the caller, rather than the generic Save to Workspace's plain
   * text -- the builder needs the real structure, not a flattened
   * string. */
  onSendToCarouselBuilder?: (output: unknown) => void;
  /** When provided, and the result is a `table` of rows that each carry
   * a `title` (the shape `content.ideas_generator` and any future
   * ideas-shaped tool produces), a result gets a "Send ideas to
   * calendar" action handing every row to the caller at once, so ideas
   * can go straight onto the calendar without a manual copy per idea. */
  onSendIdeasToCalendar?: (rows: Record<string, unknown>[]) => void;
}

export function ToolRunner({
  toolId,
  initialValues,
  onApplyToProfile,
  onSendToComposer,
  onSendToCarouselBuilder,
  onSendIdeasToCalendar,
}: ToolRunnerProps) {
  const { user } = useAuth();
  const { push: pushToast } = useToast();
  const [searchParams] = useSearchParams();
  const reproduceRunId = searchParams.get("run_id");
  const [reproducedInput, setReproducedInput] = useState<Record<string, unknown> | null>(null);

  const [load, setLoad] = useState<LoadState>({ status: "loading" });
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [runError, setRunError] = useState<string | null>(null);

  const [runId, setRunId] = useState<string | null>(null);
  const [output, setOutput] = useState<unknown>(null);
  const [contextUsed, setContextUsed] = useState<string[]>([]);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [reviewConfirmed, setReviewConfirmed] = useState(false);

  const [rating, setRating] = useState<"up" | "down" | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [ratingSaved, setRatingSaved] = useState(false);

  const [nudge, setNudge] = useState("");
  const [editing, setEditing] = useState(false);
  const [editedText, setEditedText] = useState("");
  const [saveTitle, setSaveTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAsset, setSavedAsset] = useState<AssetResponse | null>(null);

  const [history, setHistory] = useState<ToolRunSummary[] | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const tool = load.status === "ready" ? load.tool : null;
  const schema = tool?.input_schema as JsonSchemaObject | undefined;
  const needsProfile = schema ? usesProfileData(schema) : false;
  const { snapshot } = useProfileSnapshot(needsProfile);

  const minPlanMet = tool
    ? (PLAN_RANK[user?.plan ?? "free"] ?? 0) >= (PLAN_RANK[tool.min_plan] ?? 0)
    : true;

  useEffect(() => {
    let cancelled = false;
    setLoad({ status: "loading" });
    apiFetch<ToolSummary[]>("/api/v1/tools")
      .then((tools) => {
        if (cancelled) return;
        const found = tools.find((candidate) => candidate.id === toolId);
        setLoad(found ? { status: "ready", tool: found } : { status: "not-found" });
      })
      .catch((err) => {
        if (cancelled) return;
        setLoad({
          status: "error",
          message: err instanceof ApiError ? err.message : "Failed to load this tool.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [toolId]);

  // `?run_id=` on the URL (the Workspace Hub's "open in tool" link on a
  // saved asset) means reproduce that exact run's inputs -- fetched
  // once and folded into the seeding effect below ahead of every other
  // prefill source, since "open in tool" promises the *same* inputs,
  // not just a reasonable starting point.
  useEffect(() => {
    if (!reproduceRunId) {
      setReproducedInput(null);
      return;
    }
    let cancelled = false;
    apiFetch<ToolRunSummary>(`/api/v1/tools/runs/${reproduceRunId}`)
      .then((run) => {
        if (!cancelled) setReproducedInput(run.input);
      })
      .catch(() => {
        if (!cancelled) setReproducedInput(null);
      });
    return () => {
      cancelled = true;
    };
  }, [reproduceRunId]);

  // Seeds the form once the definition (and, if the tool needs it, the
  // profile snapshot) are ready. Precedence: a reproduced run's own
  // inputs win outright, then an explicit prefill, then a remembered
  // last-used value, then a profile-backed default, then the field's
  // own schema default.
  useEffect(() => {
    if (!schema) return;
    const remembered = loadLastUsed(toolId) ?? {};
    const seeded: Record<string, unknown> = {};
    for (const field of fieldsForSchema(schema)) {
      if (reproducedInput && field.key in reproducedInput) {
        seeded[field.key] = reproducedInput[field.key];
      } else if (initialValues && field.key in initialValues) {
        seeded[field.key] = initialValues[field.key];
      } else if (field.key in remembered) {
        seeded[field.key] = remembered[field.key];
      } else {
        seeded[field.key] = profileDefaultFor(field, snapshot) ?? defaultValueFor(field);
      }
    }
    setValues(seeded);
  }, [schema, snapshot, toolId, initialValues, reproducedInput]);

  function resetResultState() {
    setRating(null);
    setFeedbackText("");
    setRatingSaved(false);
    setNudge("");
    setEditing(false);
    setEditedText("");
    setSaveTitle("");
    setSavedAsset(null);
    setReviewConfirmed(false);
  }

  function applyRunResult(
    newRunId: string,
    newOutput: unknown,
    newContextUsed: string[],
    newQuota: QuotaInfo,
    newWarning?: string | null,
  ) {
    setRunId(newRunId);
    setOutput(newOutput);
    setContextUsed(newContextUsed);
    setQuota(newQuota);
    setWarning(newWarning ?? null);
    resetResultState();
    setHistory(null); // stale until the rail is reopened
  }

  async function performRun(input: Record<string, unknown>) {
    const response = await apiFetch<ToolRunResponse>(`/api/v1/tools/${toolId}/run`, {
      method: "POST",
      body: { input },
    });
    applyRunResult(
      response.run_id,
      response.output,
      response.context_used,
      response.quota,
      response.warning,
    );
  }

  async function performStreamingRun(input: Record<string, unknown>) {
    const controller = new AbortController();
    abortRef.current = controller;
    let buffer = "";
    setStreamedText("");
    await streamSSE<ToolRunStreamFrame>(
      `/api/v1/tools/${toolId}/run?stream=true`,
      { input },
      (frame) => {
        if (frame.type === "delta") {
          buffer += frame.text;
          setStreamedText(buffer);
        } else if (frame.type === "error") {
          setRunError(frame.message);
        } else if (frame.type === "tool_run") {
          let parsed: unknown = null;
          try {
            parsed = JSON.parse(buffer);
          } catch {
            parsed = null;
          }
          applyRunResult(frame.run_id, parsed, frame.context_used, frame.quota, frame.warning);
        }
      },
      { signal: controller.signal },
    );
  }

  async function handleRun() {
    if (!tool || !schema || !minPlanMet || running || streaming) return;

    const validation = zodSchemaForTool(schema).safeParse(values);
    if (!validation.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of validation.error.issues) {
        const key = String(issue.path[0] ?? "");
        if (key && !fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    setRunError(null);
    setRunning(true);
    saveLastUsed(toolId, values);

    try {
      const payload = buildSubmissionPayload(schema, values);
      if (tool.supports_streaming) {
        setStreaming(true);
        await performStreamingRun(payload);
      } else {
        await performRun(payload);
      }
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setRunError(err instanceof ApiError ? err.message : "The run failed.");
      }
    } finally {
      setRunning(false);
      setStreaming(false);
      abortRef.current = null;
    }
  }

  function handleCancel() {
    abortRef.current?.abort();
  }

  async function handleRegenerate() {
    if (!runId || running || streaming) return;
    setRunning(true);
    setRunError(null);
    try {
      const response = await apiFetch<ToolRunResponse>(`/api/v1/tools/runs/${runId}/regenerate`, {
        method: "POST",
        body: { nudge: nudge.trim() || null },
      });
      applyRunResult(
        response.run_id,
        response.output,
        response.context_used,
        response.quota,
        response.warning,
      );
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "Regeneration failed.");
    } finally {
      setRunning(false);
    }
  }

  async function handleRate(nextRating: "up" | "down") {
    if (!runId) return;
    setRating(nextRating);
    try {
      await apiFetch(`/api/v1/tools/runs/${runId}/rate`, {
        method: "POST",
        body: { rating: nextRating, feedback_text: feedbackText.trim() || null },
      });
      setRatingSaved(true);
    } catch (err) {
      pushToast({
        title: "Couldn't save your rating",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  }

  async function handleSave() {
    if (!runId || !tool || tool.save_as === null) return;
    setSaving(true);
    try {
      const body = editing ? editedText : extractSaveableText(tool.result_renderer, output);
      const asset = await apiFetch<AssetResponse>(`/api/v1/tools/runs/${runId}/save`, {
        method: "POST",
        body: { title: saveTitle.trim() || tool.name, body },
      });
      setSavedAsset(asset);
      pushToast({ title: "Saved to Workspace", variant: "success" });
    } catch (err) {
      pushToast({
        title: "Couldn't save this result",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleCopy() {
    if (!tool) return;
    if (tool.counts_as_outreach && !reviewConfirmed) return;
    const text = editing ? editedText : extractSaveableText(tool.result_renderer, output);
    try {
      await navigator.clipboard.writeText(text);
      pushToast({ title: "Copied to clipboard", variant: "success" });
    } catch {
      pushToast({ title: "Couldn't copy to clipboard", variant: "danger" });
    }
  }

  function startEditing() {
    if (!tool) return;
    setEditedText(extractSaveableText(tool.result_renderer, output));
    setEditing(true);
  }

  async function loadHistory() {
    setHistoryOpen((open) => !open);
    if (history !== null) return;
    try {
      const rows = await apiFetch<ToolRunSummary[]>(`/api/v1/tools/${toolId}/runs`);
      setHistory(rows);
    } catch {
      setHistory([]);
    }
  }

  function loadFromHistory(run: ToolRunSummary) {
    setRunId(run.id);
    setOutput(run.output);
    setContextUsed(run.context_used);
    setQuota(null);
    setWarning(null);
    resetResultState();
    setRating((run.rating as "up" | "down" | null) ?? null);
    setFeedbackText(run.feedback_text ?? "");
  }

  const quotaSummary = useMemo(() => {
    if (quota) return `${quota.used} / ${quota.limit} ${quota.metric} used`;
    if (tool) return `Uses 1 ${tool.quota_metric} run`;
    return null;
  }, [quota, tool]);

  if (load.status === "loading") {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (load.status === "not-found") {
    return (
      <EmptyState
        title="Tool not found"
        description="This tool doesn't exist, or isn't available to your account."
      />
    );
  }

  if (load.status === "error") {
    return <p className="text-sm text-danger">{load.message}</p>;
  }

  if (!tool || !schema) {
    // Unreachable -- load.status === "ready" (the only remaining case)
    // always carries a tool, whose input_schema is always an object.
    // The check exists purely so TypeScript narrows both below.
    return null;
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      <div className="flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{tool.name}</CardTitle>
            <CardDescription>{tool.short_description}</CardDescription>
          </CardHeader>

          {schema && (
            <ToolRunnerForm
              schema={schema}
              values={values}
              errors={errors}
              onChange={(key, value) => setValues((prev) => ({ ...prev, [key]: value }))}
              snapshot={snapshot}
              disabled={running || streaming}
            />
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button onClick={handleRun} loading={running && !streaming} disabled={!minPlanMet}>
              Run
            </Button>
            {streaming && (
              <Button variant="ghost" onClick={handleCancel}>
                Cancel
              </Button>
            )}
            {quotaSummary && <Badge>{quotaSummary}</Badge>}
          </div>

          {!minPlanMet && (
            <p className="mt-2 text-sm text-warning">
              {tool.name} requires the {tool.min_plan} plan.{" "}
              <a href="/settings" className="underline">
                Upgrade
              </a>{" "}
              to use it.
            </p>
          )}
          {runError && (
            <p role="alert" className="mt-2 text-sm text-danger">
              {runError}
            </p>
          )}
        </Card>

        {(streaming || streamedText || output !== null) && (
          <Card>
            <CardHeader>
              <CardTitle>Result</CardTitle>
            </CardHeader>

            {streaming && output === null && (
              <pre className="whitespace-pre-wrap rounded-md bg-bg-subtle p-3 text-sm text-fg">
                {streamedText || "…"}
              </pre>
            )}

            {output !== null && !editing && (
              <ResultView
                renderer={tool.result_renderer}
                output={output}
                onPickVariant={
                  onApplyToProfile && tool.save_as
                    ? (text) => onApplyToProfile({ assetType: tool.save_as as string, text })
                    : undefined
                }
              />
            )}

            {editing && (
              <textarea
                rows={8}
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg"
              />
            )}

            {warning && (
              <p className="mt-3 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
                {warning}
              </p>
            )}

            {output !== null && tool.counts_as_outreach && (
              <label className="mt-3 flex items-start gap-2 text-sm text-fg-muted">
                <input
                  type="checkbox"
                  checked={reviewConfirmed}
                  onChange={(e) => setReviewConfirmed(e.target.checked)}
                  className="mt-0.5"
                />
                I&apos;ve reviewed this message and will personalise it further.
              </label>
            )}

            {output !== null && (
              <div className="mt-4 flex flex-col gap-3 border-t border-border pt-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleCopy}
                    disabled={tool.counts_as_outreach && !reviewConfirmed}
                  >
                    Copy
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={editing ? () => setEditing(false) : startEditing}
                  >
                    {editing ? "Stop editing" : "Edit"}
                  </Button>
                  <Button
                    variant={rating === "up" ? "primary" : "secondary"}
                    size="sm"
                    onClick={() => handleRate("up")}
                    aria-pressed={rating === "up"}
                  >
                    👍
                  </Button>
                  <Button
                    variant={rating === "down" ? "primary" : "secondary"}
                    size="sm"
                    onClick={() => handleRate("down")}
                    aria-pressed={rating === "down"}
                  >
                    👎
                  </Button>
                  {ratingSaved && (
                    <span className="text-xs text-fg-muted">Thanks for the feedback</span>
                  )}
                </div>

                {rating && (
                  <input
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    onBlur={() => runId && handleRate(rating)}
                    placeholder="Add a comment (optional)"
                    className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
                  />
                )}

                <div className="flex flex-wrap items-center gap-2">
                  <input
                    value={nudge}
                    onChange={(e) => setNudge(e.target.value)}
                    placeholder="Nudge for regeneration, e.g. 'make it shorter'"
                    className="h-9 w-64 rounded-md border border-border bg-bg px-3 text-sm text-fg"
                  />
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleRegenerate}
                    loading={running}
                    disabled={streaming}
                  >
                    Regenerate
                  </Button>
                </div>

                {tool.save_as !== null && (
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      value={saveTitle}
                      onChange={(e) => setSaveTitle(e.target.value)}
                      placeholder={tool.name}
                      className="h-9 w-64 rounded-md border border-border bg-bg px-3 text-sm text-fg"
                    />
                    <Button variant="secondary" size="sm" onClick={handleSave} loading={saving}>
                      Save to Workspace
                    </Button>
                    {savedAsset && <Badge variant="success">Saved</Badge>}
                  </div>
                )}

                {onApplyToProfile && tool.save_as && tool.result_renderer !== "variants" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() =>
                      onApplyToProfile({
                        assetType: tool.save_as as string,
                        text: editing
                          ? editedText
                          : extractSaveableText(tool.result_renderer, output),
                      })
                    }
                  >
                    Apply to profile
                  </Button>
                )}

                {onSendToComposer && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() =>
                      onSendToComposer(
                        editing ? editedText : extractSaveableText(tool.result_renderer, output),
                      )
                    }
                  >
                    Send to Composer
                  </Button>
                )}

                {onSendToCarouselBuilder && tool.save_as === "carousel" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onSendToCarouselBuilder(output)}
                  >
                    Open in Carousel Builder
                  </Button>
                )}

                {onSendIdeasToCalendar &&
                  tool.result_renderer === "table" &&
                  isIdeaRows(output) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onSendIdeasToCalendar(ideaRowsOf(output))}
                    >
                      Send ideas to calendar
                    </Button>
                  )}

                {contextUsed.length > 0 && (
                  <details className="text-sm">
                    <summary className="cursor-pointer text-fg-muted">What this used</summary>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {contextUsed.map((key) => (
                        <Badge key={key}>{key}</Badge>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}
          </Card>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <Button variant="secondary" onClick={loadHistory}>
          {historyOpen ? "Hide history" : "Show history"}
        </Button>
        {historyOpen && (
          <div className="flex flex-col gap-2">
            {history === null && <Skeleton className="h-16 w-full" />}
            {history?.length === 0 && <p className="text-sm text-fg-muted">No runs yet.</p>}
            {history?.map((run) => (
              <button
                key={run.id}
                type="button"
                onClick={() => loadFromHistory(run)}
                className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                  run.id === runId
                    ? "border-primary bg-primary/5 text-fg"
                    : "border-border bg-bg text-fg-muted hover:bg-bg-subtle"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span>{new Date(run.created_at).toLocaleString()}</span>
                  <Badge variant={run.status === "succeeded" ? "success" : "danger"}>
                    {run.status}
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
