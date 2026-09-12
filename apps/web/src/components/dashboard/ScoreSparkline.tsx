import type { ScoreHistoryPoint } from "@linksavvy/contracts";

const WIDTH = 280;
const HEIGHT = 60;
const PADDING = 4;

export interface ScoreSparklineProps {
  points: ScoreHistoryPoint[];
  delta: number | null;
}

function buildPath(points: ScoreHistoryPoint[]): string {
  if (points.length === 0) return "";
  const [first] = points;
  if (points.length === 1 && first) {
    const y = HEIGHT - PADDING - (first.overall / 100) * (HEIGHT - 2 * PADDING);
    return `M ${PADDING},${y} L ${WIDTH - PADDING},${y}`;
  }
  const step = (WIDTH - 2 * PADDING) / (points.length - 1);
  return points
    .map((point, index) => {
      const x = PADDING + index * step;
      const y = HEIGHT - PADDING - (point.overall / 100) * (HEIGHT - 2 * PADDING);
      return `${index === 0 ? "M" : "L"} ${x},${y}`;
    })
    .join(" ");
}

/** A 90-day overall-score trend line with its delta -- deliberately no
 * charting library for a single polyline. */
export function ScoreSparkline({ points, delta }: ScoreSparklineProps) {
  if (points.length === 0) {
    return <p className="text-sm text-fg-muted">Not enough history yet to show a trend.</p>;
  }

  const deltaLabel =
    delta === null ? null : delta === 0 ? "No change" : delta > 0 ? `+${delta}` : `${delta}`;
  const deltaColor =
    delta === null || delta === 0 ? "text-fg-muted" : delta > 0 ? "text-success" : "text-danger";

  return (
    <div className="flex items-center gap-4">
      <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="shrink-0">
        <path
          d={buildPath(points)}
          fill="none"
          stroke="hsl(var(--color-primary))"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>
      {deltaLabel && (
        <span className={`text-sm font-medium ${deltaColor}`}>{deltaLabel} over 90 days</span>
      )}
    </div>
  );
}
