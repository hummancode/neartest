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
