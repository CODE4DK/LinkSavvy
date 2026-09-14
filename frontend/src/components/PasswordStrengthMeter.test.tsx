import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PasswordStrengthMeter, scorePassword } from "./PasswordStrengthMeter";

describe("scorePassword", () => {
  it("scores an empty password as 0", () => {
    expect(scorePassword("")).toBe(0);
  });

  it("scores a short all-lowercase password as weak", () => {
    expect(scorePassword("abc123456")).toBeLessThanOrEqual(1);
  });

  it("scores a long mixed-case password with symbols as strong", () => {
    expect(scorePassword("Correct-Horse-Battery-99!")).toBe(4);
  });
});

describe("PasswordStrengthMeter", () => {
  it("renders nothing extra for an empty password", () => {
    render(<PasswordStrengthMeter password="" />);
    expect(screen.queryByText(/password strength/i)).not.toBeInTheDocument();
  });

  it("shows a strength label once typing starts", () => {
    render(<PasswordStrengthMeter password="weak" />);
    expect(screen.getByText(/password strength/i)).toBeInTheDocument();
  });
});
