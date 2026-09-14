import type { Experience, Education, ProfileSnapshot, Skill } from "@/contracts";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export interface StepReviewProps {
  draft: ProfileSnapshot;
  warnings: string[];
  onChange: (next: ProfileSnapshot) => void;
  onBack: () => void;
  onContinue: () => void;
}

const LOW_CONFIDENCE_THRESHOLD = 0.7;

function useLowConfidenceSections(draft: ProfileSnapshot): Set<string> {
  const sections = new Set<string>();
  for (const [path, provenance] of Object.entries(draft.field_provenance ?? {})) {
    if (provenance.confidence < LOW_CONFIDENCE_THRESHOLD) {
      sections.add(path.replace(/^\//, ""));
    }
  }
  return sections;
}

function LowConfidenceBadge({ shown }: { shown: boolean }) {
  if (!shown) return null;
  return <Badge variant="warning">Please double-check</Badge>;
}

export function StepReview({ draft, warnings, onChange, onBack, onContinue }: StepReviewProps) {
  const lowConfidence = useLowConfidenceSections(draft);

  const updateIdentity = (patch: Partial<NonNullable<ProfileSnapshot["identity"]>>) => {
    onChange({ ...draft, identity: { ...draft.identity, ...patch } });
  };

  const updateExperience = (index: number, patch: Partial<Experience>) => {
    const experiences = [...(draft.experiences ?? [])];
    experiences[index] = { ...experiences[index], ...patch };
    onChange({ ...draft, experiences });
  };

  const removeExperience = (index: number) => {
    onChange({ ...draft, experiences: (draft.experiences ?? []).filter((_, i) => i !== index) });
  };

  const addExperience = () => {
    const experiences: Experience[] = [...(draft.experiences ?? []), {}];
    onChange({ ...draft, experiences });
  };

  const updateEducation = (index: number, patch: Partial<Education>) => {
    const education = [...(draft.education ?? [])];
    education[index] = { ...education[index], ...patch };
    onChange({ ...draft, education });
  };

  const removeEducation = (index: number) => {
    onChange({ ...draft, education: (draft.education ?? []).filter((_, i) => i !== index) });
  };

  const addEducation = () => {
    onChange({ ...draft, education: [...(draft.education ?? []), {}] });
  };

  const skillNames = (draft.skills ?? []).map((skill) => skill.name ?? "").join(", ");
  const updateSkillsFromText = (text: string) => {
    const skills: Skill[] = text
      .split(",")
      .map((name) => name.trim())
      .filter(Boolean)
      .map((name) => ({ name }));
    onChange({ ...draft, skills });
  };

  return (
    <div className="mx-auto max-w-2xl">
      <button type="button" onClick={onBack} className="mb-4 text-sm text-fg-muted hover:text-fg">
        ← Back
      </button>

      <h1 className="text-2xl font-semibold text-fg">Review and correct</h1>
      <p className="mt-1 text-sm text-fg-muted">
        Here&apos;s what we found. Fix anything that&apos;s off before continuing — you can't skip
        this step.
      </p>

      {warnings.length > 0 && (
        <Card className="mt-4 border-warning/40 bg-warning/5">
          <CardHeader>
            <CardTitle className="text-sm">We weren&apos;t sure about a few things</CardTitle>
          </CardHeader>
          <ul className="list-disc space-y-1 pl-5 text-sm text-fg-muted">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Card>
      )}

      <div className="mt-6 flex flex-col gap-6">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Identity</CardTitle>
            <LowConfidenceBadge shown={lowConfidence.has("identity")} />
          </CardHeader>
          <div className="flex flex-col gap-3">
            <Input
              label="Full name"
              value={draft.identity?.full_name ?? ""}
              onChange={(e) => updateIdentity({ full_name: e.target.value })}
            />
            <Input
              label="Headline"
              value={draft.identity?.headline ?? ""}
              onChange={(e) => updateIdentity({ headline: e.target.value })}
            />
            <Input
              label="Location"
              value={draft.identity?.location ?? ""}
              onChange={(e) => updateIdentity({ location: e.target.value })}
            />
            <Input
              label="Custom URL"
              value={draft.identity?.custom_url ?? ""}
              onChange={(e) => updateIdentity({ custom_url: e.target.value })}
            />
          </div>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>About</CardTitle>
            <LowConfidenceBadge shown={lowConfidence.has("about")} />
          </CardHeader>
          <textarea
            value={draft.about ?? ""}
            onChange={(e) => onChange({ ...draft, about: e.target.value })}
            rows={5}
            className="w-full rounded-md border border-border bg-bg p-3 text-sm text-fg"
          />
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Experience</CardTitle>
            <LowConfidenceBadge shown={lowConfidence.has("experiences")} />
          </CardHeader>
          <div className="flex flex-col gap-4">
            {(draft.experiences ?? []).map((experience, index) => (
              <div key={index} className="rounded-md border border-border p-3">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <Input
                    label="Title"
                    value={experience.title ?? ""}
                    onChange={(e) => updateExperience(index, { title: e.target.value })}
                  />
                  <Input
                    label="Company"
                    value={experience.company ?? ""}
                    onChange={(e) => updateExperience(index, { company: e.target.value })}
                  />
                </div>
                <div className="mt-3">
                  <label className="flex items-center gap-2 text-sm text-fg">
                    <input
                      type="checkbox"
                      checked={experience.is_current ?? false}
                      onChange={(e) => updateExperience(index, { is_current: e.target.checked })}
                    />
                    I currently work here
                  </label>
                </div>
                <div className="mt-3">
                  <label className="mb-1 block text-sm font-medium text-fg">Bullets (one per line)</label>
                  <textarea
                    value={(experience.bullets ?? []).join("\n")}
                    onChange={(e) =>
                      updateExperience(index, {
                        bullets: e.target.value.split("\n").filter((line) => line.trim()),
                      })
                    }
                    rows={3}
                    className="w-full rounded-md border border-border bg-bg p-2 text-sm text-fg"
                  />
                </div>
                <div className="mt-3">
                  <Button variant="secondary" size="sm" onClick={() => removeExperience(index)}>
                    Remove
                  </Button>
                </div>
              </div>
            ))}
            <div>
              <Button variant="secondary" size="sm" onClick={addExperience}>
                Add experience
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Education</CardTitle>
            <LowConfidenceBadge shown={lowConfidence.has("education")} />
          </CardHeader>
          <div className="flex flex-col gap-4">
            {(draft.education ?? []).map((education, index) => (
              <div key={index} className="rounded-md border border-border p-3">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <Input
                    label="School"
                    value={education.school ?? ""}
                    onChange={(e) => updateEducation(index, { school: e.target.value })}
                  />
                  <Input
                    label="Degree"
                    value={education.degree ?? ""}
                    onChange={(e) => updateEducation(index, { degree: e.target.value })}
                  />
                </div>
                <div className="mt-3">
                  <Button variant="secondary" size="sm" onClick={() => removeEducation(index)}>
                    Remove
                  </Button>
                </div>
              </div>
            ))}
            <div>
              <Button variant="secondary" size="sm" onClick={addEducation}>
                Add education
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Skills</CardTitle>
            <LowConfidenceBadge shown={lowConfidence.has("skills")} />
          </CardHeader>
          <CardDescription>Comma-separated.</CardDescription>
          <Input
            value={skillNames}
            onChange={(e) => updateSkillsFromText(e.target.value)}
            placeholder="Python, Distributed Systems, SQL"
          />
        </Card>
      </div>

      <div className="mt-8 flex justify-end">
        <Button onClick={onContinue}>Continue</Button>
      </div>
    </div>
  );
}
