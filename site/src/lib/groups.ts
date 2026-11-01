// Typed access to site/data/tufe_gruplari.json (CPI groups for the personal inflation page).
import raw from "../../data/tufe_gruplari.json";

export interface Group {
  id: string;
  label: string;
  weight: number | null;
  change_12m: number | null;
  sample: boolean;
}
export interface CpiGroups {
  generated_at: string;
  end_month: string;
  start_month: string;
  headline_change_12m: number;
  sample: boolean;
  weights_sample: boolean;
  sources: {
    cpi_tr: { label: string; source: string; code: string | null; verified: boolean; sample: boolean };
    groups: { label: string; source: string; codes: Record<string, string | null>; verified: boolean; sample: boolean };
    weights: { label: string; source: string; code: string | null; verified: boolean; sample: boolean };
  };
  groups: Group[];
}

export const cpiGroups = raw as unknown as CpiGroups;
