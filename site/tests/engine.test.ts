// Runs tests/cases.json (shared with the Python test suite) against src/lib/engine.ts.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as e from "../src/lib/engine.ts";

const casesPath = new URL("../../tests/cases.json", import.meta.url);
const { cases } = JSON.parse(readFileSync(casesPath, "utf8"));

const FN: Record<string, (...a: any[]) => unknown> = {
  total_return: e.totalReturn,
  annualize: e.annualize,
  real_return: e.realReturn,
  currency_return: e.currencyReturn,
  shift_month: e.shiftMonth,
  window_return: e.windowReturn,
  deposit_index: e.depositIndex,
  to_tl: e.toTl,
  asset_windows: e.assetWindows,
  value_today: e.valueToday,
  normalize_shares: e.normalizeShares,
  inflation_contributions: e.inflationContributions,
  personal_inflation: e.personalInflation,
  ratio_index: e.ratioIndex,
  mortgage_payment: e.mortgagePayment,
  rent_vs_buy: e.rentVsBuy,
  pearson: e.pearson,
  paired_changes: e.pairedChanges,
  rolling_correlation: e.rollingCorrelation,
  same_direction_share: e.sameDirectionShare,
  holding_returns: e.holdingReturns,
  portfolio_summary: e.portfolioSummary,
  irr: e.irr,
  loan_cost: e.loanCost,
  installment_vs_cash: e.installmentVsCash,
  salary_analysis: e.salaryAnalysis,
  event_study: e.eventStudy,
  card_minimum_payoff: e.cardMinimumPayoff,
  refinance_compare: e.refinanceCompare,
  deposit_net: e.depositNet,
  required_saving: e.requiredSaving,
  half_life_years: e.halfLifeYears,
  breakeven_gross_rate: e.breakevenGrossRate,
  province_wealth: e.provinceWealth,
  normal_cdf: e.normalCdf,
  normal_ppf: e.normalPpf,
  gini_from_sigma: e.giniFromSigma,
  top_share_lognormal: e.topShareLognormal,
  wealth_inequality: e.wealthInequality,
  gold_allocation: e.goldAllocation,
  net_worth_timeline: e.netWorthTimeline,
  progressive_tax: e.progressiveTax,
  payroll_year: e.payrollYear,
  gross_for_net: e.grossForNet,
  rental_income_tax: e.rentalIncomeTax,
  housing_affordability: e.housingAffordability,
  lorenz_lognormal: e.lorenzLognormal,
};

function expand(arg: any): any {
  if (arg && typeof arg === "object" && "$flat" in arg) {
    const [start, months, startValue, growth] = arg.$flat;
    const out: Record<string, number> = {};
    let v = startValue;
    for (let k = 0; k <= months; k++) {
      out[e.shiftMonth(start, k)] = v;
      v *= 1 + growth;
    }
    return out;
  }
  return arg;
}

function matches(actual: any, expected: any, tol: number, subset = false): boolean {
  if (expected === null || typeof expected === "string" || typeof expected === "boolean") return actual === expected;
  if (typeof expected === "number") return typeof actual === "number" && Math.abs(actual - expected) <= tol;
  if (Array.isArray(expected)) {
    return Array.isArray(actual) && actual.length === expected.length && expected.every((x, k) => matches(actual[k], x, tol));
  }
  if (typeof expected === "object") {
    if (actual === null || typeof actual !== "object") return false;
    if (!subset && !("years" in expected)) {
      const a = Object.keys(actual).sort().join();
      const b = Object.keys(expected).sort().join();
      if (a !== b) return false;
    }
    return Object.entries(expected).every(([k, v]) => k in actual && matches(actual[k], v, tol));
  }
  throw new TypeError(String(expected));
}

for (const c of cases) {
  test(c.name, () => {
    const fn = FN[c.fn];
    assert.ok(fn, `no TS function mapped for ${c.fn}`);
    const args = c.args.map(expand);
    if (c.raises) {
      assert.throws(() => fn(...args), e.SeriesError);
    } else {
      const got = fn(...args);
      assert.ok(matches(got, c.expect, c.tol, c.subset ?? false), `${c.fn}: got ${JSON.stringify(got)}, expected ${JSON.stringify(c.expect)}`);
    }
  });
}

test("every case in cases.json was mapped", () => {
  for (const c of cases) assert.ok(c.fn in FN, c.fn);
});
