import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import type { DashboardResponse } from "@/contracts";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useAssistant } from "@/lib/assistant-context";
import { PRIMARY_NAV_ITEMS } from "@/lib/nav-items";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { HealthScoreRing } from "@/components/dashboard/HealthScoreRing";
import { CategorySubscore } from "@/components/dashboard/CategorySubscore";
import { ScoreSparkline } from "@/components/dashboard/ScoreSparkline";
import { RecommendationCard } from "@/components/dashboard/RecommendationCard";
import { RunAuditControl } from "@/components/dashboard/RunAuditControl";

function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<DashboardResponse>("/api/v1/dashboard"),
  });
}

function AssistantPromptBar() {
  const [value, setValue] = useState("");
  const navigate = useNavigate();
  const { startConversationWithMessage } = useAssistant();

  return (
    <Card>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const text = value.trim();
          if (!text) {
            navigate("/assistant");
            return;
          }
          startConversationWithMessage(text);
          navigate("/assistant");
        }}
        className="flex flex-col gap-3 sm:flex-row sm:items-center"
      >
        <div className="flex-1">
          <p className="text-sm font-medium text-fg">Ask your AI Assistant</p>
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="e.g. How can I make my headline stronger?"
            className="mt-2 w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-fg placeholder:text-fg-muted focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>
        <Button type="submit" variant="secondary">
          Ask
        </Button>
      </form>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-64 w-full" />
      <Skeleton className="h-40 w-full" />
    </div>
  );
}

function FirstTimeEmptyState({ data }: { data: DashboardResponse }) {
  const needsSnapshot = data.run_audit.reason === "no_active_snapshot";
  return (
    <EmptyState
      title={needsSnapshot ? "Set up your profile first" : "Run your first audit"}
      description={
        needsSnapshot
          ? "Bring in your professional data so LinkSavvy has something to score."
          : "See your Health Score, category breakdowns, and your top recommendations in a couple of minutes."
      }
      action={
        needsSnapshot ? (
          <Link to="/onboarding">
            <Button>Get started</Button>
          </Link>
        ) : (
          <RunAuditControl runAudit={data.run_audit} />
        )
      }
    />
  );
}

function HealthScoreSection({ data }: { data: DashboardResponse }) {
  if (!data.health_score) return null;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Health Score</CardTitle>
          <CardDescription>
            Last updated{" "}
            {data.health_score.completed_at
              ? new Date(data.health_score.completed_at).toLocaleDateString()
              : "just now"}
          </CardDescription>
        </div>
        <RunAuditControl runAudit={data.run_audit} />
      </CardHeader>
      <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
        <HealthScoreRing overall={data.health_score.overall} />
        <div className="w-full flex-1">
          {data.health_score.categories.map((result) => (
            <CategorySubscore key={result.category} result={result} />
          ))}
        </div>
      </div>
    </Card>
  );
}

function TrendSection({ data }: { data: DashboardResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>90-day trend</CardTitle>
        <CardDescription>How your overall score has moved.</CardDescription>
      </CardHeader>
      <ScoreSparkline points={data.score_history.points} delta={data.score_history.delta} />
    </Card>
  );
}

function RecommendationsSection({ data }: { data: DashboardResponse }) {
  if (data.top_recommendations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recommendations</CardTitle>
          <CardDescription>Nothing open right now — nice work.</CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top recommendations</CardTitle>
        <CardDescription>The highest-leverage things to do next.</CardDescription>
      </CardHeader>
      <div className="flex flex-col gap-3">
        {data.top_recommendations.map((recommendation) => (
          <RecommendationCard key={recommendation.id} recommendation={recommendation} />
        ))}
      </div>
    </Card>
  );
}

function HubGrid({ hubs }: { hubs: Record<string, boolean> }) {
  const hubLinks = PRIMARY_NAV_ITEMS.filter((item) => item.path !== "/");
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {hubLinks.map((item) => {
        const enabled = item.flag === undefined || hubs[item.flag];
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
  );
}

function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick actions</CardTitle>
      </CardHeader>
      <div className="flex flex-wrap gap-2">
        <Link to="/profile">
          <Button variant="secondary" size="sm">
            Update profile
          </Button>
        </Link>
        <Link to="/content">
          <Button variant="secondary" size="sm">
            Draft a post
          </Button>
        </Link>
        <Link to="/career">
          <Button variant="secondary" size="sm">
            Update resume
          </Button>
        </Link>
      </div>
    </Card>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useDashboard();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-fg">
          Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="mt-1 text-sm text-fg-muted">
          {data?.health_score
            ? `Your Health Score is ${data.health_score.overall ?? "--"}.`
            : "Here's your LinkedIn Command Center."}
        </p>
      </div>

      {isLoading && <DashboardSkeleton />}

      {isError && (
        <EmptyState
          title="Couldn't load your dashboard"
          description="Please refresh the page or try again shortly."
        />
      )}

      {data && (
        <>
          <AssistantPromptBar />

          {data.is_first_time ? (
            <FirstTimeEmptyState data={data} />
          ) : (
            <>
              <HealthScoreSection data={data} />
              <TrendSection data={data} />
              <RecommendationsSection data={data} />
            </>
          )}

          <HubGrid hubs={data.hubs} />
          <QuickActions />

          {user?.role === "admin" && data.hubs["dev.playground"] && (
            <Link to="/dev/playground">
              <Card className="border-dashed transition-shadow hover:shadow-md">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle>AI Playground</CardTitle>
                  <Badge variant="primary">Admin</Badge>
                </CardHeader>
                <CardDescription>
                  Run or stream any registered prompt through the gateway directly.
                </CardDescription>
              </Card>
            </Link>
          )}
        </>
      )}
    </div>
  );
}
