import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import type { WizardSource } from "./wizard-state";

export interface StepChooseSourceProps {
  onChoose: (source: WizardSource) => void;
}

interface SourceOption {
  source: WizardSource;
  title: string;
  description: string;
}

// LinkedIn is listed first as a convenience, but every option gets the
// same card treatment — same size, same weight — so it never reads as
// "the real way" with the rest as fallbacks. Parity means parity.
const OPTIONS: SourceOption[] = [
  {
    source: "linkedin_api",
    title: "Connect LinkedIn",
    description:
      "Convenient if you'd like to use it — we only ever pull what LinkedIn's official API grants us (your name and photo today). Nothing is scraped.",
  },
  {
    source: "paste",
    title: "Paste your profile",
    description: "Copy your profile text from anywhere and paste it in. We'll parse it for you.",
  },
  {
    source: "upload",
    title: "Upload a resume",
    description: "Upload a PDF or Word document and we'll extract your details automatically.",
  },
  {
    source: "manual",
    title: "Enter it yourself",
    description: "Fill in a short guided form at your own pace. Full control, no parsing needed.",
  },
];

export function StepChooseSource({ onChoose }: StepChooseSourceProps) {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-fg">How would you like to bring in your profile?</h1>
      <p className="mt-1 text-sm text-fg-muted">
        Pick whichever is easiest — every option gets you to the same place.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {OPTIONS.map((option) => (
          <button
            key={option.source}
            type="button"
            onClick={() => onChoose(option.source)}
            className="text-left"
          >
            <Card className="h-full transition-shadow hover:shadow-md hover:border-primary/40">
              <CardHeader>
                <CardTitle>{option.title}</CardTitle>
                <CardDescription>{option.description}</CardDescription>
              </CardHeader>
              <Button variant="secondary" className="pointer-events-none">
                Choose
              </Button>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}
