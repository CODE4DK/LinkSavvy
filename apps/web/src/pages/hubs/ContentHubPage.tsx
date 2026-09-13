/**
 * Content Hub landing page. The eight content tools (post generator, hook
 * generator, etc.) will list here as cards once built, exactly like
 * Profile Hub's tool list -- for now this links to the voice profile
 * setup that every one of those tools will read from.
 */

import { Link } from "react-router-dom";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

export function ContentHubPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Content Hub</h1>
        <p className="text-sm text-fg-muted">
          Draft, refine, and plan LinkedIn posts with AI assistance -- LinkSavvy never posts to
          LinkedIn for you.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link to="/content/voice">
          <Card className="h-full transition-colors hover:border-primary">
            <CardHeader>
              <CardTitle>Voice profile</CardTitle>
              <CardDescription>
                Teach the content tools how you actually write, from your own past posts.
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>
    </div>
  );
}
