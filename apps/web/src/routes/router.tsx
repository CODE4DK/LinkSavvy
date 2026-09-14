import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "./RequireAuth";
import { RequireAdmin } from "./RequireAdmin";

// Every leaf page is loaded via the `lazy` route field rather than a
// top-level import, so Vite splits each into its own chunk and the
// initial bundle only pays for the shell + whichever page was requested
// -- see docs/performance.md "Frontend code splitting". Layout/guard
// components (AppShell, RequireAuth, RequireAdmin) stay eager: they're
// small and needed on every route regardless.

export const router = createBrowserRouter([
  {
    path: "/login",
    lazy: () => import("@/pages/auth/LoginPage").then((m) => ({ Component: m.LoginPage })),
  },
  {
    path: "/register",
    lazy: () => import("@/pages/auth/RegisterPage").then((m) => ({ Component: m.RegisterPage })),
  },
  {
    path: "/verify-email",
    lazy: () =>
      import("@/pages/auth/VerifyEmailPage").then((m) => ({ Component: m.VerifyEmailPage })),
  },
  {
    path: "/forgot-password",
    lazy: () =>
      import("@/pages/auth/ForgotPasswordPage").then((m) => ({
        Component: m.ForgotPasswordPage,
      })),
  },
  {
    path: "/reset-password",
    lazy: () =>
      import("@/pages/auth/ResetPasswordPage").then((m) => ({ Component: m.ResetPasswordPage })),
  },
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/onboarding",
        lazy: () =>
          import("@/pages/onboarding/OnboardingPage").then((m) => ({
            Component: m.OnboardingPage,
          })),
      },
      {
        path: "/profile/connect/callback",
        lazy: () =>
          import("@/pages/ProfileConnectCallbackPage").then((m) => ({
            Component: m.ProfileConnectCallbackPage,
          })),
      },
      {
        element: <AppShell />,
        children: [
          {
            path: "/",
            lazy: () => import("@/pages/DashboardPage").then((m) => ({ Component: m.DashboardPage })),
          },
          {
            path: "/assistant",
            lazy: () =>
              import("@/pages/AssistantPage").then((m) => ({ Component: m.AssistantPage })),
          },
          {
            path: "/profile",
            lazy: () =>
              import("@/pages/hubs/ProfileHubPage").then((m) => ({ Component: m.ProfileHubPage })),
          },
          {
            path: "/profile/:toolId",
            lazy: () =>
              import("@/pages/hubs/ProfileHubPage").then((m) => ({ Component: m.ProfileHubPage })),
          },
          {
            path: "/content",
            lazy: () =>
              import("@/pages/hubs/ContentHubPage").then((m) => ({ Component: m.ContentHubPage })),
          },
          {
            path: "/content/voice",
            lazy: () =>
              import("@/content/VoiceProfilePage").then((m) => ({ Component: m.VoiceProfilePage })),
          },
          {
            path: "/content/composer",
            lazy: () => import("@/content/Composer").then((m) => ({ Component: m.Composer })),
          },
          {
            path: "/content/carousel/:carouselId",
            lazy: () =>
              import("@/content/CarouselBuilder").then((m) => ({ Component: m.CarouselBuilder })),
          },
          {
            path: "/content/calendar",
            lazy: () => import("@/content/Calendar").then((m) => ({ Component: m.Calendar })),
          },
          {
            path: "/content/:toolId",
            lazy: () =>
              import("@/pages/hubs/ContentHubPage").then((m) => ({ Component: m.ContentHubPage })),
          },
          {
            path: "/engagement",
            lazy: () =>
              import("@/pages/hubs/EngagementHubPage").then((m) => ({
                Component: m.EngagementHubPage,
              })),
          },
          {
            path: "/engagement/:toolId",
            lazy: () =>
              import("@/pages/hubs/EngagementHubPage").then((m) => ({
                Component: m.EngagementHubPage,
              })),
          },
          {
            path: "/career",
            lazy: () =>
              import("@/pages/hubs/CareerHubPage").then((m) => ({ Component: m.CareerHubPage })),
          },
          {
            path: "/career/:toolId",
            lazy: () =>
              import("@/pages/hubs/CareerHubPage").then((m) => ({ Component: m.CareerHubPage })),
          },
          {
            path: "/growth",
            lazy: () =>
              import("@/pages/hubs/GrowthHubPage").then((m) => ({ Component: m.GrowthHubPage })),
          },
          {
            path: "/growth/coach",
            lazy: () =>
              import("@/pages/hubs/GrowthCoachPage").then((m) => ({
                Component: m.GrowthCoachPage,
              })),
          },
          {
            path: "/growth/:toolId",
            lazy: () =>
              import("@/pages/hubs/GrowthHubPage").then((m) => ({ Component: m.GrowthHubPage })),
          },
          {
            path: "/workspace",
            lazy: () =>
              import("@/pages/hubs/WorkspaceHubPage").then((m) => ({
                Component: m.WorkspaceHubPage,
              })),
          },
          {
            path: "/billing/pricing",
            lazy: () =>
              import("@/pages/billing/PricingPage").then((m) => ({ Component: m.PricingPage })),
          },
          {
            path: "/billing/manage",
            lazy: () =>
              import("@/pages/billing/BillingManagePage").then((m) => ({
                Component: m.BillingManagePage,
              })),
          },
          {
            path: "/billing/checkout-return",
            lazy: () =>
              import("@/pages/billing/CheckoutReturnPage").then((m) => ({
                Component: m.CheckoutReturnPage,
              })),
          },
          {
            path: "/settings",
            lazy: () => import("@/pages/SettingsPage").then((m) => ({ Component: m.SettingsPage })),
          },
          {
            path: "/settings/notifications",
            lazy: () =>
              import("@/pages/NotificationPreferencesPage").then((m) => ({
                Component: m.NotificationPreferencesPage,
              })),
          },
          {
            path: "/dev/playground",
            lazy: () =>
              import("@/pages/dev/PlaygroundPage").then((m) => ({ Component: m.PlaygroundPage })),
          },
          {
            element: <RequireAdmin />,
            children: [
              {
                path: "/admin",
                lazy: () => import("@/pages/admin/AdminPage").then((m) => ({ Component: m.AdminPage })),
              },
            ],
          },
          {
            path: "*",
            lazy: () => import("@/pages/NotFoundPage").then((m) => ({ Component: m.NotFoundPage })),
          },
        ],
      },
    ],
  },
]);
