import { ProfileSection } from "./settings/ProfileSection";
import { ThemeSection } from "./settings/ThemeSection";
import { SessionsSection } from "./settings/SessionsSection";
import { ChangePasswordSection } from "./settings/ChangePasswordSection";
import { DeleteAccountSection } from "./settings/DeleteAccountSection";

export function SettingsPage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <h1 className="text-2xl font-semibold text-fg">Settings</h1>
      <ProfileSection />
      <ThemeSection />
      <SessionsSection />
      <ChangePasswordSection />
      <DeleteAccountSection />
    </div>
  );
}
