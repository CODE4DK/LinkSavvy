import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import type {
  PlaygroundPromptSummary,
  PlaygroundRunResponse,
  PlaygroundStreamFrame,
} from "@linksavvy/contracts";
import { useAuth } from "@/lib/auth-context";
import { apiFetch, streamSSE, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";

const TIERS = ["fast", "standard", "advanced"] as const;

interface RunResult {
  parsed: unknown;
  raw: string | null;
  tokensIn: number;
  tokensOut: number;
  costMinor: number;
  currency: string;
  latencyMs: number;
  cached: boolean;
  fallbackUsed: boolean;
}

function fromRunResponse(response: PlaygroundRunResponse): RunResult {
  return {
    parsed: response.parsed ?? null,
    raw: response.text,
    tokensIn: response.tokens_in,
    tokensOut: response.tokens_out,
    costMinor: response.cost_minor,
    currency: response.currency,
    latencyMs: response.latency_ms,
    cached: response.cached,
    fallbackUsed: response.fallback_used,
  };
}

export function PlaygroundPage() {
  const { user, featureFlags } = useAuth();
  const [prompts, setPrompts] = useState<PlaygroundPromptSummary[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tier, setTier] = useState<string>("");
  const [contextValues, setContextValues] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [result, setResult] = useState<RunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const canAccess = user?.role === "admin" && featureFlags["dev.playground"] === true;

  useEffect(() => {
    if (!canAccess) return;
    apiFetch<PlaygroundPromptSummary[]>("/internal/playground/prompts")
      .then(setPrompts)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Failed to load prompts."));
  }, [canAccess]);

  const selected = useMemo(
    () => prompts?.find((p) => p.id === selectedId) ?? null,
    [prompts, selectedId],
  );

  function selectPrompt(prompt: PlaygroundPromptSummary) {
    setSelectedId(prompt.id);
    setTier(prompt.tier);
    setContextValues(Object.fromEntries(prompt.required_context.map((key) => [key, ""])));
    setResult(null);
    setStreamedText("");
    setRunError(null);
  }

  async function handleRun() {
    if (!selected) return;
    setRunning(true);
    setRunError(null);
    setResult(null);
    try {
      const response = await apiFetch<PlaygroundRunResponse>("/internal/playground/run", {
        method: "POST",
        body: {
          prompt_id: selected.id,
          context: contextValues,
          tier_override: tier || null,
        },
      });
      setResult(fromRunResponse(response));
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "The run failed.");
    } finally {
      setRunning(false);
    }
  }

  async function handleStream() {
    if (!selected) return;
    setStreaming(true);
    setRunError(null);
    setResult(null);
    setStreamedText("");
    const controller = new AbortController();
    abortRef.current = controller;
    let tokensIn = 0;
    let tokensOut = 0;
    let costMinor = 0;
    let latencyMs = 0;
    let fallbackUsed = false;
    let cached = false;
    try {
      await streamSSE<PlaygroundStreamFrame>(
        "/internal/playground/stream",
        { prompt_id: selected.id, context: contextValues, tier_override: tier || null },
        (frame) => {
          if (frame.type === "meta") {
            cached = frame.cached;
          } else if (frame.type === "delta") {
            setStreamedText((prev) => prev + frame.text);
          } else if (frame.type === "error") {
            setRunError(frame.message);
          } else if (frame.type === "done") {
            tokensIn = frame.tokens_in;
            tokensOut = frame.tokens_out;
            costMinor = frame.cost_minor;
            latencyMs = frame.latency_ms ?? 0;
            fallbackUsed = frame.fallback_used ?? false;
          }
        },
        { signal: controller.signal },
      );
      setResult({
        parsed: null,
        raw: null,
        tokensIn,
        tokensOut,
        costMinor,
        currency: "USD",
        latencyMs,
        cached,
        fallbackUsed,
      });
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setRunError(err instanceof ApiError ? err.message : "The stream failed.");
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }

  function handleCancelStream() {
    abortRef.current?.abort();
  }

  if (!canAccess) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
      <div className="flex flex-col gap-3">
        <h1 className="text-xl font-semibold text-fg">AI Playground</h1>
        <p className="text-sm text-fg-muted">
          Run or stream any registered prompt directly through the gateway.
        </p>
        {loadError && <p className="text-sm text-danger">{loadError}</p>}
        {!prompts && !loadError && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        <div className="flex flex-col gap-2">
          {prompts?.map((prompt) => (
            <button
              key={prompt.id}
              type="button"
              onClick={() => selectPrompt(prompt)}
              className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                selectedId === prompt.id
                  ? "border-primary bg-primary/5 text-fg"
                  : "border-border bg-bg text-fg-muted hover:bg-bg-subtle"
              }`}
            >
              <div className="font-medium text-fg">{prompt.id}</div>
              <div className="text-xs">v{prompt.version} · {prompt.tier}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-6">
        {!selected && (
          <Card>
            <CardDescription>Select a prompt on the left to get started.</CardDescription>
          </Card>
        )}

        {selected && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>{selected.id}</CardTitle>
                <CardDescription>{selected.description}</CardDescription>
              </CardHeader>
              <div className="flex flex-wrap gap-2 text-xs text-fg-muted">
                <Badge>max tokens: {selected.max_output_tokens}</Badge>
                <Badge>temperature: {selected.temperature}</Badge>
                <Badge>cache ttl: {selected.cache_ttl_seconds}s</Badge>
                <Badge variant={selected.output_schema ? "primary" : "default"}>
                  {selected.output_schema ? "schema output" : "text output"}
                </Badge>
              </div>
              {selected.output_schema && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-sm text-fg-muted">Output schema</summary>
                  <pre className="mt-2 overflow-x-auto rounded-md bg-bg-subtle p-3 text-xs">
                    {JSON.stringify(selected.output_schema, null, 2)}
                  </pre>
                </details>
              )}
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Input</CardTitle>
              </CardHeader>
              <div className="flex flex-col gap-4">
                <Select
                  label="Tier override"
                  value={tier}
                  onChange={(e) => setTier(e.target.value)}
                >
                  {TIERS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                      {t === selected.tier ? " (default)" : ""}
                    </option>
                  ))}
                </Select>
                {selected.required_context.map((key) => (
                  <div key={key} className="flex flex-col gap-1.5">
                    <label htmlFor={`ctx-${key}`} className="text-sm font-medium text-fg">
                      {key}
                    </label>
                    <textarea
                      id={`ctx-${key}`}
                      rows={3}
                      value={contextValues[key] ?? ""}
                      onChange={(e) =>
                        setContextValues((prev) => ({ ...prev, [key]: e.target.value }))
                      }
                      className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg"
                    />
                  </div>
                ))}
                <div className="flex gap-2">
                  <Button onClick={handleRun} loading={running} disabled={streaming}>
                    Run
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={handleStream}
                    loading={streaming}
                    disabled={running}
                  >
                    Stream
                  </Button>
                  {streaming && (
                    <Button variant="ghost" onClick={handleCancelStream}>
                      Cancel
                    </Button>
                  )}
                </div>
                {runError && (
                  <p role="alert" className="text-sm text-danger">
                    {runError}
                  </p>
                )}
              </div>
            </Card>

            {(result || streamedText || streaming) && (
              <Card>
                <CardHeader>
                  <CardTitle>Result</CardTitle>
                </CardHeader>
                <div className="flex flex-col gap-4">
                  {streamedText && (
                    <div>
                      <p className="mb-1 text-sm font-medium text-fg">Streamed text</p>
                      <pre className="whitespace-pre-wrap rounded-md bg-bg-subtle p-3 text-sm">
                        {streamedText}
                      </pre>
                    </div>
                  )}
                  {result && (
                    <>
                      <div className="flex flex-wrap gap-2 text-xs">
                        <Badge variant={result.cached ? "success" : "default"}>
                          {result.cached ? "cache hit" : "cache miss"}
                        </Badge>
                        <Badge variant={result.fallbackUsed ? "warning" : "default"}>
                          {result.fallbackUsed ? "fallback used" : "primary provider"}
                        </Badge>
                        <Badge>tokens in: {result.tokensIn}</Badge>
                        <Badge>tokens out: {result.tokensOut}</Badge>
                        <Badge>
                          cost: {(result.costMinor / 100).toFixed(4)} {result.currency}
                        </Badge>
                        <Badge>latency: {Math.round(result.latencyMs)}ms</Badge>
                      </div>
                      {result.parsed != null && (
                        <div>
                          <p className="mb-1 text-sm font-medium text-fg">Parsed output</p>
                          <pre className="overflow-x-auto rounded-md bg-bg-subtle p-3 text-xs">
                            {JSON.stringify(result.parsed, null, 2)}
                          </pre>
                        </div>
                      )}
                      {result.raw != null && (
                        <div>
                          <p className="mb-1 text-sm font-medium text-fg">Raw output</p>
                          <pre className="whitespace-pre-wrap rounded-md bg-bg-subtle p-3 text-xs">
                            {result.raw}
                          </pre>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}
