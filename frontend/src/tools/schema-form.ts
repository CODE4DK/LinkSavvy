/**
 * Turns a tool's JSON Schema (as returned by `GET /api/v1/tools`, straight
 * from the Pydantic input model's `model_json_schema()`) into a form
 * ToolRunner can render and validate generically -- no tool ever has
 * bespoke form code, so any widget behaviour it needs has to be
 * expressible as a JSON Schema convention every tool's definition can opt
 * into. That's the contract this module owns:
 *
 * - `format: "textarea"`           -> a multi-line text field
 * - `format: "profile_section"`    -> a picker over one of the user's own
 *   profile sections; the field's own `x-profile-section-kind` (e.g.
 *   `"experience"`) says which section list to offer
 * - `x-default-source`             -> prefill the field from the user's
 *   profile (e.g. `"headline"`) rather than leaving it blank
 * - a plain JSON Schema `enum`     -> a single-select
 * - `type: "array"` with an `items.enum` -> a multi-select
 * - `type: "integer" | "number"`   -> a number field
 * - `type: "boolean"`              -> a checkbox
 * - anything else `type: "string"` -> a single-line text field
 *
 * Every one of these is a switch on the *shape* of a field's own schema,
 * never on a tool or field name -- that's what keeps ToolRunner itself
 * free of tool-specific branching while still letting a tool ask for a
 * richer widget than a bare string input.
 */

import { z } from "zod";
import type { ProfileSnapshot } from "@/contracts";

export interface JsonSchemaProperty {
  type?: "string" | "number" | "integer" | "boolean" | "array" | "object";
  enum?: (string | number)[];
  items?: JsonSchemaProperty;
  format?: string;
  title?: string;
  description?: string;
  default?: unknown;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  "x-default-source"?: string;
  "x-profile-section-kind"?: string;
}

export interface JsonSchemaObject {
  type?: "object";
  properties?: Record<string, JsonSchemaProperty>;
  required?: string[];
}

export type FieldWidget =
  "string" | "longtext" | "enum" | "multiselect" | "number" | "boolean" | "profile_section";

export interface FieldDescriptor {
  key: string;
  property: JsonSchemaProperty;
  widget: FieldWidget;
  required: boolean;
  label: string;
}

export function widgetForProperty(property: JsonSchemaProperty): FieldWidget {
  if (property.format === "profile_section") return "profile_section";
  if (property.type === "boolean") return "boolean";
  if (property.type === "integer" || property.type === "number") return "number";
  if (property.type === "array") return "multiselect";
  if (property.enum) return "enum";
  if (property.format === "textarea") return "longtext";
  return "string";
}

function labelFor(key: string, property: JsonSchemaProperty): string {
  if (property.title) return property.title;
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function fieldsForSchema(schema: JsonSchemaObject): FieldDescriptor[] {
  const properties = schema.properties ?? {};
  const required = new Set(schema.required ?? []);
  return Object.entries(properties).map(([key, property]) => ({
    key,
    property,
    widget: widgetForProperty(property),
    required: required.has(key),
    label: labelFor(key, property),
  }));
}

function zodFieldFor(field: FieldDescriptor): z.ZodTypeAny {
  const { property, widget, required, label } = field;

  let base: z.ZodTypeAny;
  switch (widget) {
    case "boolean":
      base = z.boolean();
      break;
    case "number": {
      let num = z.number();
      if (property.minimum !== undefined) num = num.min(property.minimum);
      if (property.maximum !== undefined) num = num.max(property.maximum);
      base = num;
      break;
    }
    case "multiselect":
      base = z.array(z.string());
      break;
    case "enum": {
      const options = (property.enum ?? []).map(String);
      base = options.length > 0 ? z.enum(options as [string, ...string[]]) : z.string();
      break;
    }
    default: {
      let str = z.string();
      if (required) str = str.min(1, `${label} is required.`);
      if (property.maxLength !== undefined) {
        str = str.max(
          property.maxLength,
          `${label} must be ${property.maxLength} characters or fewer.`,
        );
      }
      base = str;
    }
  }

  if (!required) {
    return base.optional().or(z.literal(""));
  }
  return base;
}

/** Builds a Zod object schema mirroring the tool's JSON Schema closely
 * enough for client-side validation -- not a full JSON Schema
 * interpreter, just the subset of constraints our own Pydantic models
 * actually emit (required, enum, min/max length, min/max value). */
export function zodSchemaForTool(
  schema: JsonSchemaObject,
): z.ZodObject<Record<string, z.ZodTypeAny>> {
  const shape: Record<string, z.ZodTypeAny> = {};
  for (const field of fieldsForSchema(schema)) {
    shape[field.key] = zodFieldFor(field);
  }
  return z.object(shape);
}

export function defaultValueFor(field: FieldDescriptor): unknown {
  if (field.property.default !== undefined) return field.property.default;
  switch (field.widget) {
    case "boolean":
      return false;
    case "multiselect":
      return [];
    case "number":
      return "";
    default:
      return "";
  }
}

/** Profile-backed defaults for a field declaring `x-default-source` --
 * a small, named lookup table (not a switch on tool or field name) that
 * every tool's input schema can opt a text field into. */
const PROFILE_DEFAULT_SOURCES: Record<string, (snapshot: ProfileSnapshot) => string | undefined> = {
  full_name: (snapshot) => snapshot.identity?.full_name,
  headline: (snapshot) => snapshot.identity?.headline,
  about: (snapshot) => snapshot.about,
};

export function profileDefaultFor(
  field: FieldDescriptor,
  snapshot: ProfileSnapshot | null,
): string | undefined {
  const source = field.property["x-default-source"];
  if (!source || !snapshot) return undefined;
  return PROFILE_DEFAULT_SOURCES[source]?.(snapshot);
}

export interface ProfileSectionOption {
  value: string;
  label: string;
}

/** Option lists for the `profile_section` picker widget, keyed by the
 * field's own `x-profile-section-kind` -- again a lookup table over the
 * *kind* of section being picked, not over which tool asked for it. */
const PROFILE_SECTION_OPTIONS: Record<
  string,
  (snapshot: ProfileSnapshot) => ProfileSectionOption[]
> = {
  experience: (snapshot) =>
    (snapshot.experiences ?? []).map((experience, index) => ({
      value: String(index),
      label:
        [experience.title, experience.company].filter(Boolean).join(" at ") ||
        `Experience ${index + 1}`,
    })),
};

export function profileSectionOptionsFor(
  field: FieldDescriptor,
  snapshot: ProfileSnapshot | null,
): ProfileSectionOption[] {
  const kind = field.property["x-profile-section-kind"];
  if (!kind || !snapshot) return [];
  return PROFILE_SECTION_OPTIONS[kind]?.(snapshot) ?? [];
}

/** Turns form state (always plain strings/booleans/arrays, since that's
 * all HTML form controls produce) into the JSON body a tool's Pydantic
 * input model expects: a blank optional field is omitted entirely
 * (letting the model apply its own default) rather than sent as `""`,
 * and any field backed by a numeric JSON Schema type -- a plain number
 * field or a `profile_section` picker over a numeric index alike -- is
 * coerced to a real number. */
export function buildSubmissionPayload(
  schema: JsonSchemaObject,
  values: Record<string, unknown>,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  for (const field of fieldsForSchema(schema)) {
    const value = values[field.key];
    if (value === undefined) continue;
    if (value === "" && !field.required) continue;
    const isNumeric = field.property.type === "integer" || field.property.type === "number";
    payload[field.key] = isNumeric && value !== "" ? Number(value) : value;
  }
  return payload;
}

export function usesProfileData(schema: JsonSchemaObject): boolean {
  return fieldsForSchema(schema).some(
    (field) => field.property["x-default-source"] || field.widget === "profile_section",
  );
}
