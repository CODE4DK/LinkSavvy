import type {
  CancelSubscriptionRequest,
  ChangePlanRequest,
  CheckoutRequest,
  CheckoutResponse,
  PaymentResponse,
  PortalResponse,
  PricingResponse,
  SubscriptionResponse,
} from "@/contracts";
import { apiFetch } from "./api";

export function getPricing(): Promise<PricingResponse> {
  return apiFetch<PricingResponse>("/api/v1/billing/pricing");
}

export function getSubscription(): Promise<SubscriptionResponse> {
  return apiFetch<SubscriptionResponse>("/api/v1/billing/subscription");
}

export function listPayments(): Promise<PaymentResponse[]> {
  return apiFetch<PaymentResponse[]>("/api/v1/billing/payments");
}

export function createCheckout(payload: CheckoutRequest): Promise<CheckoutResponse> {
  return apiFetch<CheckoutResponse>("/api/v1/billing/checkout", { method: "POST", body: payload });
}

export function createPortalSession(): Promise<PortalResponse> {
  return apiFetch<PortalResponse>("/api/v1/billing/portal", { method: "POST" });
}

export function cancelSubscription(
  payload: CancelSubscriptionRequest,
): Promise<SubscriptionResponse> {
  return apiFetch<SubscriptionResponse>("/api/v1/billing/cancel", {
    method: "POST",
    body: payload,
  });
}

export function changePlan(payload: ChangePlanRequest): Promise<SubscriptionResponse> {
  return apiFetch<SubscriptionResponse>("/api/v1/billing/change-plan", {
    method: "POST",
    body: payload,
  });
}
