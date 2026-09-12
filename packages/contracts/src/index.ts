/**
 * Public entry point for `@linksavvy/contracts`.
 *
 * `schema.d.ts` is generated from the API's OpenAPI document
 * (`make contracts`, backed by `apps/api/scripts/export_openapi.py` and
 * `openapi-typescript`) — never hand-edit it. Everything below is a thin,
 * hand-maintained convenience layer on top of the generated `components`
 * schemas, so the web app can `import type { LoginResponse } from
 * "@linksavvy/contracts"` instead of drilling into `components["schemas"]`.
 */

import type { components, paths } from "./schema";

export type { paths };
export type Schemas = components["schemas"];

export * from "./profile-schema";

export type RegisterRequest = Schemas["RegisterRequest"];
export type MessageResponse = Schemas["MessageResponse"];
export type VerifyEmailRequest = Schemas["VerifyEmailRequest"];
export type ResendVerificationRequest = Schemas["ResendVerificationRequest"];
export type LoginRequest = Schemas["LoginRequest"];
export type LoginResponse = Schemas["LoginResponse"];
export type RefreshResponse = Schemas["RefreshResponse"];
export type SessionOut = Schemas["SessionOut"];
export type ForgotPasswordRequest = Schemas["ForgotPasswordRequest"];
export type ResetPasswordRequest = Schemas["ResetPasswordRequest"];
export type ChangePasswordRequest = Schemas["ChangePasswordRequest"];
export type LinkedInStartResponse = Schemas["LinkedInStartResponse"];
export type UserPublic = Schemas["UserPublic"];
export type MeResponse = Schemas["MeResponse"];
export type HTTPValidationError = Schemas["HTTPValidationError"];
export type UpdateProfileRequest = Schemas["UpdateProfileRequest"];
export type DeleteAccountRequest = Schemas["DeleteAccountRequest"];

export type SnapshotSummary = Schemas["SnapshotSummary"];
export type SnapshotDetail = Schemas["SnapshotDetail"];
export type SyncResponse = Schemas["SyncResponse"];
export type ImportPasteRequest = Schemas["ImportPasteRequest"];
export type ImportResponse = Schemas["ImportResponse"];
export type CommitImportRequest = Schemas["CommitImportRequest"];
export type SnapshotDiff = Schemas["SnapshotDiff"];
export type FieldChange = Schemas["FieldChange"];
export type ListItemChange = Schemas["ListItemChange"];

export type GatewayMetricsResponse = Schemas["GatewayMetricsResponse"];
export type PlaygroundPromptSummary = Schemas["PlaygroundPromptSummary"];
export type PlaygroundRunRequest = Schemas["PlaygroundRunRequest"];
export type PlaygroundRunResponse = Schemas["PlaygroundRunResponse"];

/** The `{"error": {code, message, details}}` envelope every API error uses. */
export interface ApiErrorEnvelope {
  error: {
    code:
      | "INVALID_CREDENTIALS"
      | "EMAIL_NOT_VERIFIED"
      | "TOKEN_EXPIRED"
      | "TOKEN_REUSED"
      | "RATE_LIMITED"
      | "FORBIDDEN"
      | "NOT_FOUND"
      | "VALIDATION_FAILED"
      | "INTERNAL"
      | "QUOTA_EXCEEDED"
      | "AI_OUTPUT_INVALID"
      | "AI_POLICY_BLOCKED"
      | "AI_PROVIDER_UNAVAILABLE";
    message: string;
    details: Record<string, unknown>;
  };
}

/** One SSE frame from POST /internal/playground/stream. */
export type PlaygroundStreamFrame =
  | { type: "meta"; correlation_id: string; model: string; provider: string; cached: boolean }
  | { type: "delta"; text: string }
  | { type: "error"; code: string; message: string }
  | {
      type: "done";
      tokens_in: number;
      tokens_out: number;
      cost_minor: number;
      latency_ms?: number;
      fallback_used?: boolean;
    };
