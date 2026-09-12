import { Link } from "react-router-dom";
import { EmptyState } from "@/components/ui/EmptyState";

export function NotFoundPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <EmptyState
        title="Page not found"
        description="The page you're looking for doesn't exist or has moved."
        action={
          <Link to="/" className="text-sm text-primary hover:underline">
            Back to dashboard
          </Link>
        }
      />
    </div>
  );
}
