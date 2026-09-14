import type { ProfileSnapshot } from "@/contracts";

/** The entry method the user picked in step 1 — "upload" covers both PDF
 * and DOCX, since the user hasn't chosen a file yet; the committed
 * snapshot's actual `source` (upload_pdf vs upload_docx) comes back from
 * the server once a file is parsed. */
export type WizardSource = "linkedin_api" | "paste" | "upload" | "manual";

export interface WizardState {
  step: 1 | 2 | 3 | 4;
  source: WizardSource | null;
  importId: string | null;
  draft: ProfileSnapshot | null;
  warnings: string[];
}

export const INITIAL_WIZARD_STATE: WizardState = {
  step: 1,
  source: null,
  importId: null,
  draft: null,
  warnings: [],
};

const STORAGE_KEY = "linksavvy.onboarding-wizard";

export function loadWizardState(): WizardState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return INITIAL_WIZARD_STATE;
    const parsed = JSON.parse(raw) as Partial<WizardState>;
    return { ...INITIAL_WIZARD_STATE, ...parsed };
  } catch {
    return INITIAL_WIZARD_STATE;
  }
}

export function saveWizardState(state: WizardState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage failures (private browsing, quota, etc) — progress
    // just won't survive a refresh, which is a degraded experience, not
    // a broken one.
  }
}

export function clearWizardState(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore.
  }
}
