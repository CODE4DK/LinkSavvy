import type { ApiErrorEnvelope } from "@linksavvy/contracts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  readonly code: ApiErrorEnvelope["error"]["code"];
  readonly details: Record<string, unknown>;
  readonly status: number;

  constructor(status: number, envelope: ApiErrorEnvelope["error"]) {
    super(envelope.message);
    this.name = "ApiError";
    this.status = status;
    this.code = envelope.code;
    this.details = envelope.details;
  }
}

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE" | "PATCH" | "PUT";
  body?: unknown;
  /** Skip attaching the Authorization header (used by /auth/refresh itself). */
  skipAuth?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {};
  // FormData sets its own multipart Content-Type (with boundary) — the
  // browser only does that correctly if we leave the header unset.
  if (options.body !== undefined && !isFormData) headers["Content-Type"] = "application/json";
  if (accessToken && !options.skipAuth) headers.Authorization = `Bearer ${accessToken}`;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    credentials: "include",
    body: isFormData ? (options.body as FormData) : options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (payload && typeof payload === "object" && "error" in payload) {
      throw new ApiError(response.status, (payload as ApiErrorEnvelope).error);
    }
    throw new ApiError(response.status, {
      code: "INTERNAL",
      message: "Something went wrong. Please try again.",
      details: {},
    });
  }

  return payload as T;
}

/**
 * POST a JSON body and read the response as Server-Sent Events, invoking
 * `onFrame` for each parsed `data: <json>` event. Used by the developer
 * playground's streaming button (see app/ai/gateway.py's `_stream` on the
 * API side, which this mirrors frame-for-frame).
 *
 * Passing `signal` lets the caller cancel mid-stream — aborting the fetch
 * closes the connection, which is what actually aborts the upstream
 * provider request on the server.
 */
export async function streamSSE<T>(
  path: string,
  body: unknown,
  onFrame: (frame: T) => void,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!response.ok || !response.body) {
    const payload = await response.json().catch(() => null);
    if (payload && typeof payload === "object" && "error" in payload) {
      throw new ApiError(response.status, (payload as ApiErrorEnvelope).error);
    }
    throw new ApiError(response.status, {
      code: "INTERNAL",
      message: "Something went wrong. Please try again.",
      details: {},
    });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let separatorIndex = buffer.indexOf("\n\n");
    while (separatorIndex !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data: "));
      if (dataLine) {
        onFrame(JSON.parse(dataLine.slice("data: ".length)) as T);
      }
      separatorIndex = buffer.indexOf("\n\n");
    }
  }
}
