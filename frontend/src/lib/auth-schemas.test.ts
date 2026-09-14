import { describe, expect, it } from "vitest";
import { loginSchema, registerSchema, fieldErrors } from "./auth-schemas";

describe("loginSchema", () => {
  it("accepts a valid email and non-empty password", () => {
    const result = loginSchema.safeParse({ email: "a@example.com", password: "x" });
    expect(result.success).toBe(true);
  });

  it("rejects an invalid email", () => {
    const result = loginSchema.safeParse({ email: "not-an-email", password: "x" });
    expect(result.success).toBe(false);
  });
});

describe("registerSchema", () => {
  it("rejects a weak password", () => {
    const result = registerSchema.safeParse({
      fullName: "A Person",
      email: "a@example.com",
      password: "short1",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const errors = fieldErrors(result.error);
      expect(errors.password).toBeDefined();
    }
  });

  it("accepts a valid registration payload", () => {
    const result = registerSchema.safeParse({
      fullName: "A Person",
      email: "a@example.com",
      password: "correct-horse-99",
    });
    expect(result.success).toBe(true);
  });
});
