import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { apiFetch, ApiError } from "@/lib/api";
import { PRIMARY_NAV_ITEMS } from "@/lib/nav-items";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

function useHasProfileSnapshot(): boolean | undefined {
  const { data, isLoading } = useQuery({
    queryKey: ["profile", "snapshot", "exists"],
    queryFn: async () => {
      try {
        await apiFetch("/api/v1/profile/snapshot");
        return true;
      } catch (error) {
        if (error instanceof ApiError && error.code === "NOT_FOUND") return false;
        throw error;
      }
    },
  });
  return isLoading ? undefined : data;
}

export function DashboardPage() {
  const { user, featureFlags } = useAuth();
  const hasSnapshot = useHasProfileSnapshot();
  const hubLinks = PRIMARY_NAV_ITEMS.filter((item) => item.path !== "/");

  return (
    <div>
      <h1 className="text-2xl font-semibold text-fg">
        Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}
      </h1>
      <p className="mt-1 text-sm text-fg-muted">
        Here&apos;s your LinkedIn Command Center. Hubs light up as they ship.
      </p>

      {hasSnapshot === false && (
        <Card className="mt-6 border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle>Set up your profile</CardTitle>
            <CardDescription>
              Bring in your professional data via LinkedIn, paste, upload, or a quick form — takes
              a couple of minutes.
            </CardDescription>
          </CardHeader>
          <Link to="/onboarding">
            <Button>Get started</Button>
          </Link>
        </Card>
      )}

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {hubLinks.map((item) => {
          const enabled = item.flag === undefined || featureFlags[item.flag];
          return (
            <Link key={item.path} to={item.path}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle>{item.label}</CardTitle>
                  <Badge variant={enabled ? "success" : "default"}>
                    {enabled ? "Live" : "Coming soon"}
                  </Badge>
                </CardHeader>
                <CardDescription>
                  {enabled ? "Open this hub to get started." : "This hub ships in a later phase."}
                </CardDescription>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
