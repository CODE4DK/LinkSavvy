/**
 * Hand-maintained Zod mirror of backend/app/career/schema.py's
 * ResumeDocument. Same rationale as profile-schema.ts: the web app
 * needs to validate and let a user correct a parsed resume draft
 * client-side (the mandatory review step before a resume is committed)
 * rather than just type request/response bodies.
 *
 * Every field is optional/defaulted, matching the Python side.
 */

import { z } from "zod";
import { datePartSchema } from "./profile-schema";

export const resumeSourceSchema = z.enum(["upload", "built", "imported_from_profile"]);
export type ResumeSource = z.infer<typeof resumeSourceSchema>;

export const provenanceSourceSchema = z.enum([
  "deterministic_parse",
  "ai_resolved",
  "user_edited",
  "built",
  "imported_from_profile",
]);
export type ProvenanceSource = z.infer<typeof provenanceSourceSchema>;

export const resumeContactSchema = z.object({
  full_name: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  location: z.string().optional(),
  linkedin_url: z.string().optional(),
  website_url: z.string().optional(),
});
export type ResumeContact = z.infer<typeof resumeContactSchema>;

export const resumeExperienceSchema = z.object({
  company: z.string().optional(),
  title: z.string().optional(),
  location: z.string().optional(),
  start: datePartSchema.optional(),
  end: datePartSchema.optional(),
  is_current: z.boolean().optional(),
  bullets: z.array(z.string()).default([]),
  technologies: z.array(z.string()).default([]),
});
export type ResumeExperience = z.infer<typeof resumeExperienceSchema>;

export const resumeEducationSchema = z.object({
  school: z.string().optional(),
  degree: z.string().optional(),
  field: z.string().optional(),
  start: datePartSchema.optional(),
  end: datePartSchema.optional(),
  description: z.string().optional(),
});
export type ResumeEducation = z.infer<typeof resumeEducationSchema>;

export const resumeSkillsSchema = z.object({
  technical: z.array(z.string()).default([]),
  tools: z.array(z.string()).default([]),
  soft: z.array(z.string()).default([]),
});
export type ResumeSkills = z.infer<typeof resumeSkillsSchema>;

export const resumeCertificationSchema = z.object({
  name: z.string().optional(),
  issuer: z.string().optional(),
  issued: datePartSchema.optional(),
  credential_id: z.string().optional(),
  url: z.string().optional(),
});
export type ResumeCertification = z.infer<typeof resumeCertificationSchema>;

export const resumeProjectSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  url: z.string().optional(),
  technologies: z.array(z.string()).default([]),
});
export type ResumeProject = z.infer<typeof resumeProjectSchema>;

export const resumeAwardSchema = z.object({
  name: z.string().optional(),
  issuer: z.string().optional(),
  date: datePartSchema.optional(),
  description: z.string().optional(),
});
export type ResumeAward = z.infer<typeof resumeAwardSchema>;

export const resumePublicationSchema = z.object({
  title: z.string().optional(),
  publisher: z.string().optional(),
  date: datePartSchema.optional(),
  url: z.string().optional(),
  description: z.string().optional(),
});
export type ResumePublication = z.infer<typeof resumePublicationSchema>;

export const resumeCustomSectionSchema = z.object({
  heading: z.string(),
  bullets: z.array(z.string()).default([]),
});
export type ResumeCustomSection = z.infer<typeof resumeCustomSectionSchema>;

export const resumeFieldProvenanceSchema = z.object({
  source: provenanceSourceSchema,
  confidence: z.number().min(0).max(1),
});
export type ResumeFieldProvenance = z.infer<typeof resumeFieldProvenanceSchema>;

export const resumeDocumentSchema = z.object({
  version: z.number().int().default(1),
  source: resumeSourceSchema,
  contact: resumeContactSchema.optional(),
  summary: z.string().optional(),
  experiences: z.array(resumeExperienceSchema).default([]),
  education: z.array(resumeEducationSchema).default([]),
  skills: resumeSkillsSchema.optional(),
  certifications: z.array(resumeCertificationSchema).default([]),
  projects: z.array(resumeProjectSchema).default([]),
  awards: z.array(resumeAwardSchema).default([]),
  publications: z.array(resumePublicationSchema).default([]),
  custom_sections: z.array(resumeCustomSectionSchema).default([]),
  field_provenance: z.record(z.string(), resumeFieldProvenanceSchema).default({}),
});
export type ResumeDocument = z.infer<typeof resumeDocumentSchema>;
