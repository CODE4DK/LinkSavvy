import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { VirtualRows } from "./VirtualRows";

const ITEMS = Array.from({ length: 5000 }, (_, i) => ({ id: `item-${i}`, label: `Item ${i}` }));

describe("VirtualRows", () => {
  it("renders only a bounded window of items even with 5,000 in the list", () => {
    render(
      <VirtualRows
        items={ITEMS}
        columns={3}
        rowHeight={100}
        height={400}
        renderItem={(item) => <div data-testid="card">{item.label}</div>}
        getKey={(item) => item.id}
      />,
    );

    const cards = screen.getAllByTestId("card");
    // height=400 / rowHeight=100 = 4 visible rows, +overscan*2 rows,
    // times 3 columns -- comfortably under 100 regardless of the
    // 5,000-item backing array.
    expect(cards.length).toBeLessThan(100);
    expect(cards.length).toBeGreaterThan(0);
  });

  it("renders the first item's content", () => {
    render(
      <VirtualRows
        items={ITEMS}
        columns={3}
        rowHeight={100}
        height={400}
        renderItem={(item) => <div data-testid="card">{item.label}</div>}
        getKey={(item) => item.id}
      />,
    );
    expect(screen.getByText("Item 0")).toBeInTheDocument();
  });
});
