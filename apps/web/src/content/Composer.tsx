/**
 * The plain-text post editor: a live character counter against
 * LinkedIn's limit, a preview pane reproducing LinkedIn's own
 * rendering, formatting helpers that are upfront about their real
 * cost, and actions for what happens next -- copy, save, add to the
 * calendar, or record that the person posted it themselves.
 *
 * LinkSavvy never posts to LinkedIn. There is no publish button here
 * on purpose.
 */

import { useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { AssetResponse } from "@linksavvy/contracts";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/lib/toast-context";
import { LinkedInPreview, type PreviewWidth } from "./LinkedInPreview";
import { LINKEDIN_POST_CHAR_LIMIT, LINKEDIN_WARNING_THRESHOLD } from "./linkedin-preview-config";
import { toUnicodeBold, toUnicodeItalic } from "./unicode-style";

function defaultTitle(body: string): string {
  const firstLine = body.split("\n").find((line) => line.trim().length > 0) ?? "Untitled draft";
  return firstLine.length > 60 ? `${firstLine.slice(0, 57)}...` : firstLine;
}

function applyToSelection(
  textarea: HTMLTextAreaElement,
  body: string,
  setBody: (next: string) => void,
  transform: (selected: string) => string,
): void {
  const { selectionStart, selectionEnd } = textarea;
  if (selectionStart === selectionEnd) return;
  const selected = body.slice(selectionStart, selectionEnd);
  const next = body.slice(0, selectionStart) + transform(selected) + body.slice(selectionEnd);
  setBody(next);
}

export function Composer() {
  const location = useLocation();
  const navigate = useNavigate();
  const { push: pushToast } = useToast();
  const prefill = (location.state as { prefill?: string } | null)?.prefill ?? "";

  const [body, setBody] = useState(prefill);
  const [width, setWidth] = useState<PreviewWidth>("desktop");
  const [savedAssetId, setSavedAssetId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showUnicodeWarning, setShowUnicodeWarning] = useState(false);
  const [pendingStyle, setPendingStyle] = useState<"bold" | "italic" | null>(null);
  const [showPostedModal, setShowPostedModal] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [recordingPosted, setRecordingPosted] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const charCount = body.length;
  const overLimit = charCount > LINKEDIN_POST_CHAR_LIMIT;
  const nearLimit = charCount >= LINKEDIN_WARNING_THRESHOLD;

  async function ensureSavedAsset(): Promise<string> {
    if (savedAssetId) return savedAssetId;
    const asset = await apiFetch<AssetResponse>("/api/v1/assets", {
      method: "POST",
      body: { type: "post", title: defaultTitle(body), body },
    });
    setSavedAssetId(asset.id);
    return asset.id;
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(body);
      pushToast({ title: "Copied to clipboard", variant: "success" });
    } catch {
      pushToast({
        title: "Couldn't copy -- select and copy the text manually.",
        variant: "danger",
      });
    }
  }

  async function handleSaveToWorkspace() {
    setSaving(true);
    try {
      await ensureSavedAsset();
      pushToast({ title: "Saved to Workspace", variant: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof ApiError ? err.message : "Couldn't save this draft.",
        variant: "danger",
      });
    } finally {
      setSaving(false);
    }
  }

  function handleAddToCalendar() {
    navigate("/content/calendar", { state: { draftBody: body } });
  }

  async function handleConfirmPosted() {
    setRecordingPosted(true);
    try {
      const assetId = await ensureSavedAsset();
      await apiFetch<AssetResponse>(`/api/v1/assets/${assetId}/mark-posted`, {
        method: "POST",
        body: { linkedin_url: linkedinUrl.trim() || null },
      });
      setShowPostedModal(false);
      setLinkedinUrl("");
      pushToast({ title: "Recorded -- nice work", variant: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof ApiError ? err.message : "Couldn't record this.",
        variant: "danger",
      });
    } finally {
      setRecordingPosted(false);
    }
  }

  function requestUnicodeStyle(style: "bold" | "italic") {
    setPendingStyle(style);
    setShowUnicodeWarning(true);
  }

  function confirmUnicodeStyle() {
    const textarea = textareaRef.current;
    if (textarea && pendingStyle) {
      applyToSelection(
        textarea,
        body,
        setBody,
        pendingStyle === "bold" ? toUnicodeBold : toUnicodeItalic,
      );
    }
    setShowUnicodeWarning(false);
    setPendingStyle(null);
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-fg">Composer</h1>
        <p className="text-sm text-fg-muted">
          LinkSavvy does not post to LinkedIn for you. Draft here, then copy this into LinkedIn
          yourself when you're ready.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Draft</CardTitle>
            <div className="flex items-center justify-between">
              <CardDescription>
                Plain text -- LinkedIn has no native bold or italics.
              </CardDescription>
              <span
                className={`text-xs font-medium ${overLimit ? "text-danger" : nearLimit ? "text-warning" : "text-fg-muted"}`}
              >
                {charCount} / {LINKEDIN_POST_CHAR_LIMIT}
              </span>
            </div>
          </CardHeader>

          <div className="mb-2 flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" onClick={() => requestUnicodeStyle("bold")}>
              Bold (fake)
            </Button>
            <Button variant="secondary" size="sm" onClick={() => requestUnicodeStyle("italic")}>
              Italic (fake)
            </Button>
          </div>

          <textarea
            ref={textareaRef}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={16}
            placeholder="Write your post here..."
            className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg placeholder:text-fg-muted"
          />

          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={handleCopy}>Copy to clipboard</Button>
            <Button variant="secondary" onClick={handleSaveToWorkspace} loading={saving}>
              Save to Workspace
            </Button>
            <Button variant="secondary" onClick={handleAddToCalendar}>
              Add to calendar
            </Button>
            <Button variant="secondary" onClick={() => setShowPostedModal(true)}>
              I posted this
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Preview</CardTitle>
              <div className="flex gap-1">
                <Button
                  variant={width === "mobile" ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => setWidth("mobile")}
                >
                  Mobile
                </Button>
                <Button
                  variant={width === "desktop" ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => setWidth("desktop")}
                >
                  Desktop
                </Button>
              </div>
            </div>
            <CardDescription>
              An approximation of LinkedIn's own rendering -- fold position and mention styling are
              observed, not guaranteed to match exactly.
            </CardDescription>
          </CardHeader>
          <LinkedInPreview body={body} width={width} />
        </Card>
      </div>

      <Modal
        open={showUnicodeWarning}
        onClose={() => setShowUnicodeWarning(false)}
        title="This hurts accessibility"
      >
        <p className="mb-4 text-sm text-fg">
          This replaces your selected text with different Unicode characters that merely look
          {pendingStyle === "bold" ? " bold" : " italic"}. Screen readers often can't recognize them
          as normal letters -- some skip them, some read them out strangely. Use this sparingly, and
          never for anything that must be accessible.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setShowUnicodeWarning(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmUnicodeStyle}>
            Apply anyway
          </Button>
        </div>
      </Modal>

      <Modal open={showPostedModal} onClose={() => setShowPostedModal(false)} title="I posted this">
        <p className="mb-4 text-sm text-fg-muted">
          This just records that you posted it -- LinkSavvy never posts on your behalf.
        </p>
        <input
          value={linkedinUrl}
          onChange={(e) => setLinkedinUrl(e.target.value)}
          placeholder="LinkedIn post URL (optional)"
          className="mb-4 h-9 w-full rounded-md border border-border bg-bg px-3 text-sm text-fg"
        />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setShowPostedModal(false)}>
            Cancel
          </Button>
          <Button onClick={handleConfirmPosted} loading={recordingPosted}>
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}
