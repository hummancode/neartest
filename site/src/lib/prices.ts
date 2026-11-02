// Typed access to site/data/fiyatlar.json (TL levels of every chart instrument).
import raw from "../../data/fiyatlar.json";

export interface InstrumentSource { label: string; source: string; code: string | null; verified: boolean; sample: boolean }
export interface Instrument { id: string; label: string; group: string; sample: boolean; sources: InstrumentSource[] }
export interface Prices {
  generated_at: string;
  end_month: string;
  sample: boolean;
  instruments: Instrument[];
  series: Record<string, { start: string; values: number[] }>;
}
export const prices = raw as unknown as Prices;

// Ready-made comparisons: [title, bases, denominator].
export const PRESETS: [string, string[], string][] = [
  ["Otomobil, gram altın cinsinden", ["car"], "gold"],
  ["Otomobil, dolar cinsinden", ["car"], "usd"],
  ["Otomobil, asgari ücret cinsinden", ["car"], "min_wage"],
  ["Büyükşehirlerde konut, gram altın cinsinden", ["house_ist", "house_ank", "house_izm"], "gold"],
  ["İstanbul konut, reel (TÜFE'ye göre)", ["house_ist"], "cpi"],
  ["İstanbul konut, dolar cinsinden", ["house_ist"], "usd"],
  ["Konut, BIST 100 cinsinden", ["house_tr"], "bist100"],
  ["Kira, TÜFE'ye göre", ["rent"], "cpi"],
  ["Gram altın, S&P 500 cinsinden", ["gold"], "sp500"],
  ["Mevduat, altın ve borsa: reel", ["deposit", "gold", "bist100"], "cpi"],
];
