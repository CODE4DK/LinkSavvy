import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultView } from "./renderers";

describe("ResultView thread renderer", () => {
  it("renders chat-shaped messages", () => {
    render(
      <ResultView
        renderer="thread"
        output={{ messages: [{ role: "user", text: "Hello there" }] }}
      />,
    );
    expect(screen.getByText("Hello there")).toBeInTheDocument();
    expect(screen.getByText("user")).toBeInTheDocument();
  });

  it("falls back to a carousel-shaped output with no messages field", () => {
    render(
      <ResultView
        renderer="thread"
        output={{
          cover: { headline: "Cover headline", subhead: "Cover subhead" },
          slides: [{ index: 1, headline: "Slide one", body: "Slide one body", visual_note: "" }],
          closing: { cta: "Closing CTA text" },
          caption: "A caption",
        }}
      />,
    );
    expect(screen.getByText("Cover")).toBeInTheDocument();
    expect(screen.getByText("Slide one")).toBeInTheDocument();
    expect(screen.getByText("Slide one body")).toBeInTheDocument();
    expect(screen.getByText("Closing CTA text")).toBeInTheDocument();
  });

  it("shows empty state for neither shape", () => {
    render(<ResultView renderer="thread" output={{}} />);
    expect(screen.getByText(/no displayable output/i)).toBeInTheDocument();
  });
});
