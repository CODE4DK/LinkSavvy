/**
 * Hand-maintained Zod mirror of apps/api/app/profiles/schema.py's
 * ProfileSnapshot. Unlike schema.d.ts (generated from the OpenAPI
 * document), this is real runtime validation the web app uses to check
 * a draft snapshot — e.g. before rendering the onboarding review step,
 * or before submitting an edited draft — before it ever reaches the
 * API. Keep the two in sync by hand: this is the one Pydantic model
 * that's deliberately mirrored rather than generated, because the web
 * app needs to validate and edit snapshots client-side, not just type
 * request/response bodies.
 *
 * Every field is optional, matching the Python side: `undefined` means
 * "we don't know", `[]` means "we know there are none", and `""` means
 * "we were told it's blank".
 */

import { z } from "zod";

export const profileSourceSchema = z.enum([
  "linkedin_api",
  "paste",
  "upload_pdf",
  "upload_docx",
  "manual",
  "merged",
]);
export type ProfileSource = z.infer<typeof profileSourceSchema>;

export const datePartSchema = z.object({
  year: z.number().int().optional(),
  month: z.number().int().min(1).max(12).optional(),
});
export type DatePart = z.infer<typeof datePartSchema>;

export const identitySchema = z.object({
  full_name: z.string().optional(),
  headline: z.string().optional(),
  custom_url: z.string().optional(),
  industry: z.string().optional(),
  location: z.string().optional(),
  profile_picture_url: z.string().optional(),
});
export type Identity = z.infer<typeof identitySchema>;

export const experienceSchema = z.object({
  company: z.string().optional(),
  title: z.string().optional(),
  employment_type: z.string().optional(),
  location: z.string().optional(),
  start: datePartSchema.optional(),
  end: datePartSchema.optional(),
  is_current: z.boolean().optional(),
  description: z.string().optional(),
  bullets: z.array(z.string()).optional(),
  skills: z.array(z.string()).optional(),
});
export type Experience = z.infer<typeof experienceSchema>;

export const educationSchema = z.object({
  school: z.string().optional(),
  degree: z.string().optional(),
  field: z.string().optional(),
  start_year: z.number().int().optional(),
  end_year: z.number().int().optional(),
  description: z.string().optional(),
});
export type Education = z.infer<typeof educationSchema>;

export const skillSchema = z.object({
  name: z.string().optional(),
  endorsements: z.number().int().optional(),
  is_top: z.boolean().optional(),
});
export type Skill = z.infer<typeof skillSchema>;

export const certificationSchema = z.object({
  name: z.string().optional(),
  issuer: z.string().optional(),
  issued: datePartSchema.optional(),
  credential_id: z.string().optional(),
  url: z.string().optional(),
});
export type Certification = z.infer<typeof certificationSchema>;

export const languageSchema = z.object({
  name: z.string().optional(),
  proficiency: z.string().optional(),
});
export type Language = z.infer<typeof languageSchema>;

export const projectSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  url: z.string().optional(),
  start: datePartSchema.optional(),
  end: datePartSchema.optional(),
});
export type Project = z.infer<typeof projectSchema>;

export const metricsSchema = z.object({
  connections: z.number().int().optional(),
  followers: z.number().int().optional(),
  recommendations_received: z.number().int().optional(),
});
export type Metrics = z.infer<typeof metricsSchema>;

export const fieldProvenanceEntrySchema = z.object({
  source: profileSourceSchema,
  confidence: z.number().min(0).max(1),
});
export type FieldProvenanceEntry = z.infer<typeof fieldProvenanceEntrySchema>;

export const profileSnapshotSchema = z.object({
  version: z.number().int().default(1),
  source: profileSourceSchema,
  captured_at: z.string(),

  identity: identitySchema.optional(),
  about: z.string().optional(),
  experiences: z.array(experienceSchema).optional(),
  education: z.array(educationSchema).optional(),
  skills: z.array(skillSchema).optional(),
  certifications: z.array(certificationSchema).optional(),
  languages: z.array(languageSchema).optional(),
  projects: z.array(projectSchema).optional(),
  metrics: metricsSchema.optional(),

  field_provenance: z.record(z.string(), fieldProvenanceEntrySchema).default({}),
});
export type ProfileSnapshot = z.infer<typeof profileSnapshotSchema>;
