// Shared input parsing and display formatting for calculator pages (no calculations).
import { parseAmount } from "./card.ts";

/** TL amounts use Turkish grouping ("25.000"); rates are small numbers ("2,5", "-3"). */
export function readNumber(el: HTMLInputElement, money = false): number | null {
  const raw = el.value.trim();
  if (raw === "") return null;
  if (money) return raw === "0" ? 0 : parseAmount(raw);
  return /^-?\d+([.,]\d+)?$/.test(raw) ? Number(raw.replace(",", ".")) : null;
}

export const tl = (x: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(Math.round(x)) + " TL";
export const tl2 = (x: number) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2, minimumFractionDigits: 2 }).format(x) + " TL";
export const pct = (x: number) => (x < 0 ? "−" : "") + "%" + new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(Math.abs(x) * 100);
export const num = (x: number, d = 2) => new Intl.NumberFormat("tr-TR", { maximumFractionDigits: d }).format(x);
