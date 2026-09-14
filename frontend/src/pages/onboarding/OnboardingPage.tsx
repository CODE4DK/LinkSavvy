import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { StepChooseSource } from "./StepChooseSource";
import { StepImport } from "./StepImport";
import { StepReview } from "./StepReview";
import { StepConfirm } from "./StepConfirm";
import {
  INITIAL_WIZARD_STATE,
  clearWizardState,
  loadWizardState,
  saveWizardState,
  type WizardState,
} from "./wizard-state";

const STEP_LABELS = ["Choose", "Import", "Review", "Confirm"] as const;

function StepIndicator({ step }: { step: WizardState["step"] }) {
  return (
    <ol className="mx-auto mb-8 flex max-w-xl items-center justify-between">
      {STEP_LABELS.map((label, index) => {
        const stepNumber = index + 1;
        const isActive = stepNumber === step;
        const isDone = stepNumber < step;
        return (
          <li key={label} className="flex flex-1 items-center gap-2">
            <span
              className={
                "flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium " +
                (isActive
                  ? "bg-primary text-primary-foreground"
                  : isDone
                    ? "bg-success/20 text-success"
                    : "bg-bg-subtle text-fg-muted")
              }
            >
              {stepNumber}
            </span>
            <span className={isActive ? "text-sm text-fg" : "text-sm text-fg-muted"}>{label}</span>
            {stepNumber < STEP_LABELS.length && <span className="flex-1 border-t border-border" />}
          </li>
        );
      })}
    </ol>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const [state, setState] = useState<WizardState>(() => loadWizardState());

  useEffect(() => {
    saveWizardState(state);
  }, [state]);

  const goToStep1 = () => setState(INITIAL_WIZARD_STATE);

  return (
    <div className="mx-auto max-w-3xl py-6">
      <StepIndicator step={state.step} />

      {state.step === 1 && (
        <StepChooseSource onChoose={(source) => setState({ ...state, source, step: 2 })} />
      )}

      {state.step === 2 && state.source && (
        <StepImport
          source={state.source}
          onBack={goToStep1}
          onImported={({ importId, draft, warnings }) =>
            setState({ ...state, importId, draft, warnings, step: 3 })
          }
        />
      )}

      {state.step === 3 && state.draft && (
        <StepReview
          draft={state.draft}
          warnings={state.warnings}
          onChange={(draft) => setState({ ...state, draft })}
          onBack={() => setState({ ...state, step: 2 })}
          onContinue={() => setState({ ...state, step: 4 })}
        />
      )}

      {state.step === 4 && state.draft && (
        <StepConfirm
          draft={state.draft}
          importId={state.importId}
          onBack={() => setState({ ...state, step: 3 })}
          onCommitted={() => {
            clearWizardState();
            navigate("/", { replace: true });
          }}
        />
      )}
    </div>
  );
}
