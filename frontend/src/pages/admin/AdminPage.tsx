import { useState } from "react";
import { UsersTab } from "./tabs/UsersTab";
import { SubscriptionsTab } from "./tabs/SubscriptionsTab";
import { FeatureFlagsTab } from "./tabs/FeatureFlagsTab";
import { AiOpsTab } from "./tabs/AiOpsTab";
import { ModerationTab } from "./tabs/ModerationTab";
import { PlatformHealthTab } from "./tabs/PlatformHealthTab";
import { cn } from "@/lib/cn";

const TABS = [
  { id: "users", label: "Users", Component: UsersTab },
  { id: "subscriptions", label: "Subscriptions", Component: SubscriptionsTab },
  { id: "flags", label: "Feature flags", Component: FeatureFlagsTab },
  { id: "ai-ops", label: "AI operations", Component: AiOpsTab },
  { id: "moderation", label: "Moderation", Component: ModerationTab },
  { id: "platform-health", label: "Platform health", Component: PlatformHealthTab },
] as const;

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]["id"]>("users");
  const Active = TABS.find((tab) => tab.id === activeTab)?.Component ?? UsersTab;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-fg">Admin</h1>
      <div className="mt-4 flex gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "border-b-2 px-3 py-2 text-sm font-medium",
              activeTab === tab.id
                ? "border-primary text-fg"
                : "border-transparent text-fg-muted hover:text-fg",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-6">
        <Active />
      </div>
    </div>
  );
}
