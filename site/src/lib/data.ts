// Typed access to the JSON produced by pipeline/build.py. Read at build time.
import raw from "../../data/reel_tablo.json";

export interface Window {
  years: number;
  nominal_tl: number;
  usd: number;
  real_tl: number;
  nominal_tl_annual: number;
  usd_annual: number;
  real_tl_annual: number;
}
export interface Row {
  id: string;
  label: string;
  sample: boolean;
  windows: Window[];
  real_trend_5y: number[];
}
export interface Source {
  label: string;
  source: string;
  code: string | null;
  verified: boolean;
  sample: boolean;
}
export interface ReelTablo {
  generated_at: string;
  end_month: string;
  sample: boolean;
  sources: Record<string, Source>;
  notes: string[];
  rows: Row[];
}

export const tablo = raw as unknown as ReelTablo;
export const YEARS = [1, 3, 5, 10] as const;
