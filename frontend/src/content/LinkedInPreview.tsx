/**
 * Reproduces LinkedIn's own post rendering closely enough to preview
 * what a draft will look like once posted: the truncation fold with a
 * "…see more" control, preserved blank lines, hashtags and @-mentions
 * styled as links, and a mobile/desktop width toggle. This is a
 * best-effort approximation, not a pixel-perfect clone -- LinkedIn's
 * actual rendering (fold position, mention resolution) isn't public
 * and can drift; see linkedin-preview-config.ts for the observed
 * constants this depends on.
 */

import { useState, type ReactNode } from "react";
import { LINKEDIN_FOLD_CHAR_LIMIT } from "./linkedin-preview-config";

const HASHTAG_OR_MENTION = /(#[\w-]+|@[\w.-]+)/g;

function renderInlineTokens(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(HASHTAG_OR_MENTION);
  return parts.map((part, index) => {
    if (part.startsWith("#") || part.startsWith("@")) {
      return (
        <span key={`${keyPrefix}-${index}`} className="text-primary">
          {part}
        </span>
      );
    }
    return <span key={`${keyPrefix}-${index}`}>{part}</span>;
  });
}

export type PreviewWidth = "mobile" | "desktop";

const WIDTH_CLASSES: Record<PreviewWidth, string> = {
  mobile: "max-w-[360px]",
  desktop: "max-w-[550px]",
};

export function LinkedInPreview({
  body,
  width = "desktop",
}: {
  body: string;
  width?: PreviewWidth;
}) {
  const [expanded, setExpanded] = useState(false);

  const needsFold = body.length > LINKEDIN_FOLD_CHAR_LIMIT;
  const visibleText = expanded || !needsFold ? body : body.slice(0, LINKEDIN_FOLD_CHAR_LIMIT);

  return (
    <div
      className={`${WIDTH_CLASSES[width]} rounded-lg border border-border bg-card p-4 shadow-sm`}
    >
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-fg">
        {renderInlineTokens(visibleText, "text")}
        {!expanded && needsFold && (
          <>
            <span className="text-fg-muted">&hellip;</span>{" "}
            <button
              type="button"
              onClick={() => setExpanded(true)}
              className="font-medium text-fg-muted hover:underline"
            >
              see more
            </button>
          </>
        )}
      </p>
    </div>
  );
}
