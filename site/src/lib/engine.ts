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

// --- portfolio (Portföyüm) -------------------------------------------------

export interface HoldingInput {
  amount: number; quantity: number | null; level_then: number; level_now: number;
  cpi_then: number; cpi_now: number; usd_then: number; usd_now: number; gold_then: number; gold_now: number;
}
export interface HoldingResult {
  amount: number; value: number; inflated_cost: number; nominal: number; real: number; usd: number; gold: number; inflation_gap_tl: number;
}

/** Same as reel/engine.py holding_returns. */
export function holdingReturns(p: HoldingInput): HoldingResult {
  if (!(p.amount > 0) || !(p.level_then > 0)) throw new SeriesError("amount and purchase level must be positive");
  const value = p.quantity !== null && p.quantity !== undefined ? p.quantity * p.level_now : valueToday(p.amount, p.level_then, p.level_now);
  const nominal = value / p.amount - 1.0;
  const inflated = valueToday(p.amount, p.cpi_then, p.cpi_now);
  return {
    amount: p.amount, value, inflated_cost: inflated, nominal,
    real: value / inflated - 1.0,
    usd: currencyReturn(nominal, p.usd_now / p.usd_then - 1.0),
    gold: currencyReturn(nominal, p.gold_now / p.gold_then - 1.0),
    inflation_gap_tl: value - inflated,
  };
}

export function portfolioSummary(holdings: { amount: number; value: number; inflated_cost: number }[]) {
  if (holdings.length === 0) throw new SeriesError("empty portfolio");
  const cost = holdings.reduce((a, h) => a + h.amount, 0);
  const value = holdings.reduce((a, h) => a + h.value, 0);
  const inflated = holdings.reduce((a, h) => a + h.inflated_cost, 0);
  return { cost, value, nominal: value / cost - 1.0, real: value / inflated - 1.0, inflation_gap_tl: value - inflated };
}

// --- IRR ---------------------------------------------------------------------

export function npv(rate: number, cashflows: number[]): number {
  return cashflows.reduce((a, cf, k) => a + cf / (1.0 + rate) ** k, 0);
}

/** Per-period rate that makes the NPV zero (bisection). Same as reel/engine.py irr. */
export function irr(cashflows: number[], lo = -0.99, hi = 10.0): number {
  if (npv(0.0, cashflows) === 0.0) return 0.0;
  let fLo = npv(lo, cashflows);
  const fHi = npv(hi, cashflows);
  if (fLo * fHi > 0) throw new SeriesError("no rate makes the cash flows balance");
  for (let i = 0; i < 300; i++) {
    const mid = (lo + hi) / 2.0;
    const fMid = npv(mid, cashflows);
    if (fMid === 0.0 || hi - lo < 1e-15) return mid;
    if (fLo * fMid < 0) hi = mid;
    else { lo = mid; fLo = fMid; }
  }
  return (lo + hi) / 2.0;
}

// --- loan true cost ------------------------------------------------------------

export interface AmortRow { month: number; installment: number; interest: number; kkdf: number; bsmv: number; principal: number; balance: number }

export function amortization(principal: number, monthlyRate: number, months: number, kkdf = 0.0, bsmv = 0.0): AmortRow[] {
  if (!(principal > 0) || !(months > 0)) throw new SeriesError("principal and term must be positive");
  const payment = mortgagePayment(principal, monthlyRate * (1.0 + kkdf + bsmv), months);
  let balance = principal;
  const rows: AmortRow[] = [];
  for (let t = 1; t <= months; t++) {
    const interest = balance * monthlyRate;
    const k = interest * kkdf, b = interest * bsmv;
    let princ = payment - interest - k - b;
    if (t === months) princ = balance;
    balance -= princ;
    rows.push({ month: t, installment: interest + k + b + princ, interest, kkdf: k, bsmv: b, principal: princ, balance: Math.max(balance, 0.0) });
  }
  return rows;
}

export interface LoanCostParams { principal: number; monthly_rate: number; months: number; kkdf: number; bsmv: number; upfront_fees: number; monthly_fees: number; inflation: number }

export function loanCost(p: LoanCostParams) {
  const rows = amortization(p.principal, p.monthly_rate, p.months, p.kkdf, p.bsmv);
  const payments = rows.map((r) => r.installment + p.monthly_fees);
  const m = irr([p.principal - p.upfront_fees, ...payments.map((x) => -x)]);
  const annual = (1.0 + m) ** 12 - 1.0;
  const sum = (f: (r: AmortRow) => number) => rows.reduce((a, r) => a + f(r), 0);
  return {
    schedule: rows,
    installment: rows[0].installment + p.monthly_fees,
    total_paid: payments.reduce((a, x) => a + x, 0) + p.upfront_fees,
    total_interest: sum((r) => r.interest),
    total_kkdf: sum((r) => r.kkdf),
    total_bsmv: sum((r) => r.bsmv),
    total_fees: p.upfront_fees + p.monthly_fees * p.months,
    advertised_annual: p.monthly_rate * 12,
    monthly_cost: m,
    annual_cost: annual,
    real_annual_cost: realReturn(annual, p.inflation),
  };
}

// --- installments vs cash ------------------------------------------------------

export function presentValue(payments: number[], monthlyRate: number, firstOffset = 1): number {
  return payments.reduce((a, x, k) => a + x / (1.0 + monthlyRate) ** (firstOffset + k), 0);
}

export interface InstallmentParams { cash_price: number; installment: number; count: number; first_offset: number; annual_discount: number; inflation: number }

export function installmentVsCash(p: InstallmentParams) {
  if (!(p.cash_price > 0) || !(p.installment > 0) || !(p.count > 0) || p.first_offset < 0) {
    throw new SeriesError("prices, installment and count must be positive");
  }
  const md = (1.0 + p.annual_discount) ** (1 / 12) - 1.0;
  const mi = (1.0 + p.inflation) ** (1 / 12) - 1.0;
  const payments = Array(p.count).fill(p.installment);
  const pv = presentValue(payments, md, p.first_offset);
  const flows = Array(p.first_offset + p.count).fill(0.0);
  flows[0] += p.cash_price;
  for (let k = 0; k < p.count; k++) flows[p.first_offset + k] -= p.installment;
  const hidden = irr(flows);
  const cheaper = Math.abs(pv - p.cash_price) < 1e-9 ? "equal" : pv < p.cash_price ? "installments" : "cash";
  return {
    nominal_total: p.installment * p.count,
    pv_installments: pv,
    real_total: presentValue(payments, mi, p.first_offset),
    saving: p.cash_price - pv,
    cheaper,
    hidden_monthly_rate: hidden,
    hidden_annual_rate: (1.0 + hidden) ** 12 - 1.0,
  };
}

// --- real salary -----------------------------------------------------------------

export function salaryAnalysis(points: Series, cpi: Series, end: string, usd: Series | null = null, gold: Series | null = null) {
  const months = Object.keys(points).sort((a, b) => monthIndex(a) - monthIndex(b));
  if (months.length === 0) throw new SeriesError("no salary points");
  for (const m of [...months, end]) if (!(m in cpi)) throw new SeriesError(`no CPI for ${m}`);
  const rows = months.map((m, k) => {
    const row: Record<string, any> = {
      month: m, salary: points[m], today_tl: valueToday(points[m], cpi[m], cpi[end]),
      usd: usd && m in usd ? points[m] / usd[m] : null,
      gold: gold && m in gold ? points[m] / gold[m] : null,
      raise_nominal: null, inflation: null, raise_real: null,
    };
    if (k) {
      const prev = months[k - 1];
      row.raise_nominal = totalReturn(points[prev], points[m]);
      row.inflation = totalReturn(cpi[prev], cpi[m]);
      row.raise_real = realReturn(row.raise_nominal, row.inflation);
    }
    return row;
  });
  return { rows, real_change_total: rows[rows.length - 1].today_tl / rows[0].today_tl - 1.0 };
}

// --- event study -----------------------------------------------------------------

function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  const n = s.length;
  return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2.0;
}

export function eventStudy(series: Series, kind: string, events: string[], before: number, after: number) {
  const offsets: number[] = [];
  for (let o = -before; o <= after; o++) offsets.push(o);
  const paths: number[][] = [], used: string[] = [], skipped: string[] = [];
  for (const ev of events) {
    const base = shiftMonth(ev, -1);
    const months = offsets.map((o) => shiftMonth(ev, o));
    if (!(base in series) || months.some((m) => !(m in series))) { skipped.push(ev); continue; }
    const b = series[base];
    if (kind === "level") {
      if (b <= 0) { skipped.push(ev); continue; }
      paths.push(months.map((m) => series[m] / b - 1.0));
    } else {
      paths.push(months.map((m) => series[m] - b));
    }
    used.push(ev);
  }
  const n = paths.length;
  const mean = n ? offsets.map((_, i) => paths.reduce((a, p) => a + p[i], 0) / n) : [];
  const med = n ? offsets.map((_, i) => median(paths.map((p) => p[i]))) : [];
  return { offsets, n, events: used, skipped, paths, mean, median: med };
}

// --- credit card minimum payment ----------------------------------------------

export function cardMinimumPayoff(p: { balance: number; monthly_rate: number; kkdf: number; bsmv: number; min_share: number; min_floor: number; max_months?: number }) {
  if (!(p.balance > 0) || !(p.min_share > 0 && p.min_share <= 1)) throw new SeriesError("balance must be positive and minimum share in (0, 1]");
  const maxMonths = p.max_months ?? 600;
  let bal = p.balance, paid = 0, interestTotal = 0, taxTotal = 0, months = 0;
  const balances = [p.balance];
  while (bal > 1e-9 && months < maxMonths) {
    months++;
    const interest = bal * p.monthly_rate;
    const tax = interest * (p.kkdf + p.bsmv);
    bal += interest + tax;
    const pay = Math.min(bal, Math.max(p.min_share * bal, p.min_floor));
    bal -= pay;
    paid += pay; interestTotal += interest; taxTotal += tax;
    balances.push(Math.max(bal, 0));
  }
  return { months, paid_off: bal <= 1e-9, total_paid: paid, total_interest: interestTotal, total_tax: taxTotal, remaining: Math.max(bal, 0), balances };
}

// --- loan restructuring -------------------------------------------------------

export interface RefiParams {
  balance: number; rate_old: number; months_old: number; rate_new: number; months_new: number;
  kkdf: number; bsmv: number; prepay_penalty: number; new_fees: number; fees_financed: boolean; annual_discount: number;
}
export function refinanceCompare(p: RefiParams) {
  if (!(p.balance > 0) || !(p.months_old > 0) || !(p.months_new > 0)) throw new SeriesError("balance and terms must be positive");
  const tax = 1.0 + p.kkdf + p.bsmv;
  const oldPayment = mortgagePayment(p.balance, p.rate_old * tax, p.months_old);
  const newPrincipal = p.balance * (1.0 + p.prepay_penalty) + (p.fees_financed ? p.new_fees : 0.0);
  const upfront = p.fees_financed ? 0.0 : p.new_fees;
  const newPayment = mortgagePayment(newPrincipal, p.rate_new * tax, p.months_new);
  const md = (1.0 + p.annual_discount) ** (1 / 12) - 1.0;
  const pvOld = presentValue(Array(p.months_old).fill(oldPayment), md, 1);
  const pvNew = upfront + presentValue(Array(p.months_new).fill(newPayment), md, 1);
  const saving = pvOld - pvNew;
  return {
    old_payment: oldPayment, new_payment: newPayment, new_principal: newPrincipal, upfront,
    total_old: oldPayment * p.months_old, total_new: upfront + newPayment * p.months_new,
    pv_old: pvOld, pv_new: pvNew, saving_pv: saving,
    better: Math.abs(saving) < 1e-9 ? "equal" : saving > 0 ? "new" : "old",
  };
}

// --- deposit net return, savings goal, half-life ----------------------------------

export function depositNet(p: { principal: number; gross_annual: number; days: number; withholding: number; inflation: number }) {
  if (!(p.principal > 0) || !(p.days > 0)) throw new SeriesError("principal and term must be positive");
  const grossTerm = (p.gross_annual * p.days) / 365.0;
  const netTerm = grossTerm * (1.0 - p.withholding);
  const netAnnual = (1.0 + netTerm) ** (365.0 / p.days) - 1.0;
  return {
    gross_interest_term: p.principal * grossTerm,
    tax_term: p.principal * grossTerm * p.withholding,
    net_interest_term: p.principal * netTerm,
    net_term_rate: netTerm,
    net_annual: netAnnual,
    real_annual: realReturn(netAnnual, p.inflation),
  };
}

export function requiredSaving(p: { target_today: number; years: number; inflation: number; nominal_return: number; current: number; grow_with_inflation: boolean }) {
  if (!(p.target_today > 0) || !(p.years > 0)) throw new SeriesError("target and years must be positive");
  const n = 12 * p.years;
  const mi = (1.0 + p.inflation) ** (1 / 12) - 1.0;
  const mr = (1.0 + p.nominal_return) ** (1 / 12) - 1.0;
  const targetNominal = p.target_today * (1.0 + p.inflation) ** p.years;
  const fvCurrent = p.current * (1.0 + mr) ** n;
  const g = (t: number) => (p.grow_with_inflation ? (1.0 + mi) ** (t - 1) : 1.0);
  let factor = 0;
  for (let t = 1; t <= n; t++) factor += g(t) * (1.0 + mr) ** (n - t);
  const monthly = Math.max(0.0, (targetNominal - fvCurrent) / factor);
  let contributions = 0;
  for (let t = 1; t <= n; t++) contributions += monthly * g(t);
  return { monthly, target_nominal: targetNominal, fv_current: fvCurrent, total_contributed: contributions + p.current };
}

export function halfLifeYears(annualInflation: number): number {
  if (!(annualInflation > 0)) throw new SeriesError("inflation must be positive");
  return Math.log(2.0) / Math.log(1.0 + annualInflation);
}

/** Gross annual deposit rate whose net, rolled-over return exactly matches inflation. */
export function breakevenGrossRate(p: { inflation: number; days: number; withholding: number }): number {
  if (!(p.days > 0) || !(p.withholding < 1)) throw new SeriesError("term must be positive and withholding below 100 %");
  const netTerm = (1.0 + p.inflation) ** (p.days / 365.0) - 1.0;
  return (netTerm / (1.0 - p.withholding)) * 365.0 / p.days;
}

// --- province household wealth (MODEL ESTIMATE) -------------------------------------

export interface WealthParams {
  population: number; deposits_tl: number; m2_price: number; household_size: number;
  ownership_rate: number; dwelling_m2: number; household_deposit_share: number;
}
/** Same model as reel/engine.py province_wealth. */
export function provinceWealth(p: WealthParams) {
  if (!(p.population > 0) || !(p.household_size > 0) || p.dwelling_m2 < 0 || p.m2_price < 0 || p.deposits_tl < 0) {
    throw new SeriesError("population and household size must be positive; amounts non-negative");
  }
  for (const s of [p.ownership_rate, p.household_deposit_share]) if (!(s >= 0 && s <= 1)) throw new SeriesError("shares must be between 0 and 1");
  const households = p.population / p.household_size;
  const housing = households * p.ownership_rate * p.dwelling_m2 * p.m2_price;
  const financial = p.deposits_tl * p.household_deposit_share;
  const total = housing + financial;
  return { households, housing, financial, total, per_household: total / households, per_capita: total / p.population };
}

// --- distributions (same algorithms as reel/engine.py) ------------------------------

export function normalCdf(x: number): number {
  if (x < -8) return 0.0;
  if (x > 8) return 1.0;
  let s = x, t = 0.0, b = x, i = 1.0;
  const q = x * x;
  while (s !== t) { t = s; i += 2.0; b *= q / i; s = t + b; }
  return 0.5 + s * Math.exp(-0.5 * q - 0.91893853320467274178);
}

export function normalPpf(p: number): number {
  if (!(p > 0 && p < 1)) throw new SeriesError("p must be in (0, 1)");
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
  const lo = 0.02425;
  let x: number;
  if (p < lo) {
    const q = Math.sqrt(-2 * Math.log(p));
    x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  } else if (p > 1 - lo) {
    const q = Math.sqrt(-2 * Math.log(1 - p));
    x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  } else {
    const q = p - 0.5, r = q * q;
    x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  for (let k = 0; k < 3; k++) {
    const pdf = Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
    if (pdf === 0) break;
    x -= (normalCdf(x) - p) / pdf;
  }
  return x;
}

export const giniFromSigma = (sigma: number) => 2.0 * normalCdf(sigma / Math.SQRT2) - 1.0;
export function sigmaFromGini(gini: number): number {
  if (!(gini > 0 && gini < 1)) throw new SeriesError("Gini must be in (0, 1)");
  return Math.SQRT2 * normalPpf((gini + 1.0) / 2.0);
}
export const topShareLognormal = (sigma: number, p: number) => 1.0 - normalCdf(normalPpf(1.0 - p) - sigma);

/** MODEL: wealth lognormal with dispersion = multiplier x income-implied dispersion. */
export function wealthInequality(p: { income_gini: number; multiplier: number }) {
  if (!(p.multiplier > 0)) throw new SeriesError("multiplier must be positive");
  const sInc = sigmaFromGini(p.income_gini);
  const sW = sInc * p.multiplier;
  return { sigma_income: sInc, sigma_wealth: sW, wealth_gini: giniFromSigma(sW), top10_share: topShareLognormal(sW, 0.1),
    top1_share: topShareLognormal(sW, 0.01), median_to_mean: Math.exp((-sW * sW) / 2.0) };
}

/** MODEL: split a national total across provinces by households x wealth^beta. */
export function goldAllocation(households: number[], wealthPerHousehold: number[], opts: { beta: number; total: number }): number[] {
  if (households.length !== wealthPerHousehold.length || households.length === 0) throw new SeriesError("need matching, non-empty lists");
  const w = households.map((h, k) => h * Math.max(wealthPerHousehold[k], 0) ** opts.beta);
  const s = w.reduce((a, x) => a + x, 0);
  if (!(s > 0)) throw new SeriesError("weights sum to zero");
  return w.map((x) => (opts.total * x) / s);
}

export function housingAffordability(p: { m2_price: number; rent_m2: number; monthly_wage: number; dwelling_m2: number }) {
  if (!(p.m2_price > 0) || !(p.rent_m2 > 0) || !(p.monthly_wage > 0) || !(p.dwelling_m2 > 0)) throw new SeriesError("inputs must be positive");
  const price = p.m2_price * p.dwelling_m2, rent = p.rent_m2 * p.dwelling_m2;
  return { price, rent, gross_yield: (12 * rent) / price, amortization_years: price / (12 * rent),
    price_to_annual_wage: price / (12 * p.monthly_wage), rent_to_wage: rent / p.monthly_wage };
}
