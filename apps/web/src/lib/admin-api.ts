import type {
  AdjustPlanRequest,
  AdminSubscriptionResponse,
  AdminUserDetailResponse,
  AdminUserResponse,
  AdminUserSearchResponse,
  AiOpsOverviewResponse,
  AiInvocationResponse,
  FeatureFlagResponse,
  ForcePasswordResetResponse,
  ImpersonateResponse,
  JobResponse,
  ModerationFlagResponse,
  PlatformHealthResponse,
  ReviewFlagRequest,
  SetFlagGlobalRequest,
  SetFlagRolloutRequest,
  SetFlagUserOverrideRequest,
  SuspendUserRequest,
  WebhookEventResponse,
} from "@linksavvy/contracts";
import { apiFetch } from "./api";

export function searchUsers(params: {
  q?: string;
  plan?: string;
  status?: string;
  offset?: number;
  limit?: number;
}): Promise<AdminUserSearchResponse> {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  return apiFetch<AdminUserSearchResponse>(`/api/v1/admin/users?${search.toString()}`);
}

export function getUserDetail(userId: string): Promise<AdminUserDetailResponse> {
  return apiFetch<AdminUserDetailResponse>(`/api/v1/admin/users/${userId}`);
}

export function suspendUser(
  userId: string,
  payload: SuspendUserRequest,
): Promise<AdminUserResponse> {
  return apiFetch<AdminUserResponse>(`/api/v1/admin/users/${userId}/suspend`, {
    method: "POST",
    body: payload,
  });
}

export function reinstateUser(userId: string): Promise<AdminUserResponse> {
  return apiFetch<AdminUserResponse>(`/api/v1/admin/users/${userId}/reinstate`, {
    method: "POST",
  });
}

export function forcePasswordReset(userId: string): Promise<ForcePasswordResetResponse> {
  return apiFetch<ForcePasswordResetResponse>(
    `/api/v1/admin/users/${userId}/force-password-reset`,
    { method: "POST" },
  );
}

export function adjustPlan(
  userId: string,
  payload: AdjustPlanRequest,
): Promise<AdminUserResponse> {
  return apiFetch<AdminUserResponse>(`/api/v1/admin/users/${userId}/adjust-plan`, {
    method: "POST",
    body: payload,
  });
}

export function impersonateUser(userId: string): Promise<ImpersonateResponse> {
  return apiFetch<ImpersonateResponse>(`/api/v1/admin/users/${userId}/impersonate`, {
    method: "POST",
  });
}

export function listSubscriptions(status?: string): Promise<AdminSubscriptionResponse[]> {
  const search = status ? `?status=${status}` : "";
  return apiFetch<AdminSubscriptionResponse[]>(`/api/v1/admin/subscriptions${search}`);
}

export function getWebhookHistory(subscriptionId: string): Promise<WebhookEventResponse[]> {
  return apiFetch<WebhookEventResponse[]>(
    `/api/v1/admin/subscriptions/${subscriptionId}/webhooks`,
  );
}

export function replayWebhook(webhookEventId: string): Promise<WebhookEventResponse> {
  return apiFetch<WebhookEventResponse>(`/api/v1/admin/webhooks/${webhookEventId}/replay`, {
    method: "POST",
  });
}

export function listFeatureFlags(): Promise<FeatureFlagResponse[]> {
  return apiFetch<FeatureFlagResponse[]>("/api/v1/admin/feature-flags");
}

export function setFlagGlobal(
  key: string,
  payload: SetFlagGlobalRequest,
): Promise<FeatureFlagResponse> {
  return apiFetch<FeatureFlagResponse>(`/api/v1/admin/feature-flags/${key}/global`, {
    method: "POST",
    body: payload,
  });
}

export function setFlagRollout(
  key: string,
  payload: SetFlagRolloutRequest,
): Promise<FeatureFlagResponse> {
  return apiFetch<FeatureFlagResponse>(`/api/v1/admin/feature-flags/${key}/rollout`, {
    method: "POST",
    body: payload,
  });
}

export function setFlagUserOverride(
  key: string,
  payload: SetFlagUserOverrideRequest,
): Promise<void> {
  return apiFetch<void>(`/api/v1/admin/feature-flags/${key}/user-override`, {
    method: "POST",
    body: payload,
  });
}

export function getAiOpsOverview(days = 30): Promise<AiOpsOverviewResponse> {
  return apiFetch<AiOpsOverviewResponse>(`/api/v1/admin/ai-ops/overview?days=${days}`);
}

export function getPromptDrilldown(promptId: string, days = 30): Promise<AiInvocationResponse[]> {
  return apiFetch<AiInvocationResponse[]>(
    `/api/v1/admin/ai-ops/prompts/${encodeURIComponent(promptId)}?days=${days}`,
  );
}

export function listModerationFlags(status = "pending"): Promise<ModerationFlagResponse[]> {
  return apiFetch<ModerationFlagResponse[]>(`/api/v1/admin/moderation/flags?status=${status}`);
}

export function reviewModerationFlag(
  flagId: string,
  payload: ReviewFlagRequest,
): Promise<ModerationFlagResponse> {
  return apiFetch<ModerationFlagResponse>(`/api/v1/admin/moderation/flags/${flagId}/review`, {
    method: "POST",
    body: payload,
  });
}

export function getPlatformHealth(): Promise<PlatformHealthResponse> {
  return apiFetch<PlatformHealthResponse>("/api/v1/admin/platform-health");
}

export function retryDeadJob(jobId: string): Promise<JobResponse> {
  return apiFetch<JobResponse>(`/api/v1/admin/jobs/${jobId}/retry`, { method: "POST" });
}
