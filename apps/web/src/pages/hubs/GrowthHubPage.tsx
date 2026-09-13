/**
 * Growth Hub: the four scores as a compact row, a 6-month multi-line
 * trend chart, the current week's plan with checkboxes and streak
 * stats, and a before/after panel that ties a score change to the tool
 * runs and profile edits that happened in between -- the product's
 * concrete proof of value. No charting library, same as
 * ScoreSparkline: these are a handful of polylines, not a dashboard
 * that needs one.
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type {
  BeforeAfterResponse,
  GrowthGoalResponse,
  GrowthScoreHistoryResponse,
  GrowthScoreResponse,
  GrowthScoresResponse,
  WeeklyPlanResponse,
} from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { ToolRunner } from "@/tools/ToolRunner";

const SCORE_LABELS: Record<keyof GrowthScoresResponse, string> = {
  health: "Health",
  visibility: "Visibility",
  consistency: "Consistency",
  personal_branding: "Personal Branding",
};

const SCORE_ORDER: (keyof GrowthScoresResponse)[] = [
  "health",
  "visibility",
  "consistency",
  "personal_branding",
];

const LINE_COLORS: Record<keyof GrowthScoresResponse, string> = {
  health: "hsl(var(--color-primary))",
  visibility: "#0ea5e9",
  consistency: "#22c55e",
  personal_branding: "#a855f7",
};

function statusLabel(status: string): string {
  if (status === "insufficient_data") return "not enough data";
  if (status === "skipped") return "not started";
  return status;
}

function ScoreCard({
  scoreType,
  score,
}: {
  scoreType: keyof GrowthScoresResponse;
  score: GrowthScoreResponse;
}) {
  return (
    <Card className="flex flex-col gap-2 p-4">
      <span className="text-xs font-medium uppercase tracking-wide text-fg-muted">
        {SCORE_LABELS[scoreType]}
      </span>
      {score.value !== null ? (
        <span className="text-3xl font-semibold text-fg">{score.value}</span>
      ) : (
        <span className="text-sm text-fg-muted">{statusLabel(score.status)}</span>
      )}
      {score.status !== "ok" && score.value !== null && (
        <Badge variant="warning">{statusLabel(score.status)}</Badge>
      )}
      {score.needed && <p className="text-xs text-fg-muted">{String(score.needed.reason ?? "")}</p>}
    </Card>
  );
}

function ScoresRow({ scores }: { scores: GrowthScoresResponse }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {SCORE_ORDER.map((scoreType) => (
        <ScoreCard key={scoreType} scoreType={scoreType} score={scores[scoreType]} />
      ))}
    </div>
  );
}

const CHART_WIDTH = 640;
const CHART_HEIGHT = 160;
const CHART_PADDING = 8;

function TrendChart({ history }: { history: GrowthScoreHistoryResponse }) {
  const allPoints = SCORE_ORDER.flatMap((scoreType) => history[scoreType]);
  if (allPoints.length === 0) {
    return (
      <p className="text-sm text-fg-muted">
        Not enough history yet -- visit the Growth Hub over the coming weeks to build a trend.
      </p>
    );
  }

  const dates = Array.from(new Set(allPoints.map((p) => p.snapshot_date))).sort();
  const xFor = (dateStr: string) => {
    if (dates.length === 1) return CHART_WIDTH / 2;
    const index = dates.indexOf(dateStr);
    return CHART_PADDING + (index / (dates.length - 1)) * (CHART_WIDTH - 2 * CHART_PADDING);
  };
  const yFor = (value: number) =>
    CHART_HEIGHT - CHART_PADDING - (value / 100) * (CHART_HEIGHT - 2 * CHART_PADDING);

  return (
    <div className="flex flex-col gap-3">
      <svg width={CHART_WIDTH} height={CHART_HEIGHT} viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}>
        {SCORE_ORDER.map((scoreType) => {
          const points = history[scoreType];
          if (points.length === 0) return null;
          const path = points
            .map((p, i) => `${i === 0 ? "M" : "L"} ${xFor(p.snapshot_date)},${yFor(p.value)}`)
            .join(" ");
          return (
            <g key={scoreType}>
              <path d={path} fill="none" stroke={LINE_COLORS[scoreType]} strokeWidth={2} />
              {scoreType === "health" &&
                points.map((p) => (
                  <circle
                    key={p.snapshot_date}
                    cx={xFor(p.snapshot_date)}
                    cy={yFor(p.value)}
                    r={3}
                    fill={LINE_COLORS.health}
                  />
                ))}
            </g>
          );
        })}
      </svg>
      <div className="flex flex-wrap gap-4 text-xs text-fg-muted">
        {SCORE_ORDER.map((scoreType) => (
          <span key={scoreType} className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: LINE_COLORS[scoreType] }}
            />
            {SCORE_LABELS[scoreType]}
            {scoreType === "health" && " (dots mark a new audit)"}
          </span>
        ))}
      </div>
    </div>
  );
}

function WeeklyPlanPanel({
  plan,
  onToggle,
}: {
  plan: WeeklyPlanResponse | null;
  onToggle: (index: number, completed: boolean) => void;
}) {
  if (!plan) {
    return (
      <EmptyState
        title="No plan yet this week"
        description="Your weekly plan is generated automatically every Monday, based on your latest audit and score history."
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-fg-muted">{plan.focus}</p>
      <p className="text-xs font-medium text-fg-muted">
        {plan.completed_count} of {plan.items.length} done this week
      </p>
      <ul className="flex flex-col gap-2">
        {plan.items.map((item, index) => (
          <li key={index} className="flex items-start gap-3 rounded-md border border-border p-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4"
              checked={item.completed}
              onChange={(e) => onToggle(index, e.target.checked)}
            />
            <div className="flex flex-1 flex-col gap-1">
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-medium ${item.completed ? "text-fg-muted line-through" : "text-fg"}`}
                >
                  {item.title}
                </span>
                <Badge>{item.estimated_minutes} min</Badge>
                <Badge variant="primary">+{item.expected_impact} pts</Badge>
              </div>
              <p className="text-xs text-fg-muted">{item.why_now}</p>
            </div>
          </li>
        ))}
      </ul>
      {plan.reflection && (
        <div className="mt-2 rounded-md border border-border bg-bg-subtle p-3 text-xs text-fg-muted">
          <p className="font-medium text-fg">Last week's retrospective</p>
          <p>
            Moved: {(plan.reflection.moved as string[] | undefined)?.join(", ") || "nothing yet"}
          </p>
          <p>
            Carried forward:{" "}
            {(plan.reflection.carry_forward as string[] | undefined)?.join(", ") || "nothing"}
          </p>
        </div>
      )}
    </div>
  );
}

function StreakStats({ consistency }: { consistency: GrowthScoreResponse }) {
  const streak = consistency.components.find((c) => c.name === "streak_length");
  const postsPerWeek = consistency.components.find((c) => c.name === "posts_per_week");
  if (!streak && !postsPerWeek) {
    return (
      <p className="text-sm text-fg-muted">
        Record posts on your content calendar to see streak stats here.
      </p>
    );
  }
  return (
    <div className="grid grid-cols-2 gap-4">
      {streak && (
        <div>
          <p className="text-2xl font-semibold text-fg">
            {String(streak.evidence.current_streak_weeks ?? "—")}
          </p>
          <p className="text-xs text-fg-muted">week streak</p>
        </div>
      )}
      {postsPerWeek && (
        <div>
          <p className="text-2xl font-semibold text-fg">
            {String(postsPerWeek.evidence.average_posts_per_week ?? "—")}
          </p>
          <p className="text-xs text-fg-muted">avg posts / week</p>
        </div>
      )}
    </div>
  );
}

function BeforeAfterPanel() {
  const today = new Date().toISOString().slice(0, 10);
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const [fromDate, setFromDate] = useState(thirtyDaysAgo);
  const [toDate, setToDate] = useState(today);
  const [result, setResult] = useState<BeforeAfterResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    apiFetch<BeforeAfterResponse>(
      `/api/v1/growth/before-after?from_date=${fromDate}&to_date=${toDate}`,
    )
      .then(setResult)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load."))
      .finally(() => setLoading(false));
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-fg-muted">
          From
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="rounded-md border border-border bg-bg px-2 py-1 text-sm text-fg"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-fg-muted">
          To
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="rounded-md border border-border bg-bg px-2 py-1 text-sm text-fg"
          />
        </label>
        <Button size="sm" onClick={load} loading={loading}>
          Compare
        </Button>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {result && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {result.score_deltas.map((d) => (
              <div key={d.score_type} className="rounded-md border border-border p-3">
                <p className="text-xs uppercase tracking-wide text-fg-muted">
                  {SCORE_LABELS[d.score_type as keyof GrowthScoresResponse] ?? d.score_type}
                </p>
                {d.from_value !== null && d.to_value !== null ? (
                  <p className="text-lg font-semibold text-fg">
                    {d.from_value} → {d.to_value}{" "}
                    <span className={d.delta && d.delta > 0 ? "text-success" : "text-fg-muted"}>
                      ({d.delta && d.delta > 0 ? "+" : ""}
                      {d.delta})
                    </span>
                  </p>
                ) : (
                  <p className="text-sm text-fg-muted">no data</p>
                )}
              </div>
            ))}
          </div>

          <div>
            <p className="mb-1 text-xs font-medium text-fg-muted">
              What happened in between ({result.tool_runs.length} tool run
              {result.tool_runs.length === 1 ? "" : "s"}, {result.profile_edits.length} profile edit
              {result.profile_edits.length === 1 ? "" : "s"})
            </p>
            {result.tool_runs.length === 0 && result.profile_edits.length === 0 ? (
              <p className="text-sm text-fg-muted">No tool runs or profile edits in this window.</p>
            ) : (
              <ul className="flex flex-col gap-1 text-sm text-fg-muted">
                {result.profile_edits.map((edit) => (
                  <li key={`edit-${edit.version}`}>
                    Profile edited (version {edit.version}, via {edit.source}) --{" "}
                    {new Date(edit.created_at).toLocaleDateString()}
                  </li>
                ))}
                {result.tool_runs.map((run, index) => (
                  <li key={`run-${index}`}>
                    Ran {run.tool_id} -- {new Date(run.created_at).toLocaleDateString()}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ToolDetail({ toolId }: { toolId: string }) {
  return (
    <div className="flex flex-col gap-4">
      <Link to="/growth" className="text-sm text-fg-muted hover:text-fg">
        ← Back to Growth Hub
      </Link>
      <ToolRunner key={toolId} toolId={toolId} />
    </div>
  );
}

function GrowthHubOverview() {
  const { push } = useToast();
  const [scores, setScores] = useState<GrowthScoresResponse | null>(null);
  const [history, setHistory] = useState<GrowthScoreHistoryResponse | null>(null);
  const [plan, setPlan] = useState<WeeklyPlanResponse | null>(null);
  const [goal, setGoal] = useState<GrowthGoalResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<GrowthScoresResponse>("/api/v1/growth/scores")
      .then(setScores)
      .catch(() => {
        setLoadError("Couldn't load your Growth Hub scores.");
      });
    apiFetch<GrowthScoreHistoryResponse>("/api/v1/growth/scores/history").then(setHistory);
    apiFetch<WeeklyPlanResponse>("/api/v1/growth/plan")
      .then(setPlan)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setPlan(null);
      });
    apiFetch<GrowthGoalResponse>("/api/v1/growth/goal")
      .then(setGoal)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setGoal(null);
      });
  }, []);

  const handleToggleItem = (index: number, completed: boolean) => {
    if (!plan) return;
    apiFetch<WeeklyPlanResponse>(`/api/v1/growth/plan/${plan.id}/items/${index}`, {
      method: "PATCH",
      body: { completed },
    })
      .then(setPlan)
      .catch(() => push({ title: "Couldn't update that item.", variant: "danger" }));
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-fg">Growth Hub</h1>
          <p className="text-sm text-fg-muted">
            Track real progress across four scores, grounded in your own data -- never scraped,
            never fabricated.
          </p>
        </div>
        <Link to="/growth/coach">
          <Button variant="secondary" size="sm">
            Talk to the Growth Coach
          </Button>
        </Link>
      </div>

      {loadError && <p className="text-sm text-danger">{loadError}</p>}

      {!scores ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : (
        <ScoresRow scores={scores} />
      )}

      {goal && (
        <Card className="p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-fg-muted">Current goal</p>
          <p className="text-sm text-fg">
            {goal.goal_type}
            {goal.target_role ? ` -- ${goal.target_role}` : ""} ({goal.horizon_weeks} weeks)
          </p>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>6-month trend</CardTitle>
          <CardDescription>Every line is your own recorded score history.</CardDescription>
        </CardHeader>
        {history ? <TrendChart history={history} /> : <Skeleton className="h-40 w-full" />}
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>This week's plan</CardTitle>
            <CardDescription>Generated every Monday from your latest audit.</CardDescription>
          </CardHeader>
          <WeeklyPlanPanel plan={plan} onToggle={handleToggleItem} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Consistency streak</CardTitle>
            <CardDescription>From your Consistency Score's own components.</CardDescription>
          </CardHeader>
          {scores ? (
            <StreakStats consistency={scores.consistency} />
          ) : (
            <Skeleton className="h-16 w-full" />
          )}
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Before / after</CardTitle>
          <CardDescription>
            Pick two dates to see which scores moved and what you actually did in between.
          </CardDescription>
        </CardHeader>
        <BeforeAfterPanel />
      </Card>
    </div>
  );
}

export function GrowthHubPage() {
  const { toolId } = useParams<{ toolId: string }>();
  return toolId ? <ToolDetail toolId={toolId} /> : <GrowthHubOverview />;
}
