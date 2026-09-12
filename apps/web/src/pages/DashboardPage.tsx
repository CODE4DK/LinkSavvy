import { Link } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { PRIMARY_NAV_ITEMS } from "@/lib/nav-items";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export function DashboardPage() {
  const { user, featureFlags } = useAuth();
  const hubLinks = PRIMARY_NAV_ITEMS.filter((item) => item.path !== "/");

  return (
    <div>
      <h1 className="text-2xl font-semibold text-fg">
        Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}
      </h1>
      <p className="mt-1 text-sm text-fg-muted">
        Here&apos;s your LinkedIn Command Center. Hubs light up as they ship.
      </p>

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
