import { z } from "zod";

const password = z
  .string()
  .min(10, "Must be at least 10 characters")
  .regex(/[A-Za-z]/, "Must contain a letter")
  .regex(/[0-9]/, "Must contain a number");

export const registerSchema = z.object({
  fullName: z.string().trim().min(1, "Full name is required"),
  email: z.string().trim().email("Enter a valid email address"),
  password,
});
export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
});
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z.object({
  password,
});
export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

export function fieldErrors<T>(error: z.ZodError<T>): Partial<Record<string, string>> {
  const errors: Partial<Record<string, string>> = {};
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (typeof key === "string" && !errors[key]) errors[key] = issue.message;
  }
  return errors;
}
