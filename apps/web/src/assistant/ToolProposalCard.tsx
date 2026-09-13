/**
 * Renders one assistant tool proposal as an editable card: the model's
 * reasoning, an input form built from the tool's own JSON Schema
 * (reusing ToolRunnerForm -- no proposal-specific form logic), and a Run
 * button. Nothing runs until the user clicks it; on confirmation this
 * calls the same confirm-tool endpoint, then shows the result with
 * ToolRunner's own ResultView and the same Save/Copy actions a hub page
 * gets -- reused, never duplicated.
 */

import { useEffect, useState } from "react";
import type { ToolRunSummary, ToolSummary } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ToolRunnerForm } from "@/tools/ToolRunnerForm";
import { ResultView, extractSaveableText } from "@/tools/renderers";
import { useProfileSnapshot } from "@/tools/useProfileSnapshot";
import {
  buildSubmissionPayload,
  defaultValueFor,
  fieldsForSchema,
  profileDefaultFor,
  zodSchemaForTool,
} from "@/tools/schema-form";
import { confirmTool } from "./api";

export interface ToolProposalCardProps {
  conversationId: string;
  proposingMessageId: string;
  toolId: string;
  reasoning: string;
  prefilledInput: Record<string, unknown>;
}

export function ToolProposalCard({
  conversationId,
  proposingMessageId,
  toolId,
  reasoning,
  prefilledInput,
}: ToolProposalCardProps) {
  const { push: pushToast } = useToast();
  const [tool, setTool] = useState<ToolSummary | null | "not-found">(null);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [run, setRun] = useState<ToolRunSummary | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveTitle, setSaveTitle] = useState("");
  const [saved, setSaved] = useState(false);
  const { snapshot } = useProfileSnapshot(true);

  useEffect(() => {
    apiFetch<ToolSummary[]>("/api/v1/tools").then((tools) => {
      const match = tools.find((t) => t.id === toolId) ?? "not-found";
      setTool(match);
      if (match !== "not-found") {
        const fields = fieldsForSchema(match.input_schema);
        setValues(
          Object.fromEntries(
            fields.map((field) => [
              field.key,
              prefilledInput[field.key] ??
                profileDefaultFor(field, snapshot) ??
                defaultValueFor(field),
            ]),
          ),
        );
        setSaveTitle(match.name);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toolId, snapshot]);

  if (tool === null) return <Skeleton className="h-32 w-full" />;
  if (tool === "not-found") {
    return (
      <Card className="p-3 text-sm text-fg-muted">
        This tool ({toolId}) is no longer available.
      </Card>
    );
  }

  async function handleRun() {
    if (!tool || tool === "not-found") return;
    const validation = zodSchemaForTool(tool.input_schema).safeParse(values);
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
    setRunning(true);
    try {
      const payload = buildSubmissionPayload(tool.input_schema, values);
      const toolMessage = await confirmTool(conversationId, {
        message_id: proposingMessageId,
        tool_id: tool.id,
        input: payload,
      });
      const runId = toolMessage.tool_call?.run_id;
      if (typeof runId === "string") {
        const runResponse = await apiFetch<ToolRunSummary>(`/api/v1/tools/runs/${runId}`);
        setRun(runResponse);
      }
    } catch (err) {
      pushToast({
        title: "Couldn't run this tool",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    } finally {
      setRunning(false);
    }
  }

  async function handleSave() {
    if (!run || !tool || tool === "not-found") return;
    setSaving(true);
    try {
      await apiFetch(`/api/v1/tools/runs/${run.id}/save`, {
        method: "POST",
        body: {
          title: saveTitle.trim() || tool.name,
          body: extractSaveableText(tool.result_renderer, run.output),
        },
      });
      setSaved(true);
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
    if (!run || !tool || tool === "not-found") return;
    try {
      await navigator.clipboard.writeText(extractSaveableText(tool.result_renderer, run.output));
      pushToast({ title: "Copied to clipboard", variant: "success" });
    } catch {
      pushToast({ title: "Couldn't copy to clipboard", variant: "danger" });
    }
  }

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div>
        <p className="text-sm font-medium text-fg">Suggested: {tool.name}</p>
        <p className="text-sm text-fg-muted">{reasoning}</p>
      </div>

      {!run && (
        <>
          <ToolRunnerForm
            schema={tool.input_schema}
            values={values}
            errors={errors}
            onChange={(key, value) => setValues((current) => ({ ...current, [key]: value }))}
            snapshot={snapshot}
            disabled={running}
          />
          <div>
            <Button onClick={handleRun} loading={running}>
              Run {tool.name}
            </Button>
          </div>
        </>
      )}

      {run && (
        <div className="flex flex-col gap-3 border-t border-border pt-3">
          <ResultView renderer={tool.result_renderer} output={run.output} />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={handleCopy}>
              Copy
            </Button>
            {tool.save_as && (
              <Button size="sm" variant="secondary" onClick={handleSave} loading={saving} disabled={saved}>
                {saved ? "Saved" : "Save to Workspace"}
              </Button>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
