/**
 * The content calendar: month, week, and list views over
 * `content_plans`, drag-to-reschedule with optimistic persistence and
 * rollback on failure, a keyboard-accessible "Move" alternative to
 * dragging, bulk-scheduling a cadence of ideas, recurring empty
 * placeholder slots, a reminder toggle, an explicit "Mark as posted"
 * action, and a 12-week consistency strip. Status is always shown as
 * colour plus a distinct shape (calendar-status.ts), never colour
 * alone.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import type {
  Cadence,
  ContentPlanResponse,
  ContentPlanStatus,
  ConsistencyWeek,
  PerformanceSummaryResponse,
} from "@/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/lib/toast-context";
import { ALL_STATUSES, STATUS_META } from "./calendar-status";
import {
  addDays,
  addMonths,
  eachDay,
  isSameDay,
  isSameMonth,
  monthGridRange,
  toISODate,
  weekRange,
} from "./calendar-dates";

type View = "month" | "week" | "list";

function PlanChip({
  plan,
  onOpen,
  onDragStart,
}: {
  plan: ContentPlanResponse;
  onOpen: () => void;
  onDragStart: (e: React.DragEvent) => void;
}) {
  const meta = STATUS_META[plan.status];
  return (
    <button
      type="button"
      draggable
      onDragStart={onDragStart}
      onClick={onOpen}
      className="flex w-full items-center gap-1.5 rounded-md border border-border bg-bg px-2 py-1 text-left text-xs hover:border-primary"
    >
      <span aria-hidden="true">{meta.glyph}</span>
      <span className="truncate text-fg">{plan.title || "(untitled)"}</span>
    </button>
  );
}

function ConsistencyStrip({ weeks }: { weeks: ConsistencyWeek[] | null }) {
  if (!weeks) return <Skeleton className="h-16 w-full" />;
  const max = Math.max(1, ...weeks.map((w) => w.posted_count));
  return (
    <div className="flex items-end gap-1.5" style={{ height: 64 }}>
      {weeks.map((week) => (
        <div key={week.week_start} className="flex flex-1 flex-col items-center gap-1">
          <div
            className="w-full rounded-t bg-primary/70"
            style={{ height: `${Math.max(4, (week.posted_count / max) * 48)}px` }}
            title={`${week.posted_count} posted the week of ${week.week_start}`}
          />
        </div>
      ))}
    </div>
  );
}

function WhatWorkedPanel({ summary }: { summary: PerformanceSummaryResponse | null }) {
  if (!summary) return <Skeleton className="h-16 w-full" />;
  if (!summary.sufficient_data) {
    return (
      <p className="text-sm text-fg-muted">
        Not enough data yet ({summary.total_data_points} of 5 posts with engagement numbers) --
        record performance on a few more posts to see what worked.
      </p>
    );
  }
  const max = Math.max(1, ...summary.by_content_type.map((row) => row.median_engagement));
  return (
    <div className="flex flex-col gap-2">
      {summary.by_content_type.map((row) => (
        <div key={row.content_type} className="flex items-center gap-2">
          <span className="w-24 shrink-0 text-sm capitalize text-fg">{row.content_type}</span>
          <div className="h-3 flex-1 rounded bg-bg-subtle">
            <div
              className="h-3 rounded bg-primary/70"
              style={{ width: `${(row.median_engagement / max) * 100}%` }}
            />
          </div>
          <span className="w-32 shrink-0 text-right text-xs text-fg-muted">
            {row.median_engagement} median ({row.sample_size} posts)
          </span>
        </div>
      ))}
    </div>
  );
}

export function Calendar() {
  const location = useLocation();
  const { push: pushToast } = useToast();

  const [view, setView] = useState<View>("month");
  const [anchor, setAnchor] = useState(new Date());
  const [plans, setPlans] = useState<ContentPlanResponse[] | null>(null);
  const [consistency, setConsistency] = useState<ConsistencyWeek[] | null>(null);
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummaryResponse | null>(
    null,
  );
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<ContentPlanResponse | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createDate, setCreateDate] = useState<Date>(new Date());
  const [createBody, setCreateBody] = useState("");
  const [bulkScheduleOpen, setBulkScheduleOpen] = useState(false);
  const [recurringOpen, setRecurringOpen] = useState(false);

  const range = useMemo(() => {
    if (view === "week") return weekRange(anchor);
    if (view === "list") return { start: addDays(anchor, -14), end: addDays(anchor, 45) };
    return monthGridRange(anchor);
  }, [view, anchor]);

  const loadPlans = useCallback(() => {
    setLoadError(null);
    apiFetch<ContentPlanResponse[]>(
      `/api/v1/content-plans?start=${toISODate(range.start)}&end=${toISODate(range.end)}`,
    )
      .then(setPlans)
      .catch((err) =>
        setLoadError(err instanceof ApiError ? err.message : "Couldn't load the calendar."),
      );
  }, [range.start, range.end]);

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  useEffect(() => {
    apiFetch<ConsistencyWeek[]>("/api/v1/content-plans/consistency")
      .then(setConsistency)
      .catch(() => {});
  }, []);

  const loadPerformanceSummary = useCallback(() => {
    apiFetch<PerformanceSummaryResponse>("/api/v1/content-plans/performance-summary")
      .then(setPerformanceSummary)
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadPerformanceSummary();
  }, [loadPerformanceSummary]);

  useEffect(() => {
    const draftBody = (location.state as { draftBody?: string } | null)?.draftBody;
    if (draftBody) {
      setCreateBody(draftBody);
      setCreateDate(new Date());
      setCreateOpen(true);
    }
  }, [location.state]);

  useEffect(() => {
    const ideaRows = (location.state as { ideaRows?: Record<string, unknown>[] } | null)?.ideaRows;
    if (!ideaRows || ideaRows.length === 0) return;
    Promise.all(
      ideaRows.map((row, index) =>
        apiFetch("/api/v1/content-plans", {
          method: "POST",
          body: {
            title: typeof row.title === "string" ? row.title : "Untitled idea",
            body_preview:
              typeof row.why === "string"
                ? row.why
                : typeof row.angle === "string"
                  ? row.angle
                  : "",
            planned_for: toISODate(addDays(new Date(), index)),
          },
        }),
      ),
    )
      .then(() => {
        pushToast({ title: `Added ${ideaRows.length} ideas to the calendar`, variant: "success" });
        loadPlans();
      })
      .catch(() => pushToast({ title: "Couldn't add all ideas", variant: "danger" }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  const plansByDate = useMemo(() => {
    const map = new Map<string, ContentPlanResponse[]>();
    for (const plan of plans ?? []) {
      const key = plan.planned_for;
      map.set(key, [...(map.get(key) ?? []), plan]);
    }
    return map;
  }, [plans]);

  async function reschedule(planId: string, newDate: Date) {
    const previous = plans;
    const iso = toISODate(newDate);
    setPlans((current) =>
      (current ?? []).map((p) => (p.id === planId ? { ...p, planned_for: iso } : p)),
    );
    try {
      await apiFetch<ContentPlanResponse>(`/api/v1/content-plans/${planId}/reschedule`, {
        method: "POST",
        body: { planned_for: iso },
      });
    } catch {
      setPlans(previous);
      pushToast({ title: "Couldn't reschedule -- reverted", variant: "danger" });
    }
  }

  async function handleCreate() {
    try {
      await apiFetch<ContentPlanResponse>("/api/v1/content-plans", {
        method: "POST",
        body: {
          title: createBody.split("\n")[0]?.slice(0, 80) || "Untitled",
          body_preview: createBody,
          planned_for: toISODate(createDate),
        },
      });
      setCreateOpen(false);
      setCreateBody("");
      loadPlans();
      pushToast({ title: "Added to calendar", variant: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof ApiError ? err.message : "Couldn't create this.",
        variant: "danger",
      });
    }
  }

  const days = eachDay(range.start, view === "list" ? range.start : range.end);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-fg">Content calendar</h1>
          <p className="text-sm text-fg-muted">
            Plan, schedule, and track what you post -- LinkSavvy never posts to LinkedIn for you.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => {
              setCreateDate(anchor);
              setCreateBody("");
              setCreateOpen(true);
            }}
          >
            New
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setRecurringOpen(true)}>
            Recurring slots
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setBulkScheduleOpen(true)}>
            Bulk-schedule ideas
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Consistency, last 12 weeks</CardTitle>
          <CardDescription>
            Posts per week, counted from when you marked them posted.
          </CardDescription>
        </CardHeader>
        <ConsistencyStrip weeks={consistency} />
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What worked</CardTitle>
          <CardDescription>
            Median engagement (reactions + comments + reposts) by post type.
          </CardDescription>
        </CardHeader>
        <WhatWorkedPanel summary={performanceSummary} />
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1">
          {(["month", "week", "list"] as View[]).map((v) => (
            <Button
              key={v}
              size="sm"
              variant={view === v ? "primary" : "secondary"}
              onClick={() => setView(v)}
            >
              {v[0]?.toUpperCase()}
              {v.slice(1)}
            </Button>
          ))}
        </div>
        {view !== "list" && (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                setAnchor((a) => (view === "week" ? addDays(a, -7) : addMonths(a, -1)))
              }
            >
              ← Prev
            </Button>
            <span className="text-sm text-fg-muted">
              {anchor.toLocaleDateString(undefined, { month: "long", year: "numeric" })}
            </span>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setAnchor((a) => (view === "week" ? addDays(a, 7) : addMonths(a, 1)))}
            >
              Next →
            </Button>
          </div>
        )}
      </div>

      {loadError && <p className="text-sm text-danger">{loadError}</p>}
      {!plans && !loadError && <Skeleton className="h-96 w-full" />}

      {plans && view !== "list" && (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-7">
          {days.map((day) => {
            const iso = toISODate(day);
            const dayPlans = plansByDate.get(iso) ?? [];
            const faded = view === "month" && !isSameMonth(day, anchor);
            return (
              <div
                key={iso}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  const planId = e.dataTransfer.getData("text/plain");
                  if (planId) void reschedule(planId, day);
                }}
                className={`flex min-h-[7rem] flex-col gap-1 rounded-md border border-border p-1.5 ${faded ? "bg-bg-subtle opacity-60" : "bg-card"}`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-medium ${isSameDay(day, new Date()) ? "text-primary" : "text-fg-muted"}`}
                  >
                    {day.getDate()}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setCreateDate(day);
                      setCreateBody("");
                      setCreateOpen(true);
                    }}
                    className="text-xs text-fg-muted hover:text-fg"
                    aria-label={`Add a post for ${iso}`}
                  >
                    +
                  </button>
                </div>
                {dayPlans.map((plan) => (
                  <PlanChip
                    key={plan.id}
                    plan={plan}
                    onOpen={() => setSelectedPlan(plan)}
                    onDragStart={(e) => e.dataTransfer.setData("text/plain", plan.id)}
                  />
                ))}
              </div>
            );
          })}
        </div>
      )}

      {plans && view === "list" && (
        <div className="flex flex-col gap-2">
          {[...plans]
            .sort((a, b) => a.planned_for.localeCompare(b.planned_for))
            .map((plan) => (
              <button
                key={plan.id}
                type="button"
                onClick={() => setSelectedPlan(plan)}
                className="flex items-center justify-between gap-2 rounded-md border border-border bg-card p-3 text-left hover:border-primary"
              >
                <div className="flex items-center gap-2">
                  <span aria-hidden="true">{STATUS_META[plan.status].glyph}</span>
                  <span className="text-sm text-fg">{plan.title || "(untitled)"}</span>
                </div>
                <span className="text-xs text-fg-muted">{plan.planned_for}</span>
              </button>
            ))}
          {plans.length === 0 && (
            <p className="text-sm text-fg-muted">Nothing planned in this range.</p>
          )}
        </div>
      )}

      <CreateModal
        open={createOpen}
        date={createDate}
        body={createBody}
        onBodyChange={setCreateBody}
        onDateChange={setCreateDate}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleCreate}
      />

      <PlanDetailModal
        plan={selectedPlan}
        onClose={() => setSelectedPlan(null)}
        onChanged={() => {
          setSelectedPlan(null);
          loadPlans();
          loadPerformanceSummary();
        }}
        onMove={(planId, date) => reschedule(planId, date)}
      />

      <RecurringSlotsModal
        open={recurringOpen}
        onClose={() => setRecurringOpen(false)}
        onCreated={() => {
          setRecurringOpen(false);
          loadPlans();
        }}
      />

      <BulkScheduleModal
        open={bulkScheduleOpen}
        ideas={(plans ?? []).filter((p) => p.status === "idea")}
        onClose={() => setBulkScheduleOpen(false)}
        onScheduled={() => {
          setBulkScheduleOpen(false);
          loadPlans();
        }}
      />
    </div>
  );
}

function CreateModal({
  open,
  date,
  body,
  onBodyChange,
  onDateChange,
  onClose,
  onSubmit,
}: {
  open: boolean;
  date: Date;
  body: string;
  onBodyChange: (v: string) => void;
  onDateChange: (d: Date) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  return (
    <Modal open={open} onClose={onClose} title="Add to calendar">
      <div className="flex flex-col gap-3">
        <input
          type="date"
          value={toISODate(date)}
          onChange={(e) => onDateChange(new Date(`${e.target.value}T00:00:00`))}
          className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
        />
        <textarea
          value={body}
          onChange={(e) => onBodyChange(e.target.value)}
          rows={5}
          placeholder="Title or draft text"
          className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg"
        />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onSubmit}>Add</Button>
        </div>
      </div>
    </Modal>
  );
}

function PlanDetailModal({
  plan,
  onClose,
  onChanged,
  onMove,
}: {
  plan: ContentPlanResponse | null;
  onClose: () => void;
  onChanged: () => void;
  onMove: (planId: string, date: Date) => void;
}) {
  const { push: pushToast } = useToast();
  const [reminderAt, setReminderAt] = useState("");
  const [postedOpen, setPostedOpen] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [impressions, setImpressions] = useState("");
  const [perf, setPerf] = useState({
    impressions: "",
    reactions: "",
    comments: "",
    reposts: "",
    profile_views: "",
  });

  useEffect(() => {
    setReminderAt("");
    setPostedOpen(false);
    setLinkedinUrl("");
    setImpressions("");
    setPerf({ impressions: "", reactions: "", comments: "", reposts: "", profile_views: "" });
  }, [plan?.id]);

  if (!plan) return null;

  async function setStatus(status: ContentPlanStatus) {
    if (!plan) return;
    try {
      await apiFetch(`/api/v1/content-plans/${plan.id}`, { method: "PATCH", body: { status } });
      onChanged();
    } catch {
      pushToast({ title: "Couldn't update status", variant: "danger" });
    }
  }

  async function saveReminder() {
    if (!plan) return;
    try {
      await apiFetch(`/api/v1/content-plans/${plan.id}/reminder`, {
        method: "POST",
        body: { reminder_at: reminderAt ? new Date(reminderAt).toISOString() : null },
      });
      pushToast({ title: "Reminder set", variant: "success" });
      onChanged();
    } catch {
      pushToast({ title: "Couldn't set reminder", variant: "danger" });
    }
  }

  async function savePerformance() {
    if (!plan) return;
    const numbers = Object.fromEntries(
      Object.entries(perf)
        .filter(([, v]) => v.trim() !== "")
        .map(([k, v]) => [k, Number(v)]),
    );
    if (Object.keys(numbers).length === 0) return;
    try {
      await apiFetch(`/api/v1/content-plans/${plan.id}/performance`, {
        method: "POST",
        body: numbers,
      });
      pushToast({ title: "Performance recorded", variant: "success" });
      onChanged();
    } catch {
      pushToast({ title: "Couldn't record performance", variant: "danger" });
    }
  }

  async function confirmPosted() {
    if (!plan) return;
    try {
      await apiFetch(`/api/v1/content-plans/${plan.id}/mark-posted`, {
        method: "POST",
        body: {
          linkedin_url: linkedinUrl.trim() || null,
          performance: impressions ? { impressions: Number(impressions) } : null,
        },
      });
      pushToast({ title: "Marked as posted", variant: "success" });
      onChanged();
    } catch {
      pushToast({ title: "Couldn't record this", variant: "danger" });
    }
  }

  return (
    <Modal open onClose={onClose} title={plan.title || "Untitled"}>
      <div className="flex flex-col gap-4">
        <p className="whitespace-pre-wrap text-sm text-fg-muted">
          {plan.body_preview || "(no draft text yet)"}
        </p>

        <div>
          <p className="mb-1 text-xs font-medium uppercase text-fg-muted">Status</p>
          <div className="flex flex-wrap gap-1.5">
            {ALL_STATUSES.map((status) => (
              <Badge
                key={status}
                variant={plan.status === status ? STATUS_META[status].badgeVariant : "default"}
                className="cursor-pointer"
              >
                <button type="button" onClick={() => setStatus(status)}>
                  {STATUS_META[status].glyph} {STATUS_META[status].label}
                </button>
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-1 text-xs font-medium uppercase text-fg-muted">
            Move (keyboard-accessible alternative to dragging)
          </p>
          <input
            type="date"
            defaultValue={plan.planned_for}
            onChange={(e) =>
              e.target.value && onMove(plan.id, new Date(`${e.target.value}T00:00:00`))
            }
            className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
          />
        </div>

        <div>
          <p className="mb-1 text-xs font-medium uppercase text-fg-muted">Reminder</p>
          <div className="flex gap-2">
            <input
              type="datetime-local"
              value={reminderAt}
              onChange={(e) => setReminderAt(e.target.value)}
              className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
            />
            <Button size="sm" variant="secondary" onClick={saveReminder}>
              Set
            </Button>
          </div>
        </div>

        {plan.status !== "posted" && (
          <Button variant="secondary" onClick={() => setPostedOpen(true)}>
            Mark as posted
          </Button>
        )}

        {postedOpen && (
          <div className="flex flex-col gap-2 rounded-md border border-border p-3">
            <input
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="LinkedIn post URL (optional)"
              className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
            />
            <input
              value={impressions}
              onChange={(e) => setImpressions(e.target.value)}
              placeholder="Impressions (optional)"
              inputMode="numeric"
              className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
            />
            <Button onClick={confirmPosted}>Confirm</Button>
          </div>
        )}

        <div>
          <p className="mb-1 text-xs font-medium uppercase text-fg-muted">Record performance</p>
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(perf) as (keyof typeof perf)[]).map((field) => (
              <input
                key={field}
                value={perf[field]}
                onChange={(e) => setPerf({ ...perf, [field]: e.target.value })}
                placeholder={field.replace("_", " ")}
                inputMode="numeric"
                className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
              />
            ))}
          </div>
          <Button size="sm" variant="secondary" className="mt-2" onClick={savePerformance}>
            Save numbers
          </Button>
        </div>
      </div>
    </Modal>
  );
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function RecurringSlotsModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const { push: pushToast } = useToast();
  const [days, setDays] = useState<number[]>([1, 3]);
  const [startDate, setStartDate] = useState(toISODate(new Date()));
  const [weeks, setWeeks] = useState(6);

  async function submit() {
    const cadence: Cadence = { days_of_week: days, start_date: startDate, weeks };
    try {
      await apiFetch("/api/v1/content-plans/recurring-slots", {
        method: "POST",
        body: { cadence },
      });
      onCreated();
    } catch {
      pushToast({ title: "Couldn't create recurring slots", variant: "danger" });
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Recurring slots">
      <CadenceFields
        days={days}
        setDays={setDays}
        startDate={startDate}
        setStartDate={setStartDate}
        weeks={weeks}
        setWeeks={setWeeks}
      />
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={submit}>Create empty slots</Button>
      </div>
    </Modal>
  );
}

function BulkScheduleModal({
  open,
  ideas,
  onClose,
  onScheduled,
}: {
  open: boolean;
  ideas: ContentPlanResponse[];
  onClose: () => void;
  onScheduled: () => void;
}) {
  const { push: pushToast } = useToast();
  const [days, setDays] = useState<number[]>([1, 3]);
  const [startDate, setStartDate] = useState(toISODate(new Date()));
  const [weeks, setWeeks] = useState(6);
  const [selected, setSelected] = useState<string[]>([]);

  async function submit() {
    if (selected.length === 0) {
      pushToast({ title: "Pick at least one idea", variant: "danger" });
      return;
    }
    const cadence: Cadence = { days_of_week: days, start_date: startDate, weeks };
    try {
      await apiFetch("/api/v1/content-plans/bulk-schedule", {
        method: "POST",
        body: { cadence, plan_ids: selected },
      });
      onScheduled();
    } catch {
      pushToast({ title: "Couldn't bulk-schedule", variant: "danger" });
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Bulk-schedule ideas">
      <CadenceFields
        days={days}
        setDays={setDays}
        startDate={startDate}
        setStartDate={setStartDate}
        weeks={weeks}
        setWeeks={setWeeks}
      />
      <div className="mt-3">
        <p className="mb-1 text-xs font-medium uppercase text-fg-muted">
          Ideas in view ({ideas.length})
        </p>
        <div className="flex max-h-40 flex-col gap-1 overflow-y-auto">
          {ideas.map((idea) => (
            <label key={idea.id} className="flex items-center gap-2 text-sm text-fg">
              <input
                type="checkbox"
                checked={selected.includes(idea.id)}
                onChange={(e) =>
                  setSelected((current) =>
                    e.target.checked
                      ? [...current, idea.id]
                      : current.filter((id) => id !== idea.id),
                  )
                }
              />
              {idea.title || "(untitled)"}
            </label>
          ))}
          {ideas.length === 0 && (
            <p className="text-sm text-fg-muted">No ideas in the current view.</p>
          )}
        </div>
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={submit}>Schedule</Button>
      </div>
    </Modal>
  );
}

function CadenceFields({
  days,
  setDays,
  startDate,
  setStartDate,
  weeks,
  setWeeks,
}: {
  days: number[];
  setDays: (d: number[]) => void;
  startDate: string;
  setStartDate: (d: string) => void;
  weeks: number;
  setWeeks: (w: number) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="mb-1 text-xs font-medium uppercase text-fg-muted">Days</p>
        <div className="flex flex-wrap gap-1.5">
          {DAY_LABELS.map((label, index) => (
            <Button
              key={label}
              size="sm"
              variant={days.includes(index) ? "primary" : "secondary"}
              onClick={() =>
                setDays(days.includes(index) ? days.filter((d) => d !== index) : [...days, index])
              }
            >
              {label}
            </Button>
          ))}
        </div>
      </div>
      <div>
        <p className="mb-1 text-xs font-medium uppercase text-fg-muted">Starting</p>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
        />
      </div>
      <div>
        <p className="mb-1 text-xs font-medium uppercase text-fg-muted">For how many weeks</p>
        <input
          type="number"
          min={1}
          max={52}
          value={weeks}
          onChange={(e) => setWeeks(Number(e.target.value))}
          className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
        />
      </div>
    </div>
  );
}
