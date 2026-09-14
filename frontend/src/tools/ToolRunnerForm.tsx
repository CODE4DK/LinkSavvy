/**
 * Renders a tool's input form purely from its JSON Schema -- every branch
 * here is on `FieldWidget` (a structural property of one field's schema,
 * see schema-form.ts), never on a tool id or a field name. Adding a tool
 * never means touching this file; it means shaping the tool's Pydantic
 * input model so its fields resolve to the widget it wants.
 */

import { useId } from "react";
import type { ProfileSnapshot } from "@/contracts";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import {
  fieldsForSchema,
  profileSectionOptionsFor,
  type FieldDescriptor,
  type JsonSchemaObject,
} from "./schema-form";

export interface ToolRunnerFormProps {
  schema: JsonSchemaObject;
  values: Record<string, unknown>;
  errors: Record<string, string>;
  onChange: (key: string, value: unknown) => void;
  snapshot: ProfileSnapshot | null;
  disabled?: boolean;
}

function StringField({ field, value, error, disabled, onChange }: FieldProps) {
  return (
    <Input
      label={field.label}
      value={typeof value === "string" ? value : ""}
      onChange={(e) => onChange(e.target.value)}
      error={error}
      disabled={disabled}
      required={field.required}
    />
  );
}

function LongTextField({ field, value, error, disabled, onChange }: FieldProps) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-fg">
        {field.label}
      </label>
      <textarea
        id={id}
        rows={4}
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        required={field.required}
        className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg disabled:cursor-not-allowed disabled:opacity-50"
      />
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  );
}

function NumberField({ field, value, error, disabled, onChange }: FieldProps) {
  return (
    <Input
      type="number"
      label={field.label}
      value={typeof value === "number" || typeof value === "string" ? value : ""}
      onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
      error={error}
      disabled={disabled}
      required={field.required}
    />
  );
}

function BooleanField({ field, value, disabled, onChange }: FieldProps) {
  return (
    <label className="flex items-center gap-2 text-sm text-fg">
      <input
        type="checkbox"
        checked={value === true}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="h-4 w-4 rounded border-border"
      />
      {field.label}
    </label>
  );
}

function EnumField({ field, value, error, disabled, onChange }: FieldProps) {
  const options = (field.property.enum ?? []).map(String);
  return (
    <Select
      label={field.label}
      value={typeof value === "string" ? value : ""}
      onChange={(e) => onChange(e.target.value)}
      error={error}
      disabled={disabled}
    >
      <option value="" disabled>
        Choose one…
      </option>
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </Select>
  );
}

function MultiSelectField({ field, value, disabled, onChange }: FieldProps) {
  const options = (field.property.items?.enum ?? []).map(String);
  const selected = Array.isArray(value) ? value.map(String) : [];
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-fg">{field.label}</span>
      <div className="flex flex-wrap gap-3">
        {options.map((option) => (
          <label key={option} className="flex items-center gap-1.5 text-sm text-fg">
            <input
              type="checkbox"
              checked={selected.includes(option)}
              disabled={disabled}
              onChange={(e) => {
                const next = e.target.checked
                  ? [...selected, option]
                  : selected.filter((item) => item !== option);
                onChange(next);
              }}
              className="h-4 w-4 rounded border-border"
            />
            {option}
          </label>
        ))}
      </div>
    </div>
  );
}

function ProfileSectionField({
  field,
  value,
  error,
  disabled,
  onChange,
  snapshot,
}: FieldProps & { snapshot: ProfileSnapshot | null }) {
  const options = profileSectionOptionsFor(field, snapshot);
  return (
    <Select
      label={field.label}
      value={typeof value === "string" ? value : ""}
      onChange={(e) => onChange(e.target.value)}
      error={error}
      disabled={disabled || options.length === 0}
    >
      <option value="" disabled>
        {options.length === 0 ? "No profile data available yet" : "Choose one…"}
      </option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </Select>
  );
}

interface FieldProps {
  field: FieldDescriptor;
  value: unknown;
  error?: string;
  disabled?: boolean;
  onChange: (value: unknown) => void;
}

export function ToolRunnerForm({
  schema,
  values,
  errors,
  onChange,
  snapshot,
  disabled,
}: ToolRunnerFormProps) {
  const fields = fieldsForSchema(schema);

  return (
    <div className="flex flex-col gap-4">
      {fields.map((field) => {
        const shared: FieldProps = {
          field,
          value: values[field.key],
          error: errors[field.key],
          disabled,
          onChange: (value) => onChange(field.key, value),
        };
        switch (field.widget) {
          case "longtext":
            return <LongTextField key={field.key} {...shared} />;
          case "number":
            return <NumberField key={field.key} {...shared} />;
          case "boolean":
            return <BooleanField key={field.key} {...shared} />;
          case "enum":
            return <EnumField key={field.key} {...shared} />;
          case "multiselect":
            return <MultiSelectField key={field.key} {...shared} />;
          case "profile_section":
            return <ProfileSectionField key={field.key} {...shared} snapshot={snapshot} />;
          default:
            return <StringField key={field.key} {...shared} />;
        }
      })}
    </div>
  );
}
