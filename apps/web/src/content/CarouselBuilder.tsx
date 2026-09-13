/**
 * Slide-by-slide carousel editor: reorder slides, edit headline/body
 * per slide, pick one of three layout templates, then export a PDF
 * (selectable text, ready to upload as a LinkedIn document post) or a
 * ZIP of per-slide PNGs. The carousel is saved as a regular Asset with
 * its structure intact (app/content/carousel_service.py), so it can be
 * reopened and edited again later.
 */

import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import type { CarouselData, CarouselResponse, CarouselSlide } from "@linksavvy/contracts";
import { apiFetch, ApiError, getAccessToken } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/lib/toast-context";

const TEMPLATES: { id: CarouselData["template"]; label: string }[] = [
  { id: "clean", label: "Clean" },
  { id: "bold", label: "Bold" },
  { id: "minimal", label: "Minimal" },
];

function blankSlide(): CarouselSlide {
  return { headline: "", body: "", visual_note: "" };
}

function blankCarousel(): CarouselData {
  return {
    template: "clean",
    cover: { headline: "", subhead: "" },
    slides: [blankSlide()],
    closing: { cta: "" },
    caption: "",
  };
}

/** A Carousel Generator tool run's raw output already matches this
 * shape (cover/slides/closing/caption) -- only `template` is missing,
 * since the AI tool doesn't pick a layout. */
function fromToolOutput(output: unknown): CarouselData | null {
  if (typeof output !== "object" || output === null) return null;
  const record = output as Record<string, unknown>;
  if (!Array.isArray(record.slides) || typeof record.cover !== "object") return null;
  return { ...blankCarousel(), ...(record as object) } as CarouselData;
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

export function CarouselBuilder() {
  const { carouselId } = useParams<{ carouselId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { push: pushToast } = useToast();

  const [title, setTitle] = useState("Untitled carousel");
  const [data, setData] = useState<CarouselData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | null>(
    carouselId && carouselId !== "new" ? carouselId : null,
  );
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState<"pdf" | "png" | null>(null);
  const justSavedRef = useRef(false);

  useEffect(() => {
    if (justSavedRef.current) {
      justSavedRef.current = false;
      return;
    }
    if (savedId) {
      apiFetch<CarouselResponse>(`/api/v1/carousels/${savedId}`)
        .then((carousel) => {
          setTitle(carousel.title);
          setData(carousel.data);
        })
        .catch((err) =>
          setLoadError(err instanceof ApiError ? err.message : "Couldn't load this carousel."),
        );
      return;
    }
    const fromOutput = (location.state as { fromToolOutput?: unknown } | null)?.fromToolOutput;
    const initial = fromOutput ? fromToolOutput(fromOutput) : null;
    setData(initial ?? blankCarousel());
    if (initial?.cover.headline) setTitle(initial.cover.headline);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedId]);

  function updateSlide(index: number, patch: Partial<CarouselSlide>) {
    if (!data) return;
    const slides = data.slides.map((slide, i) => (i === index ? { ...slide, ...patch } : slide));
    setData({ ...data, slides });
  }

  function moveSlide(index: number, direction: -1 | 1) {
    if (!data) return;
    const target = index + direction;
    if (target < 0 || target >= data.slides.length) return;
    const slides = [...data.slides];
    const moved = slides[index];
    const displaced = slides[target];
    if (!moved || !displaced) return;
    slides[index] = displaced;
    slides[target] = moved;
    setData({ ...data, slides });
  }

  function addSlide() {
    if (!data || data.slides.length >= 12) return;
    setData({ ...data, slides: [...data.slides, blankSlide()] });
  }

  function removeSlide(index: number) {
    if (!data || data.slides.length <= 1) return;
    setData({ ...data, slides: data.slides.filter((_, i) => i !== index) });
  }

  async function handleSave() {
    if (!data) return;
    setSaving(true);
    try {
      const payload = { title, data };
      const result = savedId
        ? await apiFetch<CarouselResponse>(`/api/v1/carousels/${savedId}`, {
            method: "PUT",
            body: payload,
          })
        : await apiFetch<CarouselResponse>("/api/v1/carousels", { method: "POST", body: payload });
      justSavedRef.current = true;
      setSavedId(result.id);
      navigate(`/content/carousel/${result.id}`, { replace: true });
      pushToast({ title: "Carousel saved", variant: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof ApiError ? err.message : "Couldn't save this carousel.",
        variant: "danger",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleExport(kind: "pdf" | "png") {
    if (!savedId) {
      pushToast({ title: "Save the carousel first", variant: "danger" });
      return;
    }
    setExporting(kind);
    try {
      await downloadBlob(
        `/api/v1/carousels/${savedId}/export/${kind}`,
        kind === "pdf" ? `${title}.pdf` : `${title}-slides.zip`,
      );
    } catch {
      pushToast({ title: "Export failed", variant: "danger" });
    } finally {
      setExporting(null);
    }
  }

  if (loadError) return <p className="text-sm text-danger">{loadError}</p>;
  if (!data) return <Skeleton className="h-64 w-full" />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Carousel builder</h1>
        <p className="text-sm text-fg-muted">
          Edit each slide, reorder them, and pick a layout -- then export a PDF or PNGs to upload as
          a LinkedIn document post. LinkSavvy doesn't post this for you.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Title and template</CardTitle>
          <CardDescription>The title is for your own reference in Workspace.</CardDescription>
        </CardHeader>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mb-3 h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
        />
        <div className="flex gap-2">
          {TEMPLATES.map((tpl) => (
            <Button
              key={tpl.id}
              variant={data.template === tpl.id ? "primary" : "secondary"}
              size="sm"
              onClick={() => setData({ ...data, template: tpl.id })}
            >
              {tpl.label}
            </Button>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cover</CardTitle>
        </CardHeader>
        <div className="flex flex-col gap-2">
          <input
            value={data.cover.headline}
            onChange={(e) =>
              setData({ ...data, cover: { ...data.cover, headline: e.target.value } })
            }
            placeholder="Cover headline"
            className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
          />
          <input
            value={data.cover.subhead}
            onChange={(e) =>
              setData({ ...data, cover: { ...data.cover, subhead: e.target.value } })
            }
            placeholder="Cover subhead"
            className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
          />
        </div>
      </Card>

      {data.slides.map((slide, index) => (
        <Card key={index}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Slide {index + 1}</CardTitle>
              <div className="flex gap-1">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => moveSlide(index, -1)}
                  disabled={index === 0}
                >
                  ↑
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => moveSlide(index, 1)}
                  disabled={index === data.slides.length - 1}
                >
                  ↓
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => removeSlide(index)}
                  disabled={data.slides.length <= 1}
                >
                  Remove
                </Button>
              </div>
            </div>
          </CardHeader>
          <div className="flex flex-col gap-2">
            <input
              value={slide.headline}
              onChange={(e) => updateSlide(index, { headline: e.target.value })}
              placeholder="Headline"
              className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
            />
            <textarea
              value={slide.body}
              onChange={(e) => updateSlide(index, { body: e.target.value })}
              rows={3}
              placeholder="Body"
              className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg"
            />
            <input
              value={slide.visual_note ?? ""}
              onChange={(e) => updateSlide(index, { visual_note: e.target.value })}
              placeholder="Visual note (what image/graphic belongs here)"
              className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg-muted"
            />
          </div>
        </Card>
      ))}

      <Button variant="secondary" onClick={addSlide} disabled={data.slides.length >= 12}>
        Add slide
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Closing and caption</CardTitle>
        </CardHeader>
        <div className="flex flex-col gap-2">
          <input
            value={data.closing?.cta ?? ""}
            onChange={(e) => setData({ ...data, closing: { cta: e.target.value } })}
            placeholder="Closing call to action"
            className="h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
          />
          <textarea
            value={data.caption}
            onChange={(e) => setData({ ...data, caption: e.target.value })}
            rows={3}
            placeholder="Caption (posted alongside the carousel, not a slide)"
            className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg"
          />
        </div>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button onClick={handleSave} loading={saving}>
          Save carousel
        </Button>
        <Button
          variant="secondary"
          onClick={() => handleExport("pdf")}
          loading={exporting === "pdf"}
        >
          Export PDF
        </Button>
        <Button
          variant="secondary"
          onClick={() => handleExport("png")}
          loading={exporting === "png"}
        >
          Export PNGs
        </Button>
      </div>
    </div>
  );
}
