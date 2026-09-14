import { Link } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export function NotificationsSection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>Choose what you're notified about, and how.</CardDescription>
      </CardHeader>
      <Link to="/settings/notifications" className="text-sm text-primary underline">
        Manage notification preferences
      </Link>
    </Card>
  );
}
