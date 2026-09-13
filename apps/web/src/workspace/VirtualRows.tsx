/**
 * A minimal windowed renderer for a list of items grouped into fixed-
 * height rows: only rows within the visible scroll range (plus a small
 * overscan buffer) are ever mounted, so the DOM stays bounded no
 * matter how many items the list holds -- the point of B4's "grid
 * renders without jank" requirement at 5,000 assets. No virtualization
 * library, same philosophy as ScoreSparkline's hand-rolled chart: this
 * is a handful of arithmetic on scrollTop, not enough to justify a
 * dependency.
 */

import { useMemo, useRef, useState, type ReactNode } from "react";

export interface VirtualRowsProps<T> {
  items: T[];
  columns: number;
  rowHeight: number;
  height: number;
  overscan?: number;
  renderItem: (item: T, index: number) => ReactNode;
  getKey: (item: T, index: number) => string;
}

export function VirtualRows<T>({
  items,
  columns,
  rowHeight,
  height,
  overscan = 3,
  renderItem,
  getKey,
}: VirtualRowsProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const rowCount = Math.ceil(items.length / columns);
  const totalHeight = rowCount * rowHeight;

  const firstVisibleRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const visibleRowCount = Math.ceil(height / rowHeight) + overscan * 2;
  const lastVisibleRow = Math.min(rowCount, firstVisibleRow + visibleRowCount);

  const visibleItems = useMemo(() => {
    const startIndex = firstVisibleRow * columns;
    const endIndex = Math.min(items.length, lastVisibleRow * columns);
    return items.slice(startIndex, endIndex).map((item, i) => ({
      item,
      index: startIndex + i,
    }));
  }, [items, firstVisibleRow, lastVisibleRow, columns]);

  return (
    <div
      ref={containerRef}
      data-testid="virtual-rows-viewport"
      style={{ height, overflowY: "auto", position: "relative" }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div style={{ height: totalHeight, position: "relative" }}>
        <div
          style={{
            position: "absolute",
            top: firstVisibleRow * rowHeight,
            left: 0,
            right: 0,
            display: "grid",
            gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
            gap: "1rem",
          }}
        >
          {visibleItems.map(({ item, index }) => (
            <div key={getKey(item, index)}>{renderItem(item, index)}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
