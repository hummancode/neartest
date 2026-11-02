// Typed access to site/data/durum.json (where every series comes from).
import raw from "../../data/durum.json";

export interface StatusRow {
  name: string;
  label: string;
  source: string;
  code: string | null;
  verified: boolean;
  origin: "evds" | "manual" | "sample" | "missing";
  origin_label: string;
  first_month: string | null;
  last_month: string | null;
  months: number;
  used_by: string;
}
export interface Status {
  generated_at: string;
  end_month: string;
  sample: boolean;
  counts: Record<string, number>;
  weights: { label: string; source: string; verified: boolean; sample: boolean };
  rows: StatusRow[];
}
export const status = raw as unknown as Status;
