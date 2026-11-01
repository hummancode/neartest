// TypeScript port of reel/engine.py, for in-browser calculators.
//
// Must stay formula-for-formula identical to the Python engine. Both are run
// against the same hand-computed cases in tests/cases.json:
//   Python:     pytest tests/test_shared_cases.py
//   TypeScript: cd site && npm test
//
// Plain TypeScript only (no enums, no parameter properties) so Node can run
// it directly with type stripping.

export class SeriesError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SeriesError";
  }
}

export type Series = Record<string, number>;

// --- scalar building blocks ------------------------------------------------

export function totalReturn(startValue: number, endValue: number): number {
  if (startValue <= 0) throw new SeriesError(`start value must be positive, got ${startValue}`);
  return endValue / startValue - 1.0;
}

export function annualize(total: number, years: number): number {
  if (years <= 0) throw new SeriesError(`years must be positive, got ${years}`);
  if (total <= -1.0) return -1.0;
  return (1.0 + total) ** (1.0 / years) - 1.0;
}

/** Fisher relation: (1 + n) / (1 + i) - 1. */
export function realReturn(nominal: number, inflation: number): number {
  if (inflation <= -1.0) throw new SeriesError(`inflation must be > -100 %, got ${inflation}`);
  return (1.0 + nominal) / (1.0 + inflation) - 1.0;
}

/** Return measured in a foreign currency; fxChange = change of the TL price of one unit. */
export function currencyReturn(localReturn: number, fxChange: number): number {
  return realReturn(localReturn, fxChange);
}

// --- monthly series helpers ------------------------------------------------

function monthIndex(ym: string): number {
  const [year, month] = ym.split("-");
  const m = Number.parseInt(month, 10);
  if (!(m >= 1 && m <= 12)) throw new SeriesError(`bad month in '${ym}'`);
  return Number.parseInt(year, 10) * 12 + (m - 1);
}

function indexToMonth(idx: number): string {
  const y = Math.floor(idx / 12);
  const m = idx - y * 12 + 1;
  return `${String(y).padStart(4, "0")}-${String(m).padStart(2, "0")}`;
}

export function shiftMonth(ym: string, months: number): string {
  return indexToMonth(monthIndex(ym) + months);
}

export function lastMonth(series: Series): string {
  const keys = Object.keys(series);
  if (keys.length === 0) throw new SeriesError("empty series");
  return keys.reduce((a, b) => (monthIndex(b) > monthIndex(a) ? b : a));
}

export function windowReturn(series: Series, end: string, months: number): number {
  const start = shiftMonth(end, -months);
  if (!(start in series) || !(end in series)) throw new SeriesError(`series lacks ${start} or ${end}`);
  return totalReturn(series[start], series[end]);
}

/** Rate quoted for month m is earned during month m+1, compounded monthly at rate/12. */
export function depositIndex(monthlyAnnualRates: Series, base = 100.0): Series {
  const months = Object.keys(monthlyAnnualRates).sort((a, b) => monthIndex(a) - monthIndex(b));
  if (months.length === 0) throw new SeriesError("empty rate series");
  const first = monthIndex(months[0]);
  const last = monthIndex(months[months.length - 1]);
  if (months.length !== last - first + 1) throw new SeriesError("rate series has gaps");
  const index: Series = { [months[0]]: base };
  let level = base;
  for (let k = 1; k < months.length; k++) {
    level *= 1.0 + monthlyAnnualRates[months[k - 1]] / 12.0;
    index[months[k]] = level;
  }
  return index;
}

export function toTl(usdSeries: Series, usdtry: Series): Series {
  const out: Series = {};
  for (const m of Object.keys(usdSeries)) if (m in usdtry) out[m] = usdSeries[m] * usdtry[m];
  if (Object.keys(out).length === 0) throw new SeriesError("no overlapping months");
  return out;
}

// --- what the site shows ---------------------------------------------------

export interface WindowResult {
  years: number;
  nominal_tl: number;
  usd: number;
  real_tl: number;
  nominal_tl_annual: number;
  usd_annual: number;
  real_tl_annual: number;
}

export function assetWindows(
  assetTl: Series,
  cpi: Series,
  usdtry: Series,
  end: string,
  yearsList: number[] = [1, 3, 5, 10],
): WindowResult[] {
  const out: WindowResult[] = [];
  for (const years of yearsList) {
    const months = 12 * years;
    let n: number, i: number, fx: number;
    try {
      n = windowReturn(assetTl, end, months);
      i = windowReturn(cpi, end, months);
      fx = windowReturn(usdtry, end, months);
    } catch (err) {
      if (err instanceof SeriesError) continue;
      throw err;
    }
    const r = realReturn(n, i);
    const u = currencyReturn(n, fx);
    out.push({
      years,
      nominal_tl: n, usd: u, real_tl: r,
      nominal_tl_annual: annualize(n, years),
      usd_annual: annualize(u, years),
      real_tl_annual: annualize(r, years),
    });
  }
  return out;
}

/** What `amount` TL at an earlier level (CPI, USD/TRY, gold price...) is worth at today's level. */
export function valueToday(amount: number, levelThen: number, levelNow: number): number {
  if (levelThen <= 0) throw new SeriesError("cpi_then must be positive");
  return (amount * levelNow) / levelThen;
}

// --- personal inflation (Aşama 5) ------------------------------------------

/** Spending amounts per group -> shares that sum to 1. */
export function normalizeShares(amounts: Record<string, number>): Record<string, number> {
  const vals = Object.values(amounts);
  if (vals.some((v) => v < 0)) throw new SeriesError("spending amounts must be non-negative");
  const total = vals.reduce((a, b) => a + b, 0);
  if (!(total > 0)) throw new SeriesError("total spending must be positive");
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(amounts)) out[k] = v / total;
  return out;
}

/** Each group's contribution (share x group inflation). Zero-spending groups need no data. */
export function inflationContributions(amounts: Record<string, number>, groupChanges: Record<string, number>): Record<string, number> {
  const shares = normalizeShares(amounts);
  const out: Record<string, number> = {};
  for (const [k, s] of Object.entries(shares)) {
    if (s === 0) continue;
    if (!(k in groupChanges)) throw new SeriesError(`no price data for group '${k}'`);
    out[k] = s * groupChanges[k];
  }
  return out;
}

/** Spending-weighted average of group inflation rates: sum(s_k * pi_k). Personal estimate, not an official index. */
export function personalInflation(amounts: Record<string, number>, groupChanges: Record<string, number>): number {
  return Object.values(inflationContributions(amounts, groupChanges)).reduce((a, b) => a + b, 0);
}
