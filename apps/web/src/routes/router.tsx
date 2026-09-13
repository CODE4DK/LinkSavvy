import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "./RequireAuth";
import { RequireAdmin } from "./RequireAdmin";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { VerifyEmailPage } from "@/pages/auth/VerifyEmailPage";
import { ForgotPasswordPage } from "@/pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/auth/ResetPasswordPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AssistantPage } from "@/pages/AssistantPage";
import { ProfileHubPage } from "@/pages/hubs/ProfileHubPage";
import { ContentHubPage } from "@/pages/hubs/ContentHubPage";
import { VoiceProfilePage } from "@/content/VoiceProfilePage";
import { Composer } from "@/content/Composer";
import { CarouselBuilder } from "@/content/CarouselBuilder";
import { Calendar } from "@/content/Calendar";
import { EngagementHubPage } from "@/pages/hubs/EngagementHubPage";
import { CareerHubPage } from "@/pages/hubs/CareerHubPage";
import { GrowthHubPage } from "@/pages/hubs/GrowthHubPage";
import { GrowthCoachPage } from "@/pages/hubs/GrowthCoachPage";
import { WorkspaceHubPage } from "@/pages/hubs/WorkspaceHubPage";
import { PricingPage } from "@/pages/billing/PricingPage";
import { BillingManagePage } from "@/pages/billing/BillingManagePage";
import { CheckoutReturnPage } from "@/pages/billing/CheckoutReturnPage";
import { NotificationPreferencesPage } from "@/pages/NotificationPreferencesPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { OnboardingPage } from "@/pages/onboarding/OnboardingPage";
import { ProfileConnectCallbackPage } from "@/pages/ProfileConnectCallbackPage";
import { PlaygroundPage } from "@/pages/dev/PlaygroundPage";
import { AdminPage } from "@/pages/admin/AdminPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/verify-email", element: <VerifyEmailPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  {
    element: <RequireAuth />,
    children: [
      { path: "/onboarding", element: <OnboardingPage /> },
      { path: "/profile/connect/callback", element: <ProfileConnectCallbackPage /> },
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/assistant", element: <AssistantPage /> },
          { path: "/profile", element: <ProfileHubPage /> },
          { path: "/profile/:toolId", element: <ProfileHubPage /> },
          { path: "/content", element: <ContentHubPage /> },
          { path: "/content/voice", element: <VoiceProfilePage /> },
          { path: "/content/composer", element: <Composer /> },
          { path: "/content/carousel/:carouselId", element: <CarouselBuilder /> },
          { path: "/content/calendar", element: <Calendar /> },
          { path: "/content/:toolId", element: <ContentHubPage /> },
          { path: "/engagement", element: <EngagementHubPage /> },
          { path: "/engagement/:toolId", element: <EngagementHubPage /> },
          { path: "/career", element: <CareerHubPage /> },
          { path: "/career/:toolId", element: <CareerHubPage /> },
          { path: "/growth", element: <GrowthHubPage /> },
          { path: "/growth/coach", element: <GrowthCoachPage /> },
          { path: "/growth/:toolId", element: <GrowthHubPage /> },
          { path: "/workspace", element: <WorkspaceHubPage /> },
          { path: "/billing/pricing", element: <PricingPage /> },
          { path: "/billing/manage", element: <BillingManagePage /> },
          { path: "/billing/checkout-return", element: <CheckoutReturnPage /> },
          { path: "/settings", element: <SettingsPage /> },
          { path: "/settings/notifications", element: <NotificationPreferencesPage /> },
          { path: "/dev/playground", element: <PlaygroundPage /> },
          {
            element: <RequireAdmin />,
            children: [{ path: "/admin", element: <AdminPage /> }],
          },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);
