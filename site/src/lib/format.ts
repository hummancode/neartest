// Display formatting only. No financial calculation happens here.

const MONTHS_TR = [
  "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
];

export function monthName(m: number): string {
  return MONTHS_TR[m - 1];
}

/** "2026-09" -> "Eylül 2026" */
export function monthLabel(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  return `${MONTHS_TR[m - 1]} ${y}`;
}

const pctFmt = new Intl.NumberFormat("tr-TR", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: "exceptZero",
});

/** 0.1234 -> "+%12,3" (Turkish puts % before the number). */
export function pct(x: number | null | undefined): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "—";
  return pctFmt.format(x);
}

const tlFmt = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const numFmt2 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });

export function tl(x: number): string {
  return `${tlFmt.format(Math.round(x))} TL`;
}

export function num2(x: number): string {
  return numFmt2.format(x);
}

const pctPlainFmt = new Intl.NumberFormat("tr-TR", { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 });

/** Like pct() but without a forced "+" sign (for levels such as inflation rates or weights). */
export function pctPlain(x: number | null | undefined): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "—";
  return pctPlainFmt.format(x);
}
