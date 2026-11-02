// Typed access to site/data/iller.json (province factbook) and site/data/tr_iller.json (outlines).
import raw from "../../data/iller.json";
import geoRaw from "../../data/tr_iller.json";

export interface PIndicator { id: string; label: string; unit: string; group: string; source: string; kind: "observed" | "derived" | "estimate"; sample: boolean | null }
export interface PValue { value: number; year: string; sample: boolean }
export interface Company { code: string; name: string; sector: string }
export interface StructItem { name: string; value: number; share: number; lq?: number }
export interface Structure { title: string; unit: string; source: string; year: string; sample: boolean; items: StructItem[] }
export interface Province {
  plaka: number; name: string; region: string; values: Record<string, PValue>; companies: Company[];
  structure: Record<string, Structure>;
  summary: { specialization?: string[]; top_exports?: string[]; top_markets?: string[] };
  history: Record<string, { points: [string, number][]; sample: boolean }>;
}
export interface Provinces {
  generated_at: string; sample: boolean; indicators: PIndicator[];
  wealth_defaults: { ownership_rate: number; dwelling_m2: number; household_deposit_share: number; household_size: number;
    inequality_multiplier: number; gold_total_tonnes: number; gold_beta: number };
  gold_gram_tl: number | null; has_company_list: boolean; population_history_sample?: boolean;
  provinces: Province[];
}
export const provinces = raw as unknown as Provinces;
export const geo = geoRaw as unknown as { width: number; height: number; source: string; provinces: { plaka: number; name: string; d: string; cx: number; cy: number }[] };

// Indicators that add up across provinces (share of Türkiye is meaningful).
export const ADDITIVE = new Set(["population", "gdp_mn_tl", "exports_mn_usd", "insured_employees", "companies_active",
  "companies_new", "listed_companies", "deposits_mn_tl", "loans_mn_tl", "wealth_total_bn", "house_sales", "cars",
  "gold_tonnes", "gold_value_bn", "population_change_10y"]);

export function formatP(unit: string, v: number): string {
  const nf = (d: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: d });
  if (unit === "kişi" || unit === "adet") return nf(0).format(v);
  if (unit === "kişi/hane") return `${nf(1).format(v)} kişi`;
  if (unit === "yıl") return `${nf(1).format(v)} yıl`;
  if (unit === "katsayı") return nf(3).format(v);
  if (unit === "ton") return `${nf(v >= 100 ? 0 : 1).format(v)} ton`;
  if (unit === "gram") return `${nf(0).format(v)} g`;
  if (unit === "%") return `${v < 0 ? "−" : ""}%${nf(1).format(Math.abs(v))}`;
  if (unit === "kişi/km²") return `${nf(v >= 10 ? 0 : 1).format(v)} kişi/km²`;
  if (unit === "skor") return nf(2).format(v);
  if (unit === "$") return `${nf(0).format(v)} $`;
  if (unit === "TL") return `${nf(0).format(v)} TL`;
  if (unit === "milyon TL" || unit === "milyon $" || unit === "milyar TL") return `${nf(v >= 100 ? 0 : 1).format(v)} ${unit}`;
  return `${nf(2).format(v)} ${unit}`;
}
