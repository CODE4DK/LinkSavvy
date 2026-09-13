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
export * from "./career-schema";

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

export type JobStatusResponse = Schemas["JobStatusResponse"];

export type AuditRunRequest = Schemas["AuditRunRequest"];
export type AuditRunResponse = Schemas["AuditRunResponse"];
export type AuditFindingResponse = Schemas["AuditFindingResponse"];
export type AuditCategoryResultResponse =
  Schemas["AuditCategoryResultResponse"];
export type AuditDetailResponse = Schemas["AuditDetailResponse"];
export type ScoreHistoryPoint = Schemas["ScoreHistoryPoint"];
export type ScoreHistoryResponse = Schemas["ScoreHistoryResponse"];
export type RecommendationResponse = Schemas["RecommendationResponse"];
export type RecommendationListResponse = Schemas["RecommendationListResponse"];
export type RecommendationUpdateRequest =
  Schemas["RecommendationUpdateRequest"];

export type DashboardUser = Schemas["DashboardUser"];
export type DashboardHealthScore = Schemas["DashboardHealthScore"];
export type DashboardRunAuditState = Schemas["DashboardRunAuditState"];
export type DashboardScoreHistory = Schemas["DashboardScoreHistory"];
export type DashboardResponse = Schemas["DashboardResponse"];

export type ToolSummary = Schemas["ToolSummary"];
export type ToolRunRequest = Schemas["ToolRunRequest"];
export type ToolRunResponse = Schemas["ToolRunResponse"];
export type ToolRunSummary = Schemas["ToolRunSummary"];
export type QuotaInfo = Schemas["QuotaInfo"];
export type RegenerateRequest = Schemas["RegenerateRequest"];
export type RateRequest = Schemas["RateRequest"];
export type RateResponse = Schemas["RateResponse"];
export type SaveAssetRequest = Schemas["SaveAssetRequest"];
export type AssetResponse = Schemas["AssetResponse"];

export type VoiceSamplesRequest = Schemas["VoiceSamplesRequest"];
export type VoiceDescriptorResponse = Schemas["VoiceDescriptorResponse"];

export type CreateAssetRequest = Schemas["CreateAssetRequest"];
export type MarkPostedRequest = Schemas["MarkPostedRequest"];

export type CarouselCover = Schemas["CarouselCover"];
export type CarouselSlide = Schemas["CarouselSlide"];
export type CarouselClosing = Schemas["CarouselClosing"];
export type CarouselData = Schemas["CarouselData"];
export type SaveCarouselRequest = Schemas["SaveCarouselRequest"];
export type CarouselResponse = Schemas["CarouselResponse"];

export type ContentPlanStatus = Schemas["ContentPlanCreate"]["status"];
export type ContentPlanCreate = Schemas["ContentPlanCreate"];
export type ContentPlanUpdate = Schemas["ContentPlanUpdate"];
export type ContentPlanResponse = Schemas["ContentPlanResponse"];
export type RescheduleRequest = Schemas["RescheduleRequest"];
export type ReminderRequest = Schemas["ReminderRequest"];
export type PerformanceNumbers = Schemas["PerformanceNumbers"];
export type MarkContentPlanPostedRequest =
  Schemas["MarkContentPlanPostedRequest"];
export type Cadence = Schemas["Cadence"];
export type RecurringSlotsRequest = Schemas["RecurringSlotsRequest"];
export type BulkScheduleRequest = Schemas["BulkScheduleRequest"];
export type ConsistencyWeek = Schemas["ConsistencyWeek"];
export type PostTypePerformance = Schemas["PostTypePerformance"];
export type PerformanceSummaryResponse = Schemas["PerformanceSummaryResponse"];

export type ResumeParseResponse = Schemas["ResumeParseResponse"];
export type CommitResumeRequest = Schemas["CommitResumeRequest"];
export type ResumeResponse = Schemas["ResumeResponse"];
export type JobDescriptionParseRequest = Schemas["JobDescriptionParseRequest"];
export type JobDescriptionResponse = Schemas["JobDescriptionResponse"];
export type CreateResumeMatchRequest = Schemas["CreateResumeMatchRequest"];
export type ResumeMatchResponse = Schemas["ResumeMatchResponse"];

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
  | {
      type: "meta";
      correlation_id: string;
      model: string;
      provider: string;
      cached: boolean;
    }
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

/**
 * One SSE frame from `POST /api/v1/tools/{id}/run?stream=true` -- the same
 * shape as `PlaygroundStreamFrame`'s meta/delta/error/done frames, plus a
 * final `tool_run` frame (sent only after a successful `done`) carrying
 * the persisted run's id, the context keys it used, and quota -- the same
 * information the non-streaming `ToolRunResponse` returns in one shot.
 */
export type ToolRunStreamFrame =
  | {
      type: "meta";
      correlation_id: string;
      model: string;
      provider: string;
      cached: boolean;
    }
  | { type: "delta"; text: string }
  | { type: "error"; code: string; message: string }
  | {
      type: "done";
      tokens_in: number;
      tokens_out: number;
      cost_minor: number;
      latency_ms?: number;
      fallback_used?: boolean;
    }
  | {
      type: "tool_run";
      run_id: string;
      context_used: string[];
      quota: QuotaInfo;
      warning?: string | null;
    };
