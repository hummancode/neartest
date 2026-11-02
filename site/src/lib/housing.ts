// Typed access to site/data/konut.json (computed in Python).
import raw from "../../data/konut.json";
import type { Window } from "./data.ts";

export interface HouseWindow extends Window { gold: number | null; gold_annual: number | null }
export interface CitySource { label: string; series: string; sample: boolean; windows: HouseWindow[] }
export interface City {
  id: string;
  label: string;
  sources: Record<string, CitySource>;
  rent_12m_betam: number | null;
  house_12m: Record<string, number | null>;
}
export interface Housing {
  generated_at: string;
  end_month: string;
  sample: boolean;
  cities: City[];
  reference: { cpi_12m: number | null; rent_12m: number | null; deposit_rate: number | null; credit_rate: number | null; sample: boolean };
  sources: Record<string, { label: string; source: string; code: string | null; verified: boolean; sample: boolean }>;
}
export const housing = raw as unknown as Housing;
