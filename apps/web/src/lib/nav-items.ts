export interface NavItem {
  label: string;
  path: string;
  /** Feature flag key gating this hub; undefined means always visible. */
  flag?: string;
}

export const PRIMARY_NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", path: "/" },
  { label: "AI Assistant", path: "/assistant", flag: "assistant" },
  { label: "Profile Hub", path: "/profile", flag: "hub.profile" },
  { label: "Content Hub", path: "/content", flag: "hub.content" },
  { label: "Engagement Hub", path: "/engagement", flag: "hub.engagement" },
  { label: "Career Hub", path: "/career", flag: "hub.career" },
  { label: "Growth Hub", path: "/growth", flag: "hub.growth" },
  { label: "Workspace Hub", path: "/workspace", flag: "hub.workspace" },
];
