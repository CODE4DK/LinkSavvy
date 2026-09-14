import { Link } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export function BillingSection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Billing</CardTitle>
        <CardDescription>Plan, payment method, invoices, and cancellation.</CardDescription>
      </CardHeader>
      <div className="flex gap-3">
        <Link to="/billing/pricing" className="text-sm text-primary underline">
          View plans
        </Link>
        <Link to="/billing/manage" className="text-sm text-primary underline">
          Manage subscription
        </Link>
      </div>
    </Card>
  );
}
