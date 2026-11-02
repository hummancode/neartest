"""Real-return engine.

Pure, deterministic functions. No I/O, no network. Everything the site shows
is computed here and covered by tests in tests/test_engine.py.

Conventions
-----------
- Returns are decimal fractions: 0.25 means +25 %.
- A monthly series is a dict {"YYYY-MM": value}. Months must be contiguous
  for windowed calculations; gaps raise instead of being silently skipped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class SeriesError(ValueError):
    """Raised when a series cannot support the requested calculation."""


# ---------------------------------------------------------------------------
# Scalar building blocks
# ---------------------------------------------------------------------------

def total_return(start_value: float, end_value: float) -> float:
    """Cumulative return between two levels."""
    if start_value <= 0:
        raise SeriesError(f"start value must be positive, got {start_value}")
    return end_value / start_value - 1.0


def annualize(total: float, years: float) -> float:
    """Geometric annualisation of a cumulative return."""
    if years <= 0:
        raise SeriesError(f"years must be positive, got {years}")
    if total <= -1.0:
        return -1.0
    return (1.0 + total) ** (1.0 / years) - 1.0


def real_return(nominal: float, inflation: float) -> float:
    """Fisher relation: (1 + n) / (1 + i) - 1. Exact, not the n - i approximation."""
    if inflation <= -1.0:
        raise SeriesError(f"inflation must be > -100 %, got {inflation}")
    return (1.0 + nominal) / (1.0 + inflation) - 1.0


def currency_return(local_return: float, fx_change: float) -> float:
    """Return measured in a foreign currency.

    local_return: return in TL. fx_change: change of the TL price of one unit
    of foreign currency (USD/TRY going 30 -> 33 is +0.10).
    """
    return real_return(local_return, fx_change)


# ---------------------------------------------------------------------------
# Monthly series helpers
# ---------------------------------------------------------------------------

def _month_index(ym: str) -> int:
    year, month = ym.split("-")
    m = int(month)
    if not 1 <= m <= 12:
        raise SeriesError(f"bad month in {ym!r}")
    return int(year) * 12 + (m - 1)


def _index_to_month(idx: int) -> str:
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def shift_month(ym: str, months: int) -> str:
    """'2024-03' shifted by -12 -> '2023-03'."""
    return _index_to_month(_month_index(ym) + months)


def last_month(series: dict[str, float]) -> str:
    if not series:
        raise SeriesError("empty series")
    return max(series, key=_month_index)


def window_return(series: dict[str, float], end: str, months: int) -> float:
    """Cumulative return over the `months` months ending at `end`."""
    start = shift_month(end, -months)
    if start not in series or end not in series:
        raise SeriesError(f"series lacks {start} or {end}")
    return total_return(series[start], series[end])


def deposit_index(monthly_annual_rates: dict[str, float], base: float = 100.0) -> dict[str, float]:
    """Turn a series of annual deposit rates into a wealth index.

    The rate quoted for month m (e.g. 0.48 = 48 % per year) is assumed to be
    earned during month m+1, compounded monthly at rate/12. Withholding tax is
    ignored here; the methodology page states this.
    """
    if not monthly_annual_rates:
        raise SeriesError("empty rate series")
    months = sorted(monthly_annual_rates, key=_month_index)
    first, last = _month_index(months[0]), _month_index(months[-1])
    if len(months) != last - first + 1:
        raise SeriesError("rate series has gaps")
    index = {months[0]: base}
    level = base
    for prev, cur in zip(months, months[1:]):
        level *= 1.0 + monthly_annual_rates[prev] / 12.0
        index[cur] = level
    return index


def to_tl(usd_series: dict[str, float], usdtry: dict[str, float]) -> dict[str, float]:
    """Convert a USD-priced series to TL using the same month's USD/TRY."""
    common = set(usd_series) & set(usdtry)
    if not common:
        raise SeriesError("no overlapping months")
    return {m: usd_series[m] * usdtry[m] for m in common}


# ---------------------------------------------------------------------------
# What the site shows
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WindowResult:
    years: int
    nominal_tl: float        # cumulative, TL
    usd: float               # cumulative, measured in USD
    real_tl: float           # cumulative, deflated by Turkish CPI
    nominal_tl_annual: float
    usd_annual: float
    real_tl_annual: float


def asset_windows(
    asset_tl: dict[str, float],
    cpi: dict[str, float],
    usdtry: dict[str, float],
    end: str,
    years_list: tuple[int, ...] = (1, 3, 5, 10),
) -> list[WindowResult]:
    """Nominal TL, USD-based and real TL returns for each window.

    Windows the data cannot cover are skipped, never extrapolated.
    """
    out = []
    for years in years_list:
        months = 12 * years
        try:
            n = window_return(asset_tl, end, months)
            i = window_return(cpi, end, months)
            fx = window_return(usdtry, end, months)
        except SeriesError:
            continue
        r = real_return(n, i)
        u = currency_return(n, fx)
        out.append(WindowResult(
            years=years,
            nominal_tl=n, usd=u, real_tl=r,
            nominal_tl_annual=annualize(n, years),
            usd_annual=annualize(u, years),
            real_tl_annual=annualize(r, years),
        ))
    return out


def value_today(amount: float, cpi_then: float, cpi_now: float) -> float:
    """What `amount` TL at an earlier CPI level is worth in today's TL."""
    if cpi_then <= 0:
        raise SeriesError("cpi_then must be positive")
    return amount * cpi_now / cpi_then


# ---------------------------------------------------------------------------
# Personal inflation (Aşama 5)
# ---------------------------------------------------------------------------

def normalize_shares(amounts: dict[str, float]) -> dict[str, float]:
    """Spending amounts per group -> shares that sum to 1."""
    if any(v < 0 for v in amounts.values()):
        raise SeriesError("spending amounts must be non-negative")
    total = sum(amounts.values())
    if total <= 0:
        raise SeriesError("total spending must be positive")
    return {k: v / total for k, v in amounts.items()}


def inflation_contributions(amounts: dict[str, float], group_changes: dict[str, float]) -> dict[str, float]:
    """Each group's contribution (share x group inflation) to personal inflation.

    Groups with zero spending contribute nothing and need no price data.
    """
    shares = normalize_shares(amounts)
    out = {}
    for k, s in shares.items():
        if s == 0:
            continue
        if k not in group_changes:
            raise SeriesError(f"no price data for group {k!r}")
        out[k] = s * group_changes[k]
    return out


def personal_inflation(amounts: dict[str, float], group_changes: dict[str, float]) -> float:
    """Spending-weighted average of group inflation rates: sum(s_k * pi_k).

    This is a personal estimate with the user's own weights, not an official index.
    """
    return sum(inflation_contributions(amounts, group_changes).values())


# ---------------------------------------------------------------------------
# Real interest rates (Aşama 6)
# ---------------------------------------------------------------------------
# Rates are quoted annual rates (0.50 = 50 % per year), used as quoted:
# no compounding adjustment. Compounded deposit returns are in the Reel Tablo.

def trailing_real_rates(rates: dict[str, float], cpi: dict[str, float]) -> dict[str, float]:
    """Rate quoted in month m vs. CPI inflation over the 12 months ending in m.

    "Today's rate against the latest annual inflation" - backward-looking.
    """
    out = {}
    for m in sorted(rates, key=_month_index):
        try:
            inflation = window_return(cpi, m, 12)
        except SeriesError:
            continue
        out[m] = real_return(rates[m], inflation)
    return out


def ex_post_real_rates(rates: dict[str, float], cpi: dict[str, float]) -> dict[str, float]:
    """Rate quoted in month m-12 vs. the CPI inflation that followed (m-12 -> m).

    Keyed by m, the month the 12-month period ends. This is the realised (ex-post)
    real rate for someone who locked in the rate a year earlier.
    """
    out = {}
    for m in sorted(cpi, key=_month_index):
        start = shift_month(m, -12)
        if start not in rates:
            continue
        try:
            inflation = window_return(cpi, m, 12)
        except SeriesError:
            continue
        out[m] = real_return(rates[start], inflation)
    return out


# ---------------------------------------------------------------------------
# Index paths for charts
# ---------------------------------------------------------------------------

def index_paths(
    asset_tl: dict[str, float],
    cpi: dict[str, float],
    usdtry: dict[str, float],
    end: str,
    years: int,
) -> dict[str, list]:
    """What 100 TL put into the asset `years` before `end` was worth each month.

    nominal: in TL; real: in start-month TL (deflated by CPI); usd: in USD terms,
    rebased to 100. The last values equal 100 * (1 + window return) from asset_windows.
    """
    months = [shift_month(end, -k) for k in range(12 * years, -1, -1)]
    for m in months:
        if m not in asset_tl or m not in cpi or m not in usdtry:
            raise SeriesError(f"missing data for {m}")
    a0, c0, f0 = asset_tl[months[0]], cpi[months[0]], usdtry[months[0]]
    if min(a0, c0, f0) <= 0:
        raise SeriesError("start values must be positive")
    return {
        "months": months,
        "nominal": [100.0 * asset_tl[m] / a0 for m in months],
        "real": [100.0 * (asset_tl[m] / cpi[m]) / (a0 / c0) for m in months],
        "usd": [100.0 * (asset_tl[m] / usdtry[m]) / (a0 / f0) for m in months],
    }


# ---------------------------------------------------------------------------
# "X priced in Y" ratio charts
# ---------------------------------------------------------------------------

def ratio_index(x_tl: dict[str, float], y_tl: dict[str, float], start: str, end: str) -> dict[str, list]:
    """X's price measured in units of Y, rebased to 100 at `start`.

    Both inputs are TL price levels (or indices); X in Y terms is X/Y. Every month
    from start to end must exist in both series.
    """
    months, m = [], start
    while _month_index(m) <= _month_index(end):
        months.append(m)
        m = shift_month(m, 1)
    for m in months:
        if m not in x_tl or m not in y_tl or y_tl[m] <= 0:
            raise SeriesError(f"missing data for {m}")
    base = x_tl[start] / y_tl[start]
    if base <= 0:
        raise SeriesError("start ratio must be positive")
    return {"months": months, "values": [100.0 * (x_tl[m] / y_tl[m]) / base for m in months]}


# ---------------------------------------------------------------------------
# Rent vs buy
# ---------------------------------------------------------------------------

def mortgage_payment(principal: float, monthly_rate: float, months: int) -> float:
    """Level (annuity) monthly payment."""
    if months <= 0:
        raise SeriesError("loan term must be positive")
    if monthly_rate == 0:
        return principal / months
    return principal * monthly_rate / (1.0 - (1.0 + monthly_rate) ** -months)


def rent_vs_buy(
    *,
    price: float,               # house price today (TL)
    rent: float,                # monthly rent for a comparable house today (TL)
    down_share: float,          # down payment as share of price (1.0 = cash)
    loan_rate_monthly: float,   # mortgage rate per month (Turkish loans are quoted monthly)
    loan_months: int,
    house_growth: float,        # expected house price change per year
    rent_growth: float,         # rent increase, applied once a year (contract renewal)
    invest_return: float,       # yearly return on the renter's invested savings
    inflation: float,           # yearly CPI, only to express results in today's TL
    buy_cost: float,            # purchase costs (title deed fee etc.) as share of price
    sell_cost: float,           # selling costs as share of the future price
    upkeep: float,              # yearly upkeep/tax/insurance as share of current price
    years: int,
) -> dict:
    """Compare net wealth after `years` of buying vs renting and investing the difference.

    Buyer: pays down payment + purchase costs today, then mortgage and upkeep monthly.
    Renter: invests what the buyer paid up front, then each month invests (buyer's
    outflow - rent), or withdraws when rent is higher. Buyer wealth = house value
    after selling costs - remaining loan. Monthly steps; growth rates compound monthly,
    rent steps up every 12 months.
    """
    if not 0 <= down_share <= 1:
        raise SeriesError("down payment share must be between 0 and 1")
    if price <= 0 or years <= 0:
        raise SeriesError("price and years must be positive")
    loan = price * (1.0 - down_share)
    payment = mortgage_payment(loan, loan_rate_monthly, loan_months) if loan > 0 else 0.0
    gh = (1.0 + house_growth) ** (1 / 12) - 1.0
    gi = (1.0 + invest_return) ** (1 / 12) - 1.0

    house, balance = price, loan
    portfolio = price * down_share + price * buy_cost
    yearly = []
    for t in range(1, 12 * years + 1):
        rent_t = rent * (1.0 + rent_growth) ** ((t - 1) // 12)
        pay = 0.0
        if balance > 0 and t <= loan_months:
            interest = balance * loan_rate_monthly
            pay = min(payment, balance + interest)
            balance = max(0.0, balance + interest - pay)
        buyer_out = pay + upkeep * house / 12.0
        portfolio = portfolio * (1.0 + gi) + (buyer_out - rent_t)
        house *= 1.0 + gh
        if t % 12 == 0:
            year = t // 12
            buy_w = house * (1.0 - sell_cost) - balance
            yearly.append({"year": year, "buy_wealth": buy_w, "rent_wealth": portfolio,
                           "house_value": house, "loan_balance": balance, "rent": rent_t})
    # First year from which buying stays ahead until the horizon (None if it never does).
    breakeven = None
    for row in reversed(yearly):
        if row["buy_wealth"] < row["rent_wealth"]:
            break
        breakeven = row["year"]
    deflator = (1.0 + inflation) ** years
    last = yearly[-1]
    return {
        "monthly_payment": payment,
        "buy_wealth": last["buy_wealth"],
        "rent_wealth": last["rent_wealth"],
        "buy_wealth_real": last["buy_wealth"] / deflator,
        "rent_wealth_real": last["rent_wealth"] / deflator,
        "breakeven_year": breakeven,
        "yearly": yearly,
    }


# ---------------------------------------------------------------------------
# Price basket index (e.g. new-car list prices from official dealers)
# ---------------------------------------------------------------------------

def jevons_chain_index(prices: dict[str, dict[str, float]], base: float = 100.0) -> dict[str, float]:
    """Chained Jevons index: each month moves by the geometric mean of price relatives
    of the items priced in both that month and the previous one.

    Items entering or leaving the basket only affect months where they have two
    consecutive prices. Months must be contiguous. This tracks list prices of a
    chosen basket; it is not a quality-adjusted index and not an official statistic.
    """
    months = sorted(prices, key=_month_index)
    if not months:
        raise SeriesError("empty basket")
    if len(months) != _month_index(months[-1]) - _month_index(months[0]) + 1:
        raise SeriesError("basket has month gaps")
    out = {months[0]: base}
    level = base
    for prev, cur in zip(months, months[1:]):
        common = [k for k in prices[cur] if k in prices[prev] and prices[prev][k] > 0 and prices[cur][k] > 0]
        if not common:
            raise SeriesError(f"no item priced in both {prev} and {cur}")
        log_mean = sum(math.log(prices[cur][k] / prices[prev][k]) for k in common) / len(common)
        level *= math.exp(log_mean)
        out[cur] = level
    return out


# ---------------------------------------------------------------------------
# Co-movement between two indicators
# ---------------------------------------------------------------------------
# Correlation describes how two series moved together; it does not show cause.

def pearson(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation coefficient."""
    n = len(xs)
    if n != len(ys) or n < 3:
        raise SeriesError("need at least 3 paired observations")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        raise SeriesError("a series does not vary")
    return sxy / math.sqrt(sxx * syy)


def _change(series: dict[str, float], m: str, step: int, kind: str) -> float:
    prev = series[shift_month(m, -step)]
    if kind == "rate":                      # %, bps: change in points
        return series[m] - prev
    if prev <= 0:
        raise SeriesError("level must be positive")
    return series[m] / prev - 1.0           # prices, indices: % change


def paired_changes(a: dict[str, float], b: dict[str, float], kind_a: str, kind_b: str, step: int) -> dict[str, list]:
    """Changes of a and b over `step` months, at months where both have both ends."""
    months, da, db = [], [], []
    for m in sorted(set(a) & set(b), key=_month_index):
        s = shift_month(m, -step)
        if s in a and s in b:
            months.append(m)
            da.append(_change(a, m, step, kind_a))
            db.append(_change(b, m, step, kind_b))
    return {"months": months, "a": da, "b": db}


def rolling_correlation(pairs: dict[str, list], window: int) -> dict[str, float]:
    """Correlation over the last `window` paired changes, ending at each month."""
    out = {}
    for k in range(window - 1, len(pairs["months"])):
        xs, ys = pairs["a"][k - window + 1:k + 1], pairs["b"][k - window + 1:k + 1]
        try:
            out[pairs["months"][k]] = pearson(xs, ys)
        except SeriesError:
            continue
    return out


def same_direction_share(pairs: dict[str, list]) -> float:
    """Share of periods in which both series changed in the same direction."""
    n = len(pairs["months"])
    if n == 0:
        raise SeriesError("no paired observations")
    same = sum(1 for x, y in zip(pairs["a"], pairs["b"]) if x * y > 0)
    return same / n


# ---------------------------------------------------------------------------
# Portfolio (computed in the browser with the TS port; nothing is uploaded)
# ---------------------------------------------------------------------------

def holding_returns(*, amount: float, quantity: float | None, level_then: float, level_now: float,
                    cpi_then: float, cpi_now: float, usd_then: float, usd_now: float,
                    gold_then: float, gold_now: float) -> dict:
    """One purchase: TL `amount` spent in a month when the instrument's TL level was `level_then`.

    If `quantity` (shares, grams, dollars...) is given, value = quantity x today's level;
    otherwise the amount is assumed to have bought amount/level_then units.
    """
    if amount <= 0 or level_then <= 0:
        raise SeriesError("amount and purchase level must be positive")
    value = quantity * level_now if quantity is not None else value_today(amount, level_then, level_now)
    nominal = value / amount - 1.0
    inflated_cost = value_today(amount, cpi_then, cpi_now)
    return {
        "amount": amount,
        "value": value,
        "inflated_cost": inflated_cost,
        "nominal": nominal,
        "real": value / inflated_cost - 1.0,
        "usd": currency_return(nominal, usd_now / usd_then - 1.0),
        "gold": currency_return(nominal, gold_now / gold_then - 1.0),
        "inflation_gap_tl": value - inflated_cost,
    }


def portfolio_summary(holdings: list[dict]) -> dict:
    """Money-weighted totals: value vs. cost, and vs. cost carried forward with CPI."""
    if not holdings:
        raise SeriesError("empty portfolio")
    cost = sum(h["amount"] for h in holdings)
    value = sum(h["value"] for h in holdings)
    inflated = sum(h["inflated_cost"] for h in holdings)
    return {"cost": cost, "value": value, "nominal": value / cost - 1.0,
            "real": value / inflated - 1.0, "inflation_gap_tl": value - inflated}


# ---------------------------------------------------------------------------
# Internal rate of return
# ---------------------------------------------------------------------------

def npv(rate: float, cashflows: list[float]) -> float:
    return sum(cf / (1.0 + rate) ** k for k, cf in enumerate(cashflows))


def irr(cashflows: list[float], lo: float = -0.99, hi: float = 10.0) -> float:
    """Per-period rate that makes the NPV of `cashflows` zero (bisection).

    cashflows[k] happens at period k. Needs a sign change in the NPV over [lo, hi].
    """
    if npv(0.0, cashflows) == 0.0:
        return 0.0
    f_lo, f_hi = npv(lo, cashflows), npv(hi, cashflows)
    if f_lo * f_hi > 0:
        raise SeriesError("no rate makes the cash flows balance")
    for _ in range(300):
        mid = (lo + hi) / 2.0
        f_mid = npv(mid, cashflows)
        if f_mid == 0.0 or hi - lo < 1e-15:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# Consumer loan true cost (Turkish loans: KKDF and BSMV are charged on interest)
# ---------------------------------------------------------------------------

def amortization(principal: float, monthly_rate: float, months: int, kkdf: float = 0.0, bsmv: float = 0.0) -> list[dict]:
    """Equal-installment plan where taxes are added to each month's interest.

    Installment = annuity at the tax-inclusive rate r x (1 + KKDF + BSMV).
    """
    if principal <= 0 or months <= 0:
        raise SeriesError("principal and term must be positive")
    r_eff = monthly_rate * (1.0 + kkdf + bsmv)
    payment = mortgage_payment(principal, r_eff, months)
    balance, rows = principal, []
    for t in range(1, months + 1):
        interest = balance * monthly_rate
        k, b = interest * kkdf, interest * bsmv
        princ = payment - interest - k - b
        if t == months:
            princ = balance                      # absorb float drift in the last month
        balance -= princ
        rows.append({"month": t, "installment": interest + k + b + princ, "interest": interest,
                     "kkdf": k, "bsmv": b, "principal": princ, "balance": max(balance, 0.0)})
    return rows


def loan_cost(*, principal: float, monthly_rate: float, months: int, kkdf: float, bsmv: float,
              upfront_fees: float, monthly_fees: float, inflation: float) -> dict:
    """What the loan really costs: the IRR of money received vs. every payment.

    upfront_fees: allocation fee, upfront insurance... deducted from what you receive.
    monthly_fees: e.g. monthly insurance or account fees added to each installment.
    annual_cost compounds the monthly IRR; advertised_annual is the bank's rate x 12.
    """
    rows = amortization(principal, monthly_rate, months, kkdf, bsmv)
    payments = [r["installment"] + monthly_fees for r in rows]
    m = irr([principal - upfront_fees] + [-p for p in payments])
    annual = (1.0 + m) ** 12 - 1.0
    return {
        "schedule": rows,
        "installment": rows[0]["installment"] + monthly_fees,
        "total_paid": sum(payments) + upfront_fees,
        "total_interest": sum(r["interest"] for r in rows),
        "total_kkdf": sum(r["kkdf"] for r in rows),
        "total_bsmv": sum(r["bsmv"] for r in rows),
        "total_fees": upfront_fees + monthly_fees * months,
        "advertised_annual": monthly_rate * 12,
        "monthly_cost": m,
        "annual_cost": annual,
        "real_annual_cost": real_return(annual, inflation),
    }


# ---------------------------------------------------------------------------
# Installments vs cash
# ---------------------------------------------------------------------------

def present_value(payments: list[float], monthly_rate: float, first_offset: int = 1) -> float:
    return sum(p / (1.0 + monthly_rate) ** (first_offset + k) for k, p in enumerate(payments))


def installment_vs_cash(*, cash_price: float, installment: float, count: int, first_offset: int,
                        annual_discount: float, inflation: float) -> dict:
    """Compare paying `cash_price` now with `count` installments starting in `first_offset` months.

    annual_discount: what your money earns elsewhere (e.g. deposit rate after tax).
    hidden_monthly_rate: the interest rate the installment plan implies vs. the cash price.
    """
    if cash_price <= 0 or installment <= 0 or count <= 0 or first_offset < 0:
        raise SeriesError("prices, installment and count must be positive")
    md = (1.0 + annual_discount) ** (1 / 12) - 1.0
    mi = (1.0 + inflation) ** (1 / 12) - 1.0
    payments = [installment] * count
    pv = present_value(payments, md, first_offset)
    flows = [0.0] * (first_offset + count)
    flows[0] += cash_price
    for k in range(count):
        flows[first_offset + k] -= installment
    hidden = irr(flows)
    if abs(pv - cash_price) < 1e-9:
        cheaper = "equal"
    else:
        cheaper = "installments" if pv < cash_price else "cash"
    return {
        "nominal_total": installment * count,
        "pv_installments": pv,
        "real_total": present_value(payments, mi, first_offset),
        "saving": cash_price - pv,
        "cheaper": cheaper,
        "hidden_monthly_rate": hidden,
        "hidden_annual_rate": (1.0 + hidden) ** 12 - 1.0,
    }


# ---------------------------------------------------------------------------
# Real salary
# ---------------------------------------------------------------------------

def salary_analysis(points: dict[str, float], cpi: dict[str, float], end: str,
                    usd: dict[str, float] | None = None, gold: dict[str, float] | None = None) -> dict:
    """Each salary point in today's TL, USD and grams of gold; every raise vs. inflation."""
    months = sorted(points, key=_month_index)
    if not months:
        raise SeriesError("no salary points")
    for m in months + [end]:
        if m not in cpi:
            raise SeriesError(f"no CPI for {m}")
    rows = []
    for k, m in enumerate(months):
        row = {"month": m, "salary": points[m], "today_tl": value_today(points[m], cpi[m], cpi[end]),
               "usd": points[m] / usd[m] if usd and m in usd else None,
               "gold": points[m] / gold[m] if gold and m in gold else None,
               "raise_nominal": None, "inflation": None, "raise_real": None}
        if k:
            prev = months[k - 1]
            row["raise_nominal"] = total_return(points[prev], points[m])
            row["inflation"] = total_return(cpi[prev], cpi[m])
            row["raise_real"] = real_return(row["raise_nominal"], row["inflation"])
        rows.append(row)
    return {"rows": rows, "real_change_total": rows[-1]["today_tl"] / rows[0]["today_tl"] - 1.0}


# ---------------------------------------------------------------------------
# Event study
# ---------------------------------------------------------------------------

def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def event_study(series: dict[str, float], kind: str, events: list[str], before: int, after: int) -> dict:
    """Average path of `series` around event months, relative to the month before each event.

    level -> cumulative % change from that base month; rate -> change in points.
    Events without data for the whole window are left out (and counted).
    """
    offsets = list(range(-before, after + 1))
    paths, used, skipped = [], [], []
    for ev in events:
        base = shift_month(ev, -1)
        months = [shift_month(ev, o) for o in offsets]
        if base not in series or any(m not in series for m in months):
            skipped.append(ev)
            continue
        b = series[base]
        if kind == "level":
            if b <= 0:
                skipped.append(ev)
                continue
            paths.append([series[m] / b - 1.0 for m in months])
        else:
            paths.append([series[m] - b for m in months])
        used.append(ev)
    n = len(paths)
    mean = [sum(p[i] for p in paths) / n for i in range(len(offsets))] if n else []
    median = [_median([p[i] for p in paths]) for i in range(len(offsets))] if n else []
    return {"offsets": offsets, "n": n, "events": used, "skipped": skipped, "paths": paths, "mean": mean, "median": median}


def derive_rate_events(rate: dict[str, float], threshold: float) -> list[dict]:
    """Months where a rate moved by at least `threshold` points vs. the month before."""
    out = []
    for m in sorted(rate, key=_month_index):
        prev = shift_month(m, -1)
        if prev not in rate:
            continue
        d = rate[m] - rate[prev]
        if abs(d) >= threshold:
            out.append({"month": m, "change": d, "type": "hike" if d > 0 else "cut"})
    return out
