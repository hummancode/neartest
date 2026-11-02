// Typed access to site/data/seviyeler.json (monthly levels for the browser calculator).
import raw from "../../data/seviyeler.json";

export interface LevelSource {
  label: string;
  source: string;
  code: string | null;
  verified: boolean;
  sample: boolean;
}
export interface Levels {
  generated_at: string;
  end_month: string;
  sample: boolean;
  sources: Record<string, LevelSource>;
  missing: string[];
  series: Record<"cpi_tr" | "usdtry" | "gold_gram_tl", Record<string, number>> & { min_wage_net?: Record<string, number> };
}

export const levels = raw as unknown as Levels;
