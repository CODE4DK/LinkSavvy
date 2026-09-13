/**
 * Career Hub: three panels -- Resumes, Job Descriptions, Tools -- plus
 * the generic ToolRunner at `/career/:toolId` for the seven career.*
 * tools, exactly like the other hubs. Matching a resume against a job
 * description is reachable in two clicks from either panel: open a
 * resume or JD's "Match against..." picker, then click the other side.
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type {
  JobDescriptionResponse,
  ResumeDocument,
  ResumeMatchResponse,
  ResumeParseResponse,
  ResumeResponse,
  ToolSummary,
} from "@linksavvy/contracts";
import { resumeDocumentSchema } from "@linksavvy/contracts";
import { apiFetch, ApiError, getAccessToken } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ToolRunner } from "@/tools/ToolRunner";

type Tab = "resumes" | "job-descriptions" | "tools";

interface ParsedDraft {
  draft: ResumeDocument;
  warnings: string[];
}

function parseDraftResponse(response: ResumeParseResponse): ParsedDraft {
  return {
    draft: resumeDocumentSchema.parse(response.draft) as ResumeDocument,
    warnings: response.warnings,
  };
}

async function downloadBlob(path: string, filename: string) {
  const token = getAccessToken();
  const response = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) throw new Error("Export failed");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function MatchResult({ match }: { match: ResumeMatchResponse | undefined }) {
  if (!match) return null;
  return (
    <div className="mt-3 rounded-md border border-border bg-bg p-3">
      <div className="flex items-center gap-2">
        <Badge variant="primary">{match.overall_match}% match</Badge>
      </div>
      <dl className="mt-2 flex flex-col gap-1 text-xs text-fg-muted">
        {(match.component_scores as Record<string, unknown>[]).map((component, index) => (
          <div key={index} className="flex justify-between gap-2">
            <dt>{String(component.component)}</dt>
            <dd>
              {String(component.score)} × {String(component.weight)} ={" "}
              {String(component.contribution)}
            </dd>
          </div>
        ))}
      </dl>
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <p className="text-xs font-semibold text-fg">Matched</p>
          <ul className="mt-1 flex flex-col gap-1 text-xs text-fg-muted">
            {(match.matched as Record<string, unknown>[]).map((item, index) => (
              <li key={index}>{String(item.requirement)}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-fg">Missing</p>
          <ul className="mt-1 flex flex-col gap-1 text-xs text-fg-muted">
            {(match.missing as Record<string, unknown>[]).map((item, index) => (
              <li key={index}>
                {String(item.requirement)} {item.learnable ? "(learnable)" : "(hard blocker)"}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-fg">Transferable</p>
          <ul className="mt-1 flex flex-col gap-1 text-xs text-fg-muted">
            {(match.transferable as Record<string, unknown>[]).map((item, index) => (
              <li key={index}>{String(item.requirement)}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function MatchPicker({
  options,
  onPick,
  emptyLabel,
}: {
  options: { id: string; label: string }[];
  onPick: (id: string) => void;
  emptyLabel: string;
}) {
  if (options.length === 0) {
    return <p className="mt-2 text-xs text-fg-muted">{emptyLabel}</p>;
  }
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {options.map((option) => (
        <Button key={option.id} variant="secondary" size="sm" onClick={() => onPick(option.id)}>
          {option.label}
        </Button>
      ))}
    </div>
  );
}

function ResumeReviewForm({
  draft,
  warnings,
  onCommit,
  onCancel,
}: {
  draft: ResumeDocument;
  warnings: string[];
  onCommit: (title: string, document: ResumeDocument) => Promise<void>;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(draft.contact?.full_name ?? "My Resume");
  const [json, setJson] = useState(JSON.stringify(draft, null, 2));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    setError(null);
    let parsedDocument: ResumeDocument;
    try {
      parsedDocument = resumeDocumentSchema.parse(JSON.parse(json)) as ResumeDocument;
    } catch {
      setError("That doesn't look like valid resume JSON -- fix it or cancel and try again.");
      return;
    }
    setSaving(true);
    try {
      await onCommit(title.trim() || "My Resume", parsedDocument);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review before saving</CardTitle>
        <CardDescription>
          Check what was parsed and correct anything wrong before this becomes a saved resume.
        </CardDescription>
      </CardHeader>
      {warnings.length > 0 && (
        <ul className="mb-3 flex flex-col gap-1 text-sm text-warning">
          {warnings.map((warning, index) => (
            <li key={index}>{warning}</li>
          ))}
        </ul>
      )}
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Resume title"
        className="mb-3 h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
      />
      <textarea
        rows={16}
        value={json}
        onChange={(e) => setJson(e.target.value)}
        className="w-full rounded-md border border-border bg-bg p-3 font-mono text-xs text-fg"
      />
      {error && (
        <p role="alert" className="mt-2 text-sm text-danger">
          {error}
        </p>
      )}
      <div className="mt-3 flex gap-2">
        <Button onClick={submit} loading={saving}>
          Save resume
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </Card>
  );
}

function ResumesPanel({
  jobDescriptions,
  onResumesChanged,
}: {
  jobDescriptions: JobDescriptionResponse[];
  onResumesChanged: () => void;
}) {
  const { push: pushToast } = useToast();
  const [resumes, setResumes] = useState<ResumeResponse[] | null>(null);
  const [pendingDraft, setPendingDraft] = useState<ParsedDraft | null>(null);
  const [matchingResumeId, setMatchingResumeId] = useState<string | null>(null);
  const [matches, setMatches] = useState<Record<string, ResumeMatchResponse>>({});

  const load = () => {
    apiFetch<ResumeResponse[]>("/api/v1/career/resumes")
      .then(setResumes)
      .catch(() => setResumes([]));
  };

  useEffect(load, []);

  const pasteResume = async () => {
    const text = window.prompt("Paste your resume text:");
    if (!text?.trim()) return;
    try {
      const response = await apiFetch<ResumeParseResponse>("/api/v1/career/resumes/parse/paste", {
        method: "POST",
        body: { text },
      });
      setPendingDraft(parseDraftResponse(response));
    } catch (err) {
      pushToast({
        title: "Could not parse that text",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  const uploadResume = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await apiFetch<ResumeParseResponse>(
        "/api/v1/career/resumes/parse/upload",
        { method: "POST", body: formData },
      );
      setPendingDraft(parseDraftResponse(response));
    } catch (err) {
      pushToast({
        title: "Could not read that file",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  const importFromProfile = async () => {
    try {
      const response = await apiFetch<ResumeParseResponse>("/api/v1/career/resumes/from-profile", {
        method: "POST",
      });
      setPendingDraft(parseDraftResponse(response));
    } catch (err) {
      pushToast({
        title: "Could not import from your profile",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  const commitDraft = async (title: string, document: ResumeDocument) => {
    try {
      await apiFetch<ResumeResponse>("/api/v1/career/resumes", {
        method: "POST",
        body: { title, source: document.source, document },
      });
      setPendingDraft(null);
      load();
      onResumesChanged();
      pushToast({ title: "Resume saved", variant: "success" });
    } catch (err) {
      pushToast({
        title: "Could not save this resume",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  const activate = async (id: string) => {
    await apiFetch(`/api/v1/career/resumes/${id}/activate`, { method: "POST" });
    load();
  };

  const remove = async (id: string) => {
    await apiFetch(`/api/v1/career/resumes/${id}`, { method: "DELETE" });
    load();
    onResumesChanged();
  };

  const matchAgainst = async (resumeId: string, jobDescriptionId: string) => {
    try {
      const match = await apiFetch<ResumeMatchResponse>("/api/v1/career/matches", {
        method: "POST",
        body: { resume_id: resumeId, job_description_id: jobDescriptionId },
      });
      setMatches((prev) => ({ ...prev, [resumeId]: match }));
      setMatchingResumeId(null);
    } catch (err) {
      pushToast({
        title: "Could not run the match",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  if (pendingDraft) {
    return (
      <ResumeReviewForm
        draft={pendingDraft.draft}
        warnings={pendingDraft.warnings}
        onCommit={commitDraft}
        onCancel={() => setPendingDraft(null)}
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        <Button onClick={pasteResume}>Paste resume text</Button>
        <label className="cursor-pointer">
          <span className="inline-flex h-9 items-center rounded-md border border-border bg-bg px-3 text-sm font-medium text-fg hover:bg-bg-subtle">
            Upload PDF/DOCX
          </span>
          <input
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void uploadResume(file);
              e.target.value = "";
            }}
          />
        </label>
        <Button variant="secondary" onClick={importFromProfile}>
          Import from profile
        </Button>
      </div>

      {resumes === null && <Skeleton className="h-24 w-full" />}
      {resumes && resumes.length === 0 && (
        <EmptyState
          title="No resumes yet"
          description="Paste your resume, upload a file, or import from your LinkedIn profile to get started."
        />
      )}
      {resumes?.map((resume) => (
        <Card key={resume.id}>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>{resume.title}</CardTitle>
              <div className="flex gap-1.5">
                {resume.is_active && <Badge variant="success">active</Badge>}
                <Badge>v{resume.version}</Badge>
              </div>
            </div>
            <CardDescription>{resume.source}</CardDescription>
          </CardHeader>
          <div className="flex flex-wrap gap-2">
            {!resume.is_active && (
              <Button variant="secondary" size="sm" onClick={() => activate(resume.id)}>
                Set active
              </Button>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                downloadBlob(
                  `/api/v1/career/resumes/${resume.id}/export/pdf`,
                  `${resume.title}.pdf`,
                )
              }
            >
              Export PDF
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                downloadBlob(
                  `/api/v1/career/resumes/${resume.id}/export/docx`,
                  `${resume.title}.docx`,
                )
              }
            >
              Export DOCX
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                setMatchingResumeId(matchingResumeId === resume.id ? null : resume.id)
              }
            >
              Match against a JD
            </Button>
            <Button variant="ghost" size="sm" onClick={() => remove(resume.id)}>
              Delete
            </Button>
          </div>
          {matchingResumeId === resume.id && (
            <MatchPicker
              options={jobDescriptions.map((jd) => ({ id: jd.id, label: jd.title }))}
              onPick={(jdId) => matchAgainst(resume.id, jdId)}
              emptyLabel="Save a job description first to match against it."
            />
          )}
          <MatchResult match={matches[resume.id]} />
        </Card>
      ))}
    </div>
  );
}

function JobDescriptionsPanel({
  resumes,
  jobDescriptions,
  onJobDescriptionsChanged,
}: {
  resumes: ResumeResponse[];
  jobDescriptions: JobDescriptionResponse[] | null;
  onJobDescriptionsChanged: () => void;
}) {
  const { push: pushToast } = useToast();
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [rawText, setRawText] = useState("");
  const [matchingJdId, setMatchingJdId] = useState<string | null>(null);
  const [matches, setMatches] = useState<Record<string, ResumeMatchResponse>>({});

  const addJobDescription = async () => {
    if (!rawText.trim()) return;
    try {
      await apiFetch("/api/v1/career/job-descriptions", {
        method: "POST",
        body: { title: title.trim() || "Untitled role", company: company.trim() || null, raw_text: rawText },
      });
      setAdding(false);
      setTitle("");
      setCompany("");
      setRawText("");
      onJobDescriptionsChanged();
    } catch (err) {
      pushToast({
        title: "Could not save that job description",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  const remove = async (id: string) => {
    await apiFetch(`/api/v1/career/job-descriptions/${id}`, { method: "DELETE" });
    onJobDescriptionsChanged();
  };

  const matchAgainst = async (jobDescriptionId: string, resumeId: string) => {
    try {
      const match = await apiFetch<ResumeMatchResponse>("/api/v1/career/matches", {
        method: "POST",
        body: { resume_id: resumeId, job_description_id: jobDescriptionId },
      });
      setMatches((prev) => ({ ...prev, [jobDescriptionId]: match }));
      setMatchingJdId(null);
    } catch (err) {
      pushToast({
        title: "Could not run the match",
        description: err instanceof ApiError ? err.message : undefined,
        variant: "danger",
      });
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {!adding && <Button onClick={() => setAdding(true)}>Add by paste</Button>}
      {adding && (
        <Card>
          <CardHeader>
            <CardTitle>Add a job description</CardTitle>
          </CardHeader>
          <div className="flex flex-col gap-2">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Job title"
              className="h-9 rounded-md border border-border bg-bg px-3 text-sm text-fg"
            />
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company (optional)"
              className="h-9 rounded-md border border-border bg-bg px-3 text-sm text-fg"
            />
            <textarea
              rows={10}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste the job description here"
              className="rounded-md border border-border bg-bg p-3 text-sm text-fg"
            />
            <div className="flex gap-2">
              <Button onClick={addJobDescription}>Save</Button>
              <Button variant="ghost" onClick={() => setAdding(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {jobDescriptions === null && <Skeleton className="h-24 w-full" />}
      {jobDescriptions && jobDescriptions.length === 0 && !adding && (
        <EmptyState
          title="No job descriptions saved yet"
          description="Paste a job posting to build a library you can match resumes against."
        />
      )}
      {jobDescriptions?.map((jd) => (
        <Card key={jd.id}>
          <CardHeader>
            <CardTitle>{jd.title}</CardTitle>
            <CardDescription>{jd.company ?? "No company given"}</CardDescription>
          </CardHeader>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setMatchingJdId(matchingJdId === jd.id ? null : jd.id)}
            >
              Match against a resume
            </Button>
            <Button variant="ghost" size="sm" onClick={() => remove(jd.id)}>
              Delete
            </Button>
          </div>
          {matchingJdId === jd.id && (
            <MatchPicker
              options={resumes.map((resume) => ({ id: resume.id, label: resume.title }))}
              onPick={(resumeId) => matchAgainst(jd.id, resumeId)}
              emptyLabel="Save a resume first to match against it."
            />
          )}
          <MatchResult match={matches[jd.id]} />
        </Card>
      ))}
    </div>
  );
}

function ToolsPanel() {
  const [tools, setTools] = useState<ToolSummary[] | null>(null);

  useEffect(() => {
    apiFetch<ToolSummary[]>("/api/v1/tools?hub=career")
      .then(setTools)
      .catch(() => setTools([]));
  }, []);

  if (!tools) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 7 }, (_, index) => (
          <Skeleton key={index} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {tools.map((tool) => (
        <Link key={tool.id} to={`/career/${tool.id}`}>
          <Card className="h-full transition-colors hover:border-primary">
            <CardHeader>
              <CardTitle>{tool.name}</CardTitle>
              <CardDescription>{tool.short_description}</CardDescription>
            </CardHeader>
            <div className="flex flex-wrap gap-1.5">
              <Badge>{tool.result_renderer}</Badge>
              {tool.min_plan !== "free" && <Badge variant="primary">{tool.min_plan}</Badge>}
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function CareerHubHome() {
  const [tab, setTab] = useState<Tab>("resumes");
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [jobDescriptions, setJobDescriptions] = useState<JobDescriptionResponse[] | null>(null);

  const loadResumes = () => {
    apiFetch<ResumeResponse[]>("/api/v1/career/resumes")
      .then(setResumes)
      .catch(() => setResumes([]));
  };
  const loadJobDescriptions = () => {
    apiFetch<JobDescriptionResponse[]>("/api/v1/career/job-descriptions")
      .then(setJobDescriptions)
      .catch(() => setJobDescriptions([]));
  };

  useEffect(() => {
    loadResumes();
    loadJobDescriptions();
  }, []);

  const TABS: { id: Tab; label: string }[] = [
    { id: "resumes", label: "Resumes" },
    { id: "job-descriptions", label: "Job Descriptions" },
    { id: "tools", label: "Tools" },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Career Hub</h1>
        <p className="text-sm text-fg-muted">
          Manage resumes and job descriptions, and use AI tools to analyse, match, and prepare.
        </p>
      </div>

      <div className="flex gap-2 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab === t.id
                ? "border-primary text-fg"
                : "border-transparent text-fg-muted hover:text-fg"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "resumes" && (
        <ResumesPanel
          jobDescriptions={jobDescriptions ?? []}
          onResumesChanged={loadResumes}
        />
      )}
      {tab === "job-descriptions" && (
        <JobDescriptionsPanel
          resumes={resumes}
          jobDescriptions={jobDescriptions}
          onJobDescriptionsChanged={loadJobDescriptions}
        />
      )}
      {tab === "tools" && <ToolsPanel />}
    </div>
  );
}

function ToolDetail({ toolId }: { toolId: string }) {
  return (
    <div className="flex flex-col gap-4">
      <Link to="/career" className="text-sm text-fg-muted hover:text-fg">
        ← Back to Career Hub
      </Link>
      <ToolRunner key={toolId} toolId={toolId} />
    </div>
  );
}

export function CareerHubPage() {
  const { toolId } = useParams<{ toolId: string }>();
  return toolId ? <ToolDetail toolId={toolId} /> : <CareerHubHome />;
}
