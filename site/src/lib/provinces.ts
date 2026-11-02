// Typed access to site/data/iller.json (province factbook) and site/data/tr_iller.json (outlines).
import raw from "../../data/iller.json";
import geoRaw from "../../data/tr_iller.json";

export interface PIndicator { id: string; label: string; unit: string; group: string; source: string; kind: "observed" | "derived" | "estimate"; sample: boolean | null }
export interface PValue { value: number; year: string; sample: boolean }
export interface Province { plaka: number; name: string; region: string; values: Record<string, PValue> }
export interface Provinces {
  generated_at: string; sample: boolean; indicators: PIndicator[];
  wealth_defaults: { ownership_rate: number; dwelling_m2: number; household_deposit_share: number; household_size: number };
  provinces: Province[];
}
export const provinces = raw as unknown as Provinces;
export const geo = geoRaw as unknown as { width: number; height: number; source: string; provinces: { plaka: number; name: string; d: string; cx: number; cy: number }[] };

// Indicators that add up across provinces (share of Türkiye is meaningful).
export const ADDITIVE = new Set(["population", "gdp_mn_tl", "exports_mn_usd", "insured_employees", "companies_active",
  "companies_new", "listed_companies", "deposits_mn_tl", "loans_mn_tl", "wealth_total_bn"]);

export function formatP(unit: string, v: number): string {
  const nf = (d: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: d });
  if (unit === "kişi" || unit === "adet") return nf(0).format(v);
  if (unit === "kişi/hane") return `${nf(1).format(v)} kişi`;
  if (unit === "%") return `%${nf(1).format(v)}`;
  if (unit === "skor") return nf(2).format(v);
  if (unit === "$") return `${nf(0).format(v)} $`;
  if (unit === "TL") return `${nf(0).format(v)} TL`;
  if (unit === "milyon TL" || unit === "milyon $" || unit === "milyar TL") return `${nf(v >= 100 ? 0 : 1).format(v)} ${unit}`;
  return `${nf(2).format(v)} ${unit}`;
}
