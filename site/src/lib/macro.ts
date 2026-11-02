// Typed access to site/data/makro.json and display helpers for indicators (formatting only).
import raw from "../../data/makro.json";

export interface IndicatorSource { label: string; source: string; code: string | null; verified: boolean; sample: boolean }
export interface Indicator {
  id: string; label: string; unit: string; kind: "rate" | "level"; freq: "M" | "Q" | "A"; group: string;
  sample: boolean; sources: IndicatorSource[]; points: [string, number][];
  latest: [string, number] | null; prev_year: [string, number] | null; change_12m: number | null;
}
export interface Macro { generated_at: string; end_month: string; sample: boolean; indicators: Indicator[] }
export const macro = raw as unknown as Macro;

const MONTHS = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"];

export function periodLabel(freq: string, m: string): string {
  const y = m.slice(0, 4), mo = Number(m.slice(5));
  if (freq === "A") return y;
  if (freq === "Q") return `${y} Ç${Math.ceil(mo / 3)}`;
  return `${MONTHS[mo - 1]} ${y}`;
}

export function formatValue(unit: string, v: number): string {
  return formatRaw(unit, v).replace(/^-/, "−");
}

function formatRaw(unit: string, v: number): string {
  const nf = (d: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: d, minimumFractionDigits: d });
  if (unit === "%") return `%${nf(1).format(v)}`.replace("%-", "−%");
  if (unit === "bp") return `${nf(0).format(v)} bp`;
  if (unit === "milyar $") return `${nf(1).format(v)} milyar $`;
  if (unit === "$") return `${nf(Math.abs(v) >= 1000 ? 0 : 2).format(v)} $`;
  if (unit === "TL") return `${nf(2).format(v)} TL`;
  return nf(2).format(v);
}

export function formatChange(kind: string, unit: string, d: number | null): string {
  if (d === null) return "—";
  const sign = d > 0 ? "+" : d < 0 ? "−" : "";
  const a = Math.abs(d);
  if (kind === "level") return `${sign}%${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(a * 100)}`;
  if (unit === "bp") return `${sign}${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(a)} bp`;
  if (unit === "%") return `${sign}${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(a)} puan`;
  return `${sign}${new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(a)} ${unit}`;
}
