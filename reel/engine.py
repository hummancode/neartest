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


# ---------------------------------------------------------------------------
# Credit card: paying only the minimum
# ---------------------------------------------------------------------------

def card_minimum_payoff(*, balance: float, monthly_rate: float, kkdf: float, bsmv: float,
                        min_share: float, min_floor: float, max_months: int = 600) -> dict:
    """Month-by-month card debt when only the minimum is paid and nothing new is spent.

    Each month interest (+ KKDF + BSMV on it) is added, then the minimum payment
    max(min_share x balance, min_floor), capped at the balance, is paid. Simplification:
    banks compute card interest daily; this uses monthly steps.
    """
    if balance <= 0 or not 0 < min_share <= 1:
        raise SeriesError("balance must be positive and minimum share in (0, 1]")
    bal, balances = balance, [balance]
    paid = interest_total = tax_total = 0.0
    months = 0
    while bal > 1e-9 and months < max_months:
        months += 1
        interest = bal * monthly_rate
        tax = interest * (kkdf + bsmv)
        bal += interest + tax
        pay = min(bal, max(min_share * bal, min_floor))
        bal -= pay
        paid += pay
        interest_total += interest
        tax_total += tax
        balances.append(max(bal, 0.0))
    return {"months": months, "paid_off": bal <= 1e-9, "total_paid": paid, "total_interest": interest_total,
            "total_tax": tax_total, "remaining": max(bal, 0.0), "balances": balances}


# ---------------------------------------------------------------------------
# Loan restructuring (refinancing)
# ---------------------------------------------------------------------------

def refinance_compare(*, balance: float, rate_old: float, months_old: int, rate_new: float, months_new: int,
                      kkdf: float, bsmv: float, prepay_penalty: float, new_fees: float, fees_financed: bool,
                      annual_discount: float) -> dict:
    """Keep paying the current loan, or close it and take a new one?

    New principal = remaining balance x (1 + early repayment fee) (+ fees if added to
    the loan). Both plans are compared by total paid and by present value at your own
    discount rate (what your money earns elsewhere).
    """
    if balance <= 0 or months_old <= 0 or months_new <= 0:
        raise SeriesError("balance and terms must be positive")
    tax = 1.0 + kkdf + bsmv
    old_payment = mortgage_payment(balance, rate_old * tax, months_old)
    new_principal = balance * (1.0 + prepay_penalty) + (new_fees if fees_financed else 0.0)
    upfront = 0.0 if fees_financed else new_fees
    new_payment = mortgage_payment(new_principal, rate_new * tax, months_new)
    md = (1.0 + annual_discount) ** (1 / 12) - 1.0
    pv_old = present_value([old_payment] * months_old, md, 1)
    pv_new = upfront + present_value([new_payment] * months_new, md, 1)
    saving = pv_old - pv_new
    return {
        "old_payment": old_payment, "new_payment": new_payment, "new_principal": new_principal,
        "upfront": upfront,
        "total_old": old_payment * months_old, "total_new": upfront + new_payment * months_new,
        "pv_old": pv_old, "pv_new": pv_new, "saving_pv": saving,
        "better": "equal" if abs(saving) < 1e-9 else ("new" if saving > 0 else "old"),
    }


# ---------------------------------------------------------------------------
# Deposit net return, savings goal, purchasing-power half-life
# ---------------------------------------------------------------------------

def deposit_net(*, principal: float, gross_annual: float, days: int, withholding: float, inflation: float) -> dict:
    """Net return of a time deposit after withholding tax, rolled over at the same terms for a year.

    Turkish deposits pay simple interest for the term: principal x rate x days / 365.
    """
    if principal <= 0 or days <= 0:
        raise SeriesError("principal and term must be positive")
    gross_term = gross_annual * days / 365.0
    net_term = gross_term * (1.0 - withholding)
    net_annual = (1.0 + net_term) ** (365.0 / days) - 1.0
    return {
        "gross_interest_term": principal * gross_term,
        "tax_term": principal * gross_term * withholding,
        "net_interest_term": principal * net_term,
        "net_term_rate": net_term,
        "net_annual": net_annual,
        "real_annual": real_return(net_annual, inflation),
    }


def required_saving(*, target_today: float, years: int, inflation: float, nominal_return: float,
                    current: float, grow_with_inflation: bool) -> dict:
    """Monthly saving needed to reach `target_today` (in today's TL) after `years`.

    Contributions are made at month ends; if grow_with_inflation, they rise with
    inflation every month (constant in real terms) and `monthly` is the first one.
    """
    if target_today <= 0 or years <= 0:
        raise SeriesError("target and years must be positive")
    n = 12 * years
    mi = (1.0 + inflation) ** (1 / 12) - 1.0
    mr = (1.0 + nominal_return) ** (1 / 12) - 1.0
    target_nominal = target_today * (1.0 + inflation) ** years
    fv_current = current * (1.0 + mr) ** n
    factor = sum(((1.0 + mi) ** (t - 1) if grow_with_inflation else 1.0) * (1.0 + mr) ** (n - t) for t in range(1, n + 1))
    monthly = max(0.0, (target_nominal - fv_current) / factor)
    contributions = sum(monthly * ((1.0 + mi) ** (t - 1) if grow_with_inflation else 1.0) for t in range(1, n + 1))
    return {"monthly": monthly, "target_nominal": target_nominal, "fv_current": fv_current,
            "total_contributed": contributions + current}


def half_life_years(annual_inflation: float) -> float:
    """Years until money loses half its purchasing power at a constant inflation rate."""
    if annual_inflation <= 0:
        raise SeriesError("inflation must be positive")
    return math.log(2.0) / math.log(1.0 + annual_inflation)


def breakeven_gross_rate(*, inflation: float, days: int, withholding: float) -> float:
    """Gross annual deposit rate whose net, rolled-over return exactly matches inflation."""
    if days <= 0 or withholding >= 1:
        raise SeriesError("term must be positive and withholding below 100 %")
    net_term = (1.0 + inflation) ** (days / 365.0) - 1.0
    return net_term / (1.0 - withholding) * 365.0 / days


# ---------------------------------------------------------------------------
# Province household wealth — a transparent MODEL ESTIMATE, not an official statistic
# ---------------------------------------------------------------------------

def province_wealth(*, population: float, deposits_tl: float, m2_price: float, household_size: float,
                    ownership_rate: float, dwelling_m2: float, household_deposit_share: float) -> dict:
    """Rough household wealth of a province = owner-occupied housing + households' bank deposits.

    housing   = (population / household_size) x ownership_rate x dwelling_m2 x m2_price
    financial = deposits_tl x household_deposit_share
    Leaves out second homes, land, vehicles, gold under the mattress, securities and debt.
    """
    if population <= 0 or household_size <= 0 or dwelling_m2 < 0 or m2_price < 0 or deposits_tl < 0:
        raise SeriesError("population and household size must be positive; amounts non-negative")
    for share in (ownership_rate, household_deposit_share):
        if not 0 <= share <= 1:
            raise SeriesError("shares must be between 0 and 1")
    households = population / household_size
    housing = households * ownership_rate * dwelling_m2 * m2_price
    financial = deposits_tl * household_deposit_share
    total = housing + financial
    return {"households": households, "housing": housing, "financial": financial, "total": total,
            "per_household": total / households, "per_capita": total / population}


# ---------------------------------------------------------------------------
# Distributions (same algorithms in the TypeScript port, so results match exactly)
# ---------------------------------------------------------------------------

def normal_cdf(x: float) -> float:
    """Standard normal CDF (Marsaglia's series; ~1e-15 accurate for |x| < 8)."""
    if x < -8:
        return 0.0
    if x > 8:
        return 1.0
    s, t, b, q, i = x, 0.0, x, x * x, 1.0
    while s != t:
        t = s
        i += 2.0
        b *= q / i
        s = t + b
    return 0.5 + s * math.exp(-0.5 * q - 0.91893853320467274178)


def normal_ppf(p: float) -> float:
    """Inverse standard normal CDF: Acklam's approximation refined by Newton steps."""
    if not 0 < p < 1:
        raise SeriesError("p must be in (0, 1)")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02, 1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00, -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
    lo = 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    elif p > 1 - lo:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    for _ in range(3):                                    # Newton refinement against our CDF
        pdf = math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
        if pdf == 0:
            break
        x -= (normal_cdf(x) - p) / pdf
    return x


def gini_from_sigma(sigma: float) -> float:
    """Gini coefficient of a lognormal distribution with log-standard-deviation sigma."""
    return 2.0 * normal_cdf(sigma / math.sqrt(2.0)) - 1.0


def sigma_from_gini(gini: float) -> float:
    if not 0 < gini < 1:
        raise SeriesError("Gini must be in (0, 1)")
    return math.sqrt(2.0) * normal_ppf((gini + 1.0) / 2.0)


def top_share_lognormal(sigma: float, p: float) -> float:
    """Share of the total held by the top fraction p of a lognormal population."""
    return 1.0 - normal_cdf(normal_ppf(1.0 - p) - sigma)


def wealth_inequality(*, income_gini: float, multiplier: float) -> dict:
    """MODEL: wealth assumed lognormal with dispersion = multiplier x that implied by the income Gini.

    Wealth is usually more unequal than income (multiplier > 1); the multiplier is an assumption.
    """
    if multiplier <= 0:
        raise SeriesError("multiplier must be positive")
    s_inc = sigma_from_gini(income_gini)
    s_w = s_inc * multiplier
    return {"sigma_income": s_inc, "sigma_wealth": s_w, "wealth_gini": gini_from_sigma(s_w),
            "top10_share": top_share_lognormal(s_w, 0.10), "top1_share": top_share_lognormal(s_w, 0.01),
            "median_to_mean": math.exp(-s_w * s_w / 2.0)}


def gold_allocation(households: list[float], wealth_per_household: list[float], *, beta: float, total: float) -> list[float]:
    """MODEL: split a national total (e.g. grams of household gold) across provinces.

    weight_i = households_i x wealth_per_household_i ** beta  (beta 0: per household, 1: per wealth).
    """
    if len(households) != len(wealth_per_household) or not households:
        raise SeriesError("need matching, non-empty lists")
    w = [h * (max(x, 0.0) ** beta) for h, x in zip(households, wealth_per_household)]
    s = sum(w)
    if s <= 0:
        raise SeriesError("weights sum to zero")
    return [total * x / s for x in w]


def housing_affordability(*, m2_price: float, rent_m2: float, monthly_wage: float, dwelling_m2: float) -> dict:
    """Gross rental yield, years of rent to repay the price, price in years of wages, rent / wage."""
    if m2_price <= 0 or rent_m2 <= 0 or monthly_wage <= 0 or dwelling_m2 <= 0:
        raise SeriesError("inputs must be positive")
    price = m2_price * dwelling_m2
    rent = rent_m2 * dwelling_m2
    return {"price": price, "rent": rent, "gross_yield": 12 * rent / price, "amortization_years": price / (12 * rent),
            "price_to_annual_wage": price / (12 * monthly_wage), "rent_to_wage": rent / monthly_wage}


# ---------------------------------------------------------------------------
# Economic structure
# ---------------------------------------------------------------------------

def shares(values: dict[str, float]) -> dict[str, float]:
    """Parts -> shares of the total."""
    total = sum(v for v in values.values() if v > 0)
    if total <= 0:
        raise SeriesError("total must be positive")
    return {k: max(v, 0.0) / total for k, v in values.items()}


def location_quotients(local: dict[str, float], national: dict[str, float]) -> dict[str, float]:
    """LQ = local share / national share. > 1: the place is more specialised in that sector than the country."""
    return {k: local[k] / national[k] for k in local if national.get(k, 0) > 0}


def hhi(share_values: dict[str, float]) -> float:
    """Herfindahl–Hirschman index of shares (1 = one sector only, 1/n = n equal sectors)."""
    return sum(s * s for s in share_values.values())


def lorenz_lognormal(p: float, sigma: float) -> float:
    """Lorenz curve of a lognormal distribution: L(p) = Phi(Phi^-1(p) - sigma)."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    return normal_cdf(normal_ppf(p) - sigma)


def growth_windows(points: dict[str, float], windows=(1, 5, 10)) -> dict[int, dict]:
    """Change over the last n years of a yearly series {year: value}.

    For each n whose base year (last year − n) exists with a positive value:
    change (absolute), change_pct (cumulative, %) and annual_pct (geometric average, %).
    """
    if not points:
        return {}
    last = max(points, key=int)
    end = points[last]
    out = {}
    for n in windows:
        base_year = str(int(last) - n)
        start = points.get(base_year)
        if start is None or start <= 0:
            continue
        tot = total_return(start, end)
        out[n] = {"from": base_year, "to": last, "start": start, "end": end, "change": end - start,
                  "change_pct": 100 * tot, "annual_pct": 100 * annualize(tot, n)}
    return out


def big_mac(local_price: float, fx: float, us_price: float) -> dict:
    """Big Mac index (The Economist's raw index, against the US dollar).

    dollar_price = local / fx; implied_rate = local / us_price (the rate that would equalise the prices);
    valuation = implied_rate / fx − 1 (> 0: by this measure the currency buys fewer burgers than its rate
    implies, i.e. it is "overvalued"; < 0 "undervalued"). A light-hearted PPP guide, not a forecast.
    """
    if fx <= 0 or us_price <= 0 or local_price <= 0:
        raise SeriesError("prices and exchange rate must be positive")
    implied = local_price / us_price
    return {"dollar_price": local_price / fx, "implied_rate": implied, "valuation": implied / fx - 1.0}


def change_over(values: list[float], periods_back: int, periods_per_year: int) -> dict | None:
    """Change from `periods_back` observations before the last one to the last (equally spaced series).

    Returns change_pct (cumulative %) and annual_pct (geometric, %), or None without enough history."""
    if periods_back <= 0 or periods_per_year <= 0:
        raise SeriesError("periods must be positive")
    if len(values) <= periods_back:
        return None
    start, end = values[-1 - periods_back], values[-1]
    tot = total_return(start, end)
    return {"change_pct": 100 * tot, "annual_pct": 100 * annualize(tot, periods_back / periods_per_year)}


def drawdown(values: list[float]) -> dict:
    """Last value relative to the running peak: drawdown_pct = last / peak − 1 (≤ 0)."""
    if not values:
        raise SeriesError("empty series")
    k = max(range(len(values)), key=lambda i: values[i])
    return {"peak": values[k], "peak_index": k, "drawdown_pct": 100 * (values[-1] / values[k] - 1)}


def net_worth_timeline(items: list[dict]) -> list[dict]:
    """Net worth on every date where any item has a valuation.

    items: {"id", "side": "asset"|"liability", "kind", "valuations": [[YYYY-MM-DD, value TL], ...], "sold": date|None}
    An item's value on a date is its latest valuation on or before that date (none before its first
    valuation); from its "sold" date on it counts as zero (excluded). Liabilities are subtracted.
    Returns [{date, assets, liabilities, net, by_kind}] sorted by date; by_kind holds liabilities as negatives.
    """
    for it in items:
        if it.get("side") not in ("asset", "liability"):
            raise SeriesError(f"side must be asset or liability: {it.get('id')}")
    vals = {it["id"]: sorted((d, float(v)) for d, v in it["valuations"]) for it in items}
    dates = sorted({d for v in vals.values() for d, _ in v})
    out = []
    for d in dates:
        assets = liabilities = 0.0
        by_kind: dict[str, float] = {}
        for it in items:
            sold = it.get("sold")
            if sold and d >= sold:
                continue
            known = [v for vd, v in vals[it["id"]] if vd <= d]
            if not known:
                continue
            v = known[-1]
            sign = 1.0 if it["side"] == "asset" else -1.0
            if sign > 0:
                assets += v
            else:
                liabilities += v
            by_kind[it["kind"]] = by_kind.get(it["kind"], 0.0) + sign * v
        out.append({"date": d, "assets": assets, "liabilities": liabilities, "net": assets - liabilities, "by_kind": by_kind})
    return out


# --- taxes (rates come from the regulated-parameter registry; nothing hard-coded here) ---------

def _check_brackets(brackets: list) -> None:
    if not brackets or brackets[-1][0] is not None:
        raise SeriesError("last bracket must be open-ended (upper = None)")
    uppers = [b[0] for b in brackets[:-1]]
    if any(u is None or u <= 0 for u in uppers) or uppers != sorted(set(uppers)):
        raise SeriesError("bracket thresholds must be positive and increasing")


def progressive_tax(base: float, brackets: list) -> float:
    """Tax on `base` under a progressive schedule [[upper, rate], ..., [None, rate]] (uppers cumulative)."""
    _check_brackets(brackets)
    if base <= 0:
        return 0.0
    tax, lower = 0.0, 0.0
    for upper, rate in brackets:
        top = base if upper is None else min(base, upper)
        if top > lower:
            tax += (top - lower) * rate
        if upper is None or base <= upper:
            break
        lower = upper
    return tax


def payroll_year(p: dict) -> dict:
    """Monthly payroll for an employee (Turkish wage tax logic), month by month.

    p: gross [monthly gross wages, Jan…], sgk_rate, unemp_rate, stamp_rate, brackets (annual, cumulative),
       sgk_ceiling (monthly SGK base cap, optional), min_wage_gross (optional: minimum-wage income and stamp
       tax exemption — the tax that the minimum wage itself would bear is deducted, cumulatively).
    Income tax each month = T(cumulative base) − T(previous cumulative base); base = gross − SGK − unemployment.
    """
    br = p["brackets"]
    _check_brackets(br)
    cap = p.get("sgk_ceiling")
    mw = p.get("min_wage_gross")
    ins = p["sgk_rate"] + p["unemp_rate"]
    rows, cum, mw_cum = [], 0.0, 0.0
    for m, gross in enumerate(p["gross"], start=1):
        sgk_base = min(gross, cap) if cap else gross
        sgk, unemp = sgk_base * p["sgk_rate"], sgk_base * p["unemp_rate"]
        base = gross - sgk - unemp
        tax = progressive_tax(cum + base, br) - progressive_tax(cum, br)
        cum += base
        stamp = gross * p["stamp_rate"]
        ex_tax = ex_stamp = 0.0
        if mw:
            mw_base = mw * (1 - ins)
            ex_tax = progressive_tax(mw_cum + mw_base, br) - progressive_tax(mw_cum, br)
            mw_cum += mw_base
            ex_stamp = mw * p["stamp_rate"]
        tax_net, stamp_net = max(0.0, tax - ex_tax), max(0.0, stamp - ex_stamp)
        rows.append({"month": m, "gross": gross, "sgk": sgk, "unemp": unemp, "tax_base": base, "cum_base": cum,
                     "income_tax": tax_net, "stamp": stamp_net, "tax_exemption": tax - tax_net, "stamp_exemption": stamp - stamp_net,
                     "net": gross - sgk - unemp - tax_net - stamp_net})
    keys = ("gross", "sgk", "unemp", "income_tax", "stamp", "net")
    totals = {k: sum(r[k] for r in rows) for k in keys}
    return {"rows": rows, "totals": totals, "avg_net": totals["net"] / len(rows) if rows else 0.0}


def gross_for_net(target_net: float, p: dict, month: int = 1) -> float:
    """Constant monthly gross whose net in `month` equals target_net (bisection on payroll_year)."""
    if target_net <= 0:
        raise SeriesError("target net must be positive")
    net_of = lambda g: payroll_year({**p, "gross": [g] * month})["rows"][-1]["net"]
    lo, hi = target_net, target_net * 3
    while net_of(hi) < target_net:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if net_of(mid) < target_net:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-9:
            break
    return (lo + hi) / 2


def rental_income_tax(*, annual_rent: float, exemption: float, method: str, actual_expenses: float, brackets: list,
                      lump_rate: float) -> dict:
    """Simplified residential rental income tax for one year.

    taxable_rent = rent − exemption (if the exemption applies; the caller decides eligibility).
    method "lump": expense = lump_rate × taxable rent (götürü gider); "actual": actual expenses × taxable/total rent.
    tax = progressive_tax(taxable_rent − expense). Other income, prepaid withholding and declaration rules are ignored.
    """
    if method not in ("lump", "actual"):
        raise SeriesError("method must be 'lump' or 'actual'")
    taxable = max(0.0, annual_rent - max(0.0, exemption))
    if method == "lump":
        expense = lump_rate * taxable
    else:
        expense = actual_expenses * (taxable / annual_rent) if annual_rent > 0 else 0.0
    base = max(0.0, taxable - expense)
    tax = progressive_tax(base, brackets)
    return {"taxable_rent": taxable, "expense": expense, "base": base, "tax": tax,
            "effective_rate": tax / annual_rent if annual_rent > 0 else 0.0}


# ---------------------------------------------------------------------------
# Early repayment
# ---------------------------------------------------------------------------

def prepayment(*, principal: float, monthly_rate: float, months: int, kkdf: float, bsmv: float,
               after_payments: int, amount: float, mode: str, fee_rate: float) -> dict:
    """Partial or full early repayment after `after_payments` installments of an equal-installment loan.

    mode "payment": keep the remaining term, the installment falls; mode "term": keep the installment, the term
    shortens (last payment smaller). fee_rate: early-repayment fee as a share of the amount prepaid.
    saved = remaining payments without prepaying − (prepaid + fee + remaining payments after prepaying).
    """
    if not 1 <= after_payments < months:
        raise SeriesError("after_payments must be between 1 and term − 1")
    if amount <= 0 or mode not in ("payment", "term"):
        raise SeriesError("amount must be positive and mode 'payment' or 'term'")
    plan = amortization(principal, monthly_rate, months, kkdf, bsmv)
    pay = plan[0]["installment"]
    balance = plan[after_payments - 1]["balance"]
    remaining_before = sum(r["installment"] for r in plan[after_payments:])
    prepaid = min(amount, balance)
    full = prepaid >= balance - 1e-9
    fee = prepaid * fee_rate
    left = balance - prepaid
    t_load = 1.0 + kkdf + bsmv
    if full or left <= 1e-9:
        new_pay, new_months, remaining_after = 0.0, 0, 0.0
    elif mode == "payment":
        rest = amortization(left, monthly_rate, months - after_payments, kkdf, bsmv)
        new_pay, new_months, remaining_after = rest[0]["installment"], len(rest), sum(r["installment"] for r in rest)
    else:
        new_pay, new_months, remaining_after, bal = pay, 0, 0.0, left
        while bal > 1e-9:
            charge = bal * monthly_rate * t_load
            new_months += 1
            if pay - charge >= bal:
                remaining_after += bal + charge
                bal = 0.0
            else:
                remaining_after += pay
                bal -= pay - charge
            if new_months > 10 * months:
                raise SeriesError("installment does not cover the interest")
    return {"installment_before": pay, "balance_at": balance, "prepaid": prepaid, "full": full, "fee": fee,
            "remaining_before": remaining_before, "remaining_after": remaining_after,
            "new_installment": new_pay, "new_months": new_months,
            "months_saved": (months - after_payments) - new_months,
            "saved": remaining_before - (prepaid + fee + remaining_after)}


# ---------------------------------------------------------------------------
# Capital gains on property, property tax, private pension (BES)
# ---------------------------------------------------------------------------

def capital_gain_tax(*, sale_price: float, cost: float, purchase_expenses: float, sale_expenses: float,
                     ppi_increase: float, exemption: float, brackets: list, exempt_holding: bool,
                     index_threshold: float) -> dict:
    """Simplified capital gains tax on selling real estate (değer artış kazancı).

    Cost (+ purchase expenses) is indexed by the PPI increase when that increase is at least
    `index_threshold`; gain = sale − sale expenses − (indexed) cost; taxable = gain − exemption;
    tax = progressive_tax(taxable). exempt_holding=True (the caller decided the holding-period exemption applies) → 0.
    """
    base_cost = cost + purchase_expenses
    indexed = ppi_increase >= index_threshold
    indexed_cost = base_cost * (1.0 + ppi_increase) if indexed else base_cost
    gain = sale_price - sale_expenses - indexed_cost
    if exempt_holding:
        return {"exempt": True, "indexed": indexed, "indexed_cost": indexed_cost, "gain": gain, "taxable": 0.0, "tax": 0.0, "effective_rate": 0.0}
    taxable = max(0.0, gain - max(0.0, exemption))
    tax = progressive_tax(taxable, brackets)
    return {"exempt": False, "indexed": indexed, "indexed_cost": indexed_cost, "gain": gain, "taxable": taxable, "tax": tax,
            "effective_rate": tax / gain if gain > 0 else 0.0}


def property_tax(*, value: float, rate_per_mille: float, multiplier: float) -> dict:
    """Annual property tax = value × rate (per mille) × multiplier (e.g. 2 in metropolitan municipalities); paid in 2 installments."""
    annual = value * rate_per_mille / 1000.0 * multiplier
    return {"annual": annual, "installment": annual / 2}


def bes_projection(*, monthly: float, years: int, annual_return: float, annual_fee: float, state_rate: float,
                   vesting: float, withholding: float, inflation: float, contribution_growth: float) -> dict:
    """Private pension (BES) projection with monthly contributions paid at the start of each month.

    Net fund growth: (1 + annual_return)(1 − annual_fee) per year, compounded monthly. Contributions grow by
    `contribution_growth` once a year. State contribution = state_rate × own contribution (caps ignored), of which
    `vesting` is paid at exit. Withholding applies to gains (own + vested state). Returns balances, exit value,
    its value in today's money and the saver's annual IRR.
    """
    if years <= 0 or monthly <= 0:
        raise SeriesError("years and contribution must be positive")
    n = 12 * years
    m = ((1.0 + annual_return) * (1.0 - annual_fee)) ** (1.0 / 12.0) - 1.0
    own_paid = state_paid = own_bal = state_bal = real_paid = 0.0
    flows = []
    for t in range(n):
        c = monthly * (1.0 + contribution_growth) ** (t // 12)
        grow = (1.0 + m) ** (n - t)
        own_paid += c
        real_paid += c / (1.0 + inflation) ** (t / 12.0)
        state_paid += state_rate * c
        own_bal += c * grow
        state_bal += state_rate * c * grow
        flows.append(-c)
    vested = vesting * state_bal
    tax = withholding * ((own_bal - own_paid) + vesting * (state_bal - state_paid))
    tax = max(0.0, tax)
    net_exit = own_bal + vested - tax
    flows.append(net_exit)
    mi = irr(flows)
    annual_irr = (1.0 + mi) ** 12 - 1.0
    return {"own_paid": own_paid, "real_own_paid": real_paid, "state_paid": state_paid, "own_balance": own_bal, "state_balance": state_bal,
            "vested_state": vested, "tax": tax, "net_exit": net_exit,
            "real_net_exit": net_exit / (1.0 + inflation) ** years, "annual_irr": annual_irr,
            "real_irr": real_return(annual_irr, inflation)}


def percentile_rank(value: float, history: list[float]) -> float:
    """Share of observations in `history` that are ≤ value (0 = below all, 1 = at or above all)."""
    if not history:
        raise SeriesError("empty history")
    return sum(1 for h in history if h <= value) / len(history)


def window_stats(values: list[float]) -> dict:
    """Min, max, median of a window and where its LAST value sits in it (percentile rank)."""
    if not values:
        raise SeriesError("empty window")
    s = sorted(values)
    n = len(s)
    med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"min": s[0], "max": s[-1], "median": med, "percentile": percentile_rank(values[-1], values), "n": n}
