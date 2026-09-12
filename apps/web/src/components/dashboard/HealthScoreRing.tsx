const SIZE = 140;
const STROKE_WIDTH = 12;
const RADIUS = (SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export interface HealthScoreRingProps {
  overall: number | null;
}

function ringColor(score: number): string {
  if (score >= 80) return "hsl(var(--color-success))";
  if (score >= 50) return "hsl(var(--color-warning))";
  return "hsl(var(--color-danger))";
}

/** A circular progress ring showing the overall Health Score, 0-100.
 * Renders a flat "--" track when there's no score yet (first-time users,
 * or an audit that produced no overall score at all). */
export function HealthScoreRing({ overall }: HealthScoreRingProps) {
  const hasScore = overall !== null;
  const progress = hasScore ? Math.max(0, Math.min(100, overall)) / 100 : 0;
  const offset = CIRCUMFERENCE * (1 - progress);

  return (
    <div className="relative flex h-[140px] w-[140px] items-center justify-center">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} className="-rotate-90">
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="hsl(var(--color-border))"
          strokeWidth={STROKE_WIDTH}
        />
        {hasScore && (
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={ringColor(overall)}
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        )}
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-semibold text-fg">{hasScore ? overall : "--"}</span>
        <span className="text-xs text-fg-muted">out of 100</span>
      </div>
    </div>
  );
}
