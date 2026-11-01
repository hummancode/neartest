// Typed access to site/data/reel_faiz.json (computed in Python; the page only displays it).
import raw from "../../data/reel_faiz.json";

export interface RateRow {
  month: string;
  deposit_rate: number | null;
  credit_rate: number | null;
  cpi_12m: number | null;
  deposit_real_trailing: number | null;
  credit_real_trailing: number | null;
  deposit_rate_12m_ago: number | null;
  credit_rate_12m_ago: number | null;
  deposit_real_ex_post: number | null;
  credit_real_ex_post: number | null;
}
export interface RealRates {
  generated_at: string;
  end_month: string;
  sample: boolean;
  ex_ante: null | unknown;
  sources: Record<string, { label: string; source: string; code: string | null; verified: boolean; sample: boolean }>;
  rows: RateRow[];
}

export const realRates = raw as unknown as RealRates;
