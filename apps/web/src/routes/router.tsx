import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "./RequireAuth";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { VerifyEmailPage } from "@/pages/auth/VerifyEmailPage";
import { ForgotPasswordPage } from "@/pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/auth/ResetPasswordPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AssistantPage } from "@/pages/AssistantPage";
import { ProfileHubPage } from "@/pages/hubs/ProfileHubPage";
import { ContentHubPage } from "@/pages/hubs/ContentHubPage";
import { EngagementHubPage } from "@/pages/hubs/EngagementHubPage";
import { CareerHubPage } from "@/pages/hubs/CareerHubPage";
import { GrowthHubPage } from "@/pages/hubs/GrowthHubPage";
import { WorkspaceHubPage } from "@/pages/hubs/WorkspaceHubPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/verify-email", element: <VerifyEmailPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/assistant", element: <AssistantPage /> },
          { path: "/profile", element: <ProfileHubPage /> },
          { path: "/content", element: <ContentHubPage /> },
          { path: "/engagement", element: <EngagementHubPage /> },
          { path: "/career", element: <CareerHubPage /> },
          { path: "/growth", element: <GrowthHubPage /> },
          { path: "/workspace", element: <WorkspaceHubPage /> },
          { path: "/settings", element: <SettingsPage /> },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);
