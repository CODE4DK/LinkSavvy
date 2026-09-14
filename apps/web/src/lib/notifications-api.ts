import type {
  NotificationListResponse,
  PreferencesResponse,
  SetPreferenceRequest,
} from "@linksavvy/contracts";
import { apiFetch } from "./api";

export function listNotifications(unreadOnly = false): Promise<NotificationListResponse> {
  return apiFetch<NotificationListResponse>(
    `/api/v1/notifications${unreadOnly ? "?unread_only=true" : ""}`,
  );
}

export function markNotificationRead(id: string): Promise<void> {
  return apiFetch<void>(`/api/v1/notifications/${id}/read`, { method: "POST" });
}

export function markAllNotificationsRead(): Promise<void> {
  return apiFetch<void>("/api/v1/notifications/read-all", { method: "POST" });
}

export function getNotificationPreferences(): Promise<PreferencesResponse> {
  return apiFetch<PreferencesResponse>("/api/v1/notifications/preferences");
}

export function setNotificationPreference(
  payload: SetPreferenceRequest,
): Promise<PreferencesResponse> {
  return apiFetch<PreferencesResponse>("/api/v1/notifications/preferences", {
    method: "PUT",
    body: payload,
  });
}
