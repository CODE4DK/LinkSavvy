import { describe, expect, it } from "vitest";
import type { ProfileSnapshot } from "@/contracts";
import {
  buildSubmissionPayload,
  defaultValueFor,
  fieldsForSchema,
  profileDefaultFor,
  profileSectionOptionsFor,
  usesProfileData,
  widgetForProperty,
  zodSchemaForTool,
  type FieldDescriptor,
  type JsonSchemaObject,
} from "./schema-form";

function fieldAt(schema: JsonSchemaObject, index = 0): FieldDescriptor {
  const field = fieldsForSchema(schema)[index];
  if (!field) throw new Error(`no field at index ${index}`);
  return field;
}

describe("widgetForProperty", () => {
  it("maps boolean, number, array-of-enum, enum, textarea, profile_section and plain string", () => {
    expect(widgetForProperty({ type: "boolean" })).toBe("boolean");
    expect(widgetForProperty({ type: "integer" })).toBe("number");
    expect(widgetForProperty({ type: "number" })).toBe("number");
    expect(widgetForProperty({ type: "array", items: { type: "string", enum: ["a", "b"] } })).toBe(
      "multiselect",
    );
    expect(widgetForProperty({ type: "string", enum: ["a", "b"] })).toBe("enum");
    expect(widgetForProperty({ type: "string", format: "textarea" })).toBe("longtext");
    expect(widgetForProperty({ type: "string", format: "profile_section" })).toBe(
      "profile_section",
    );
    expect(widgetForProperty({ type: "string" })).toBe("string");
  });

  it("prioritises profile_section over an underlying numeric type", () => {
    expect(widgetForProperty({ type: "integer", format: "profile_section" })).toBe(
      "profile_section",
    );
  });
});

describe("fieldsForSchema", () => {
  it("derives a title-cased label from the key when no title is given", () => {
    const schema: JsonSchemaObject = { properties: { target_role: { type: "string" } } };
    expect(fieldAt(schema).label).toBe("Target Role");
  });

  it("prefers an explicit title", () => {
    const schema: JsonSchemaObject = {
      properties: { target_role: { type: "string", title: "Role you're targeting" } },
    };
    expect(fieldAt(schema).label).toBe("Role you're targeting");
  });

  it("marks fields listed in required", () => {
    const schema: JsonSchemaObject = {
      properties: { a: { type: "string" }, b: { type: "string" } },
      required: ["a"],
    };
    expect(fieldAt(schema, 0).required).toBe(true);
    expect(fieldAt(schema, 1).required).toBe(false);
  });
});

describe("zodSchemaForTool", () => {
  const schema: JsonSchemaObject = {
    properties: {
      name: { type: "string", maxLength: 5 },
      note: { type: "string" },
      count: { type: "integer", minimum: 1, maximum: 3 },
    },
    required: ["name"],
  };

  it("rejects a blank required string field", () => {
    const result = zodSchemaForTool(schema).safeParse({ name: "", note: "", count: 2 });
    expect(result.success).toBe(false);
  });

  it("enforces maxLength on a required string field", () => {
    const result = zodSchemaForTool(schema).safeParse({ name: "toolong", note: "", count: 2 });
    expect(result.success).toBe(false);
  });

  it("accepts a blank optional string field", () => {
    const result = zodSchemaForTool(schema).safeParse({ name: "ok", note: "", count: 2 });
    expect(result.success).toBe(true);
  });

  it("enforces numeric bounds", () => {
    expect(zodSchemaForTool(schema).safeParse({ name: "ok", note: "", count: 10 }).success).toBe(
      false,
    );
    expect(zodSchemaForTool(schema).safeParse({ name: "ok", note: "", count: 2 }).success).toBe(
      true,
    );
  });
});

describe("defaultValueFor", () => {
  it("uses the schema's own default when present", () => {
    const field = fieldAt({ properties: { flag: { type: "boolean", default: true } } });
    expect(defaultValueFor(field)).toBe(true);
  });

  it("falls back to a widget-appropriate blank value", () => {
    const schema: JsonSchemaObject = {
      properties: {
        flag: { type: "boolean" },
        tags: { type: "array", items: { type: "string", enum: ["a"] } },
        name: { type: "string" },
      },
    };
    expect(defaultValueFor(fieldAt(schema, 0))).toBe(false);
    expect(defaultValueFor(fieldAt(schema, 1))).toEqual([]);
    expect(defaultValueFor(fieldAt(schema, 2))).toBe("");
  });
});

function makeSnapshot(overrides: Partial<ProfileSnapshot>): ProfileSnapshot {
  return {
    version: 1,
    source: "manual",
    captured_at: "2026-01-01T00:00:00Z",
    field_provenance: {},
    ...overrides,
  };
}

describe("profileDefaultFor", () => {
  it("returns undefined without a snapshot or an x-default-source", () => {
    const field = fieldAt({ properties: { headline: { type: "string" } } });
    expect(profileDefaultFor(field, null)).toBeUndefined();
    expect(profileDefaultFor(field, makeSnapshot({}))).toBeUndefined();
  });

  it("pulls the matching profile field for a declared source", () => {
    const field = fieldAt({
      properties: { headline: { type: "string", "x-default-source": "headline" } },
    });
    const snapshot = makeSnapshot({ identity: { headline: "Staff Engineer" } });
    expect(profileDefaultFor(field, snapshot)).toBe("Staff Engineer");
  });
});

describe("profileSectionOptionsFor", () => {
  it("lists the user's experiences for an experience-kind picker", () => {
    const field = fieldAt({
      properties: {
        experience_index: {
          type: "integer",
          format: "profile_section",
          "x-profile-section-kind": "experience",
        },
      },
    });
    const snapshot = makeSnapshot({
      experiences: [
        { title: "Engineer", company: "Acme" },
        { title: "", company: "" },
      ],
    });
    const options = profileSectionOptionsFor(field, snapshot);
    expect(options).toEqual([
      { value: "0", label: "Engineer at Acme" },
      { value: "1", label: "Experience 2" },
    ]);
  });

  it("returns no options without a snapshot", () => {
    const field = fieldAt({
      properties: {
        experience_index: {
          type: "integer",
          format: "profile_section",
          "x-profile-section-kind": "experience",
        },
      },
    });
    expect(profileSectionOptionsFor(field, null)).toEqual([]);
  });
});

describe("usesProfileData", () => {
  it("is true when any field declares x-default-source or a profile_section picker", () => {
    expect(usesProfileData({ properties: { a: { type: "string" } } })).toBe(false);
    expect(
      usesProfileData({ properties: { a: { type: "string", "x-default-source": "headline" } } }),
    ).toBe(true);
    expect(
      usesProfileData({ properties: { a: { type: "string", format: "profile_section" } } }),
    ).toBe(true);
  });
});

describe("buildSubmissionPayload", () => {
  const schema: JsonSchemaObject = {
    properties: {
      required_text: { type: "string" },
      optional_text: { type: "string" },
      index: { type: "integer", format: "profile_section", "x-profile-section-kind": "experience" },
    },
    required: ["required_text"],
  };

  it("omits a blank optional field rather than sending an empty string", () => {
    const payload = buildSubmissionPayload(schema, {
      required_text: "hi",
      optional_text: "",
      index: "1",
    });
    expect(payload).toEqual({ required_text: "hi", index: 1 });
  });

  it("coerces a numeric-typed field even when its widget is profile_section", () => {
    const payload = buildSubmissionPayload(schema, {
      required_text: "hi",
      optional_text: "note",
      index: "2",
    });
    expect(payload.index).toBe(2);
    expect(typeof payload.index).toBe("number");
  });
});
