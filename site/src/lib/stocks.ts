// Typed access to site/data/borsa.json (computed in Python).
import raw from "../../data/borsa.json";
import type { HouseWindow } from "./housing.ts";

export interface StockRow {
  id: string; ticker: string; label: string; sample: boolean; last_month: string; windows: HouseWindow[];
  source: { label: string; source: string; code: string | null; verified: boolean; sample: boolean };
}
export interface Stocks { generated_at: string; end_month: string; sample: boolean; stock_count: number; rows: StockRow[] }
export const stocks = raw as unknown as Stocks;
