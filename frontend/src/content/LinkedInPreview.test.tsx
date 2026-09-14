import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LinkedInPreview } from "./LinkedInPreview";
import { LINKEDIN_FOLD_CHAR_LIMIT } from "./linkedin-preview-config";

describe("LinkedInPreview", () => {
  it("shows short text in full with no fold control", () => {
    render(<LinkedInPreview body="A short post with #onehashtag and @someone." />);
    expect(screen.getByText(/A short post with/)).toBeInTheDocument();
    expect(screen.queryByText("see more")).not.toBeInTheDocument();
  });

  it("truncates long text behind a see-more control that expands on click", () => {
    const long = "x".repeat(LINKEDIN_FOLD_CHAR_LIMIT + 50);
    render(<LinkedInPreview body={long} />);
    const seeMore = screen.getByText("see more");
    expect(seeMore).toBeInTheDocument();
    fireEvent.click(seeMore);
    expect(screen.queryByText("see more")).not.toBeInTheDocument();
  });

  it("styles hashtags and mentions", () => {
    render(<LinkedInPreview body="Loving #buildinpublic with @someone today" />);
    expect(screen.getByText("#buildinpublic")).toHaveClass("text-primary");
    expect(screen.getByText("@someone")).toHaveClass("text-primary");
  });
});
