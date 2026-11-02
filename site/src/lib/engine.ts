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

// --- "X priced in Y" ratio charts ------------------------------------------

/** X's price in units of Y (both TL levels), rebased to 100 at `start`. */
export function ratioIndex(xTl: Series, yTl: Series, start: string, end: string): { months: string[]; values: number[] } {
  const months: string[] = [];
  for (let m = start; monthIndex(m) <= monthIndex(end); m = shiftMonth(m, 1)) months.push(m);
  for (const m of months) {
    if (!(m in xTl) || !(m in yTl) || yTl[m] <= 0) throw new SeriesError(`missing data for ${m}`);
  }
  const base = xTl[start] / yTl[start];
  if (!(base > 0)) throw new SeriesError("start ratio must be positive");
  return { months, values: months.map((m) => (100.0 * (xTl[m] / yTl[m])) / base) };
}

// --- rent vs buy -----------------------------------------------------------

export function mortgagePayment(principal: number, monthlyRate: number, months: number): number {
  if (months <= 0) throw new SeriesError("loan term must be positive");
  if (monthlyRate === 0) return principal / months;
  return (principal * monthlyRate) / (1.0 - (1.0 + monthlyRate) ** -months);
}

export interface RentVsBuyParams {
  price: number; rent: number; down_share: number; loan_rate_monthly: number; loan_months: number;
  house_growth: number; rent_growth: number; invest_return: number; inflation: number;
  buy_cost: number; sell_cost: number; upkeep: number; years: number;
}
export interface RentVsBuyYear { year: number; buy_wealth: number; rent_wealth: number; house_value: number; loan_balance: number; rent: number }
export interface RentVsBuyResult {
  monthly_payment: number; buy_wealth: number; rent_wealth: number;
  buy_wealth_real: number; rent_wealth_real: number; breakeven_year: number | null; yearly: RentVsBuyYear[];
}

/** Same model as reel/engine.py rent_vs_buy (see its docstring). */
export function rentVsBuy(p: RentVsBuyParams): RentVsBuyResult {
  if (!(p.down_share >= 0 && p.down_share <= 1)) throw new SeriesError("down payment share must be between 0 and 1");
  if (!(p.price > 0) || !(p.years > 0)) throw new SeriesError("price and years must be positive");
  const loan = p.price * (1.0 - p.down_share);
  const payment = loan > 0 ? mortgagePayment(loan, p.loan_rate_monthly, p.loan_months) : 0.0;
  const gh = (1.0 + p.house_growth) ** (1 / 12) - 1.0;
  const gi = (1.0 + p.invest_return) ** (1 / 12) - 1.0;
  let house = p.price;
  let balance = loan;
  let portfolio = p.price * p.down_share + p.price * p.buy_cost;
  const yearly: RentVsBuyYear[] = [];
  for (let t = 1; t <= 12 * p.years; t++) {
    const rentT = p.rent * (1.0 + p.rent_growth) ** Math.floor((t - 1) / 12);
    let pay = 0.0;
    if (balance > 0 && t <= p.loan_months) {
      const interest = balance * p.loan_rate_monthly;
      pay = Math.min(payment, balance + interest);
      balance = Math.max(0.0, balance + interest - pay);
    }
    const buyerOut = pay + (p.upkeep * house) / 12.0;
    portfolio = portfolio * (1.0 + gi) + (buyerOut - rentT);
    house *= 1.0 + gh;
    if (t % 12 === 0) {
      yearly.push({ year: t / 12, buy_wealth: house * (1.0 - p.sell_cost) - balance, rent_wealth: portfolio, house_value: house, loan_balance: balance, rent: rentT });
    }
  }
  let breakeven: number | null = null;
  for (let k = yearly.length - 1; k >= 0; k--) {
    if (yearly[k].buy_wealth < yearly[k].rent_wealth) break;
    breakeven = yearly[k].year;
  }
  const deflator = (1.0 + p.inflation) ** p.years;
  const last = yearly[yearly.length - 1];
  return {
    monthly_payment: payment,
    buy_wealth: last.buy_wealth,
    rent_wealth: last.rent_wealth,
    buy_wealth_real: last.buy_wealth / deflator,
    rent_wealth_real: last.rent_wealth / deflator,
    breakeven_year: breakeven,
    yearly,
  };
}

// --- co-movement (İlişkiler) -----------------------------------------------

export function pearson(xs: number[], ys: number[]): number {
  const n = xs.length;
  if (n !== ys.length || n < 3) throw new SeriesError("need at least 3 paired observations");
  const mx = xs.reduce((a, b) => a + b, 0) / n;
  const my = ys.reduce((a, b) => a + b, 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let k = 0; k < n; k++) {
    sxy += (xs[k] - mx) * (ys[k] - my);
    sxx += (xs[k] - mx) ** 2;
    syy += (ys[k] - my) ** 2;
  }
  if (sxx === 0 || syy === 0) throw new SeriesError("a series does not vary");
  return sxy / Math.sqrt(sxx * syy);
}

function change(series: Series, m: string, step: number, kind: string): number {
  const prev = series[shiftMonth(m, -step)];
  if (kind === "rate") return series[m] - prev;
  if (prev <= 0) throw new SeriesError("level must be positive");
  return series[m] / prev - 1.0;
}

export function pairedChanges(a: Series, b: Series, kindA: string, kindB: string, step: number) {
  const months: string[] = [], da: number[] = [], db: number[] = [];
  const common = Object.keys(a).filter((m) => m in b).sort((x, y) => monthIndex(x) - monthIndex(y));
  for (const m of common) {
    const s = shiftMonth(m, -step);
    if (s in a && s in b) {
      months.push(m);
      da.push(change(a, m, step, kindA));
      db.push(change(b, m, step, kindB));
    }
  }
  return { months, a: da, b: db };
}

export function rollingCorrelation(pairs: { months: string[]; a: number[]; b: number[] }, window: number): Record<string, number> {
  const out: Record<string, number> = {};
  for (let k = window - 1; k < pairs.months.length; k++) {
    try {
      out[pairs.months[k]] = pearson(pairs.a.slice(k - window + 1, k + 1), pairs.b.slice(k - window + 1, k + 1));
    } catch (e) {
      if (!(e instanceof SeriesError)) throw e;
    }
  }
  return out;
}

/** Share of periods in which both series changed in the same direction. */
export function sameDirectionShare(pairs: { months: string[]; a: number[]; b: number[] }): number {
  const n = pairs.months.length;
  if (n === 0) throw new SeriesError("no paired observations");
  let same = 0;
  for (let k = 0; k < n; k++) if (pairs.a[k] * pairs.b[k] > 0) same++;
  return same / n;
}
