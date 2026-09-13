/**
 * Renders a tool's parsed output. Dispatch is on `result_renderer` alone
 * (`variants` | `document` | `analysis` | `table` | `calendar` | `thread`)
 * -- never on a tool id -- so a new tool gets a working result view for
 * free as long as its prompt's output conforms to the shape its chosen
 * renderer expects. Those shapes are this module's half of the contract
 * (see docs/adding-a-tool.md for the other half, the prompt side):
 *
 * - `variants`: `{ variants: Record<string, JsonValue>[] }` -- each
 *   variant's longest string field is shown as its primary text, every
 *   other scalar field as a small label underneath.
 * - `document`: `{ sections: { heading?, body?, bullets? }[] }` -- a
 *   bullet may carry `flagged`/`flag_reason` (e.g. "needs a real metric
 *   here") without the renderer knowing why.
 * - `analysis`: `{ summary?, score?, findings: { title, severity?,
 *   description?, recommendation? }[] }`.
 * - `table`: `{ columns: string[], rows: Record<string, JsonValue>[] }`.
 * - `calendar`: `{ days: { date, items: { title, time?, kind? }[] }[] }`.
 * - `thread`: `{ messages: { author?, role?, text, timestamp? }[] }`.
 */

import type { ToolSummary } from "@linksavvy/contracts";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };
type JsonRecord = Record<string, JsonValue>;

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asArray(value: unknown): JsonRecord[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord);
}

function stringify(value: JsonValue | undefined): string {
  if (value === undefined || value === null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function primaryTextField(record: JsonRecord): { key: string | null; text: string } {
  let bestKey: string | null = null;
  let bestValue = "";
  for (const [key, value] of Object.entries(record)) {
    if (typeof value !== "string") continue;
    if (value.length > bestValue.length) {
      bestKey = key;
      bestValue = value;
    }
  }
  return { key: bestKey, text: bestValue };
}

function VariantsView({ output, onPick }: { output: unknown; onPick?: (text: string) => void }) {
  const variants = isRecord(output) ? asArray(output.variants) : [];
  if (variants.length === 0) return <EmptyOutput />;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {variants.map((variant, index) => {
        const { key: primaryKey, text } = primaryTextField(variant);
        const rest = Object.entries(variant).filter(([key]) => key !== primaryKey);
        return (
          <div key={index} className="rounded-md border border-border bg-bg p-3">
            <p className="whitespace-pre-wrap text-sm text-fg">{text}</p>
            {rest.length > 0 && (
              <dl className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-fg-muted">
                {rest.map(([key, value]) => (
                  <div key={key} className="flex gap-1">
                    <dt className="font-medium">{key}:</dt>
                    <dd>
                      {Array.isArray(value) ? value.map(stringify).join(", ") : stringify(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            )}
            {onPick && (
              <Button variant="secondary" size="sm" className="mt-3" onClick={() => onPick(text)}>
                Apply to profile
              </Button>
            )}
          </div>
        );
      })}
    </div>
  );
}

function DocumentView({ output }: { output: unknown }) {
  const sections = isRecord(output) ? asArray(output.sections) : [];
  if (sections.length === 0) return <EmptyOutput />;
  return (
    <div className="flex flex-col gap-4">
      {sections.map((section, index) => {
        const bullets = asArray(section.bullets);
        return (
          <div key={index}>
            {typeof section.heading === "string" && (
              <h3 className="mb-1 text-sm font-semibold text-fg">{section.heading}</h3>
            )}
            {typeof section.body === "string" && (
              <p className="whitespace-pre-wrap text-sm text-fg">{section.body}</p>
            )}
            {bullets.length > 0 && (
              <ul className="mt-2 flex flex-col gap-1.5">
                {bullets.map((bullet, bulletIndex) => (
                  <li key={bulletIndex} className="flex items-start gap-2 text-sm text-fg">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-fg-muted" />
                    <span>
                      {stringify(bullet.text)}
                      {bullet.flagged === true && (
                        <Badge variant="warning" className="ml-2 align-middle">
                          {typeof bullet.flag_reason === "string"
                            ? bullet.flag_reason
                            : "needs input"}
                        </Badge>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}

const SEVERITY_VARIANT: Record<string, "default" | "primary" | "success" | "warning" | "danger"> = {
  critical: "danger",
  warning: "warning",
  info: "default",
  success: "success",
};

function AnalysisView({ output }: { output: unknown }) {
  if (!isRecord(output)) return <EmptyOutput />;
  const findings = asArray(output.findings);
  return (
    <div className="flex flex-col gap-4">
      {(typeof output.score === "number" || typeof output.summary === "string") && (
        <div className="flex items-center gap-3">
          {typeof output.score === "number" && (
            <Badge variant="primary">Score: {output.score}</Badge>
          )}
          {typeof output.summary === "string" && (
            <p className="text-sm text-fg-muted">{output.summary}</p>
          )}
        </div>
      )}
      {findings.length > 0 && (
        <ul className="flex flex-col gap-3">
          {findings.map((finding, index) => (
            <li key={index} className="rounded-md border border-border bg-bg p-3">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-fg">{stringify(finding.title)}</p>
                {typeof finding.severity === "string" && (
                  <Badge variant={SEVERITY_VARIANT[finding.severity] ?? "default"}>
                    {finding.severity}
                  </Badge>
                )}
              </div>
              {typeof finding.description === "string" && (
                <p className="mt-1 text-sm text-fg-muted">{finding.description}</p>
              )}
              {typeof finding.recommendation === "string" && (
                <p className="mt-1 text-sm text-fg">→ {finding.recommendation}</p>
              )}
            </li>
          ))}
        </ul>
      )}
      {findings.length === 0 && typeof output.summary !== "string" && <EmptyOutput />}
    </div>
  );
}

function TableView({ output }: { output: unknown }) {
  if (!isRecord(output)) return <EmptyOutput />;
  const columns = Array.isArray(output.columns) ? output.columns.map(String) : [];
  const rows = asArray(output.rows);
  if (columns.length === 0 || rows.length === 0) return <EmptyOutput />;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-fg-muted">
            {columns.map((column) => (
              <th key={column} className="whitespace-nowrap px-2 py-1.5 font-medium">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-border/60 last:border-0">
              {columns.map((column) => (
                <td key={column} className="px-2 py-1.5 align-top text-fg">
                  {stringify(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CalendarView({ output }: { output: unknown }) {
  const days = isRecord(output) ? asArray(output.days) : [];
  if (days.length === 0) return <EmptyOutput />;
  return (
    <div className="flex flex-col gap-3">
      {days.map((day, index) => {
        const items = asArray(day.items);
        return (
          <div key={index} className="rounded-md border border-border bg-bg p-3">
            <p className="text-sm font-semibold text-fg">{stringify(day.date)}</p>
            <ul className="mt-1 flex flex-col gap-1">
              {items.map((item, itemIndex) => (
                <li key={itemIndex} className="flex items-center gap-2 text-sm text-fg-muted">
                  {typeof item.time === "string" && (
                    <span className="tabular-nums">{item.time}</span>
                  )}
                  <span className="text-fg">{stringify(item.title)}</span>
                  {typeof item.kind === "string" && <Badge>{item.kind}</Badge>}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

function ThreadView({ output }: { output: unknown }) {
  const messages = isRecord(output) ? asArray(output.messages) : [];
  if (messages.length === 0) return <EmptyOutput />;
  return (
    <div className="flex flex-col gap-3">
      {messages.map((message, index) => (
        <div key={index} className="rounded-md border border-border bg-bg p-3">
          <div className="mb-1 flex items-center gap-2 text-xs text-fg-muted">
            {typeof message.author === "string" && (
              <span className="font-medium text-fg">{message.author}</span>
            )}
            {typeof message.role === "string" && <Badge>{message.role}</Badge>}
            {typeof message.timestamp === "string" && <span>{message.timestamp}</span>}
          </div>
          <p className="whitespace-pre-wrap text-sm text-fg">{stringify(message.text)}</p>
        </div>
      ))}
    </div>
  );
}

function EmptyOutput() {
  return <p className="text-sm text-fg-muted">This run produced no displayable output.</p>;
}

const RENDERERS: Record<
  Exclude<ToolSummary["result_renderer"], "variants">,
  (props: { output: unknown }) => JSX.Element
> = {
  document: DocumentView,
  analysis: AnalysisView,
  table: TableView,
  calendar: CalendarView,
  thread: ThreadView,
};

export function ResultView({
  renderer,
  output,
  onPickVariant,
}: {
  renderer: ToolSummary["result_renderer"];
  output: unknown;
  /** Only meaningful for the `variants` renderer: when provided, each
   * variant card gets an "Apply to profile" button that calls back with
   * that one variant's primary text -- the Profile Hub page's way of
   * letting the user pick which of several variants to accept, since
   * only it (not the framework) knows what "accept" should do. */
  onPickVariant?: (text: string) => void;
}) {
  if (renderer === "variants") return <VariantsView output={output} onPick={onPickVariant} />;
  const View = RENDERERS[renderer] ?? DocumentView;
  return <View output={output} />;
}

/** The client-side half of "Save to Workspace": only the renderer knows
 * which slice of a structured output the user actually wants to keep, so
 * this picks the same primary text `VariantsView` displays, joins a
 * document's sections, or falls back to the raw JSON -- never a
 * tool-specific field name. */
export function extractSaveableText(
  renderer: ToolSummary["result_renderer"],
  output: unknown,
): string {
  if (!isRecord(output)) return JSON.stringify(output, null, 2);
  switch (renderer) {
    case "variants": {
      const variants = asArray(output.variants);
      return variants.map((variant) => primaryTextField(variant).text).join("\n\n---\n\n");
    }
    case "document": {
      const sections = asArray(output.sections);
      return sections
        .map((section) => {
          const bullets = asArray(section.bullets).map((bullet) => `- ${stringify(bullet.text)}`);
          return [stringify(section.heading), stringify(section.body), ...bullets]
            .filter(Boolean)
            .join("\n");
        })
        .join("\n\n");
    }
    case "analysis":
      return typeof output.summary === "string" ? output.summary : JSON.stringify(output, null, 2);
    default:
      return JSON.stringify(output, null, 2);
  }
}
