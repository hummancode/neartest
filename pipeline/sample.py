"""SYNTHETIC sample data so the site can be built before an API key exists.

These numbers are NOT real. They are smooth made-up paths with roughly
plausible shapes. Every output built from them carries `sample: true` and the
site shows a red "ÖRNEK VERİ" banner. Delete data/raw/ usage of this module
once real data flows.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from reel.engine import shift_month

START = "2014-01"
END = "2026-09"


def _months():
    m, out = START, []
    while True:
        out.append(m)
        if m == END:
            return out
        m = shift_month(m, 1)


def _path(start_value, annual_growth, wobble, phase):
    out = {}
    for k, m in enumerate(_months()):
        t = k / 12
        out[m] = start_value * (1 + annual_growth) ** t * (1 + wobble * math.sin(t * 1.7 + phase))
    return out


# Made-up group growth rates and weights. NOT real TÜİK figures.
_GROUP_GROWTH = {
    "food": 0.36, "alcohol_tobacco": 0.30, "clothing": 0.24, "housing": 0.42,
    "furnishing": 0.31, "health": 0.29, "transport": 0.35, "communication": 0.22,
    "recreation": 0.30, "education": 0.40, "restaurants": 0.39, "misc": 0.32,
}
SAMPLE_WEIGHTS = {
    "food": 0.24, "alcohol_tobacco": 0.04, "clothing": 0.06, "housing": 0.15,
    "furnishing": 0.08, "health": 0.03, "transport": 0.16, "communication": 0.03,
    "recreation": 0.03, "education": 0.02, "restaurants": 0.09, "misc": 0.07,
}


def build_sample() -> dict[str, dict[str, float]]:
    rates = {m: 0.10 + 0.25 * max(0.0, math.sin(k / 30)) for k, m in enumerate(_months())}
    groups = {
        f"cpi_{gid}": _path(100.0, g, 0.0, 0.0) for gid, g in _GROUP_GROWTH.items()
    }
    rates_credit = {m: r + 0.08 for m, r in rates.items()}
    market = {
        "car_cpi": _path(100.0, 0.40, 0.04, 0.7),
        "rent_cpi": _path(100.0, 0.45, 0.0, 0.0),
        "house_tr": _path(100.0, 0.42, 0.05, 1.5),
        "house_ist": _path(100.0, 0.45, 0.06, 1.2),
        "house_ank": _path(100.0, 0.40, 0.05, 1.9),
        "house_izm": _path(100.0, 0.43, 0.05, 2.4),
    }
    months = _months()
    wave = lambda k, a, b, c, d: a + b * math.sin(k / c + d)
    macro = {
        "gdp_growth": {m: wave(k, 4.0, 3.0, 9.0, 0.3) for k, m in enumerate(months) if m[5:] in ("03", "06", "09", "12")},
        "gdp_usd_pc": {m: 9000 + 900 * math.sin(k / 30) + 25 * k for k, m in enumerate(months) if m[5:] == "12"},
        "unemployment": {m: wave(k, 10.5, 1.8, 14.0, 1.0) for k, m in enumerate(months)},
        "current_account": {m: wave(k, -25.0, 20.0, 16.0, 2.0) for k, m in enumerate(months)},
        "reserves": {m: 100 + 25 * math.sin(k / 20 + 0.5) + 0.3 * k for k, m in enumerate(months)},
        # step-shaped like a real policy rate (moves in 2.5-point steps, holds in between)
        "policy_rate": {m: max(5.0, round(wave(k, 20.0, 15.0, 18.0, 4.0) / 2.5) * 2.5) for k, m in enumerate(months)},
        "cds_5y": {m: wave(k, 380.0, 170.0, 15.0, 2.5) for k, m in enumerate(months)},
        "exports_12m": {m: 150 + 1.0 * k + 15 * math.sin(k / 11.0) for k, m in enumerate(months)},
        "imports_12m": {m: 200 + 1.3 * k + 25 * math.sin(k / 9.0 + 1) for k, m in enumerate(months)},
        "budget_balance_gdp": {m: wave(k, -2.5, 1.8, 12.0, 0.8) for k, m in enumerate(months) if m[5:] in ("03", "06", "09", "12")},
    }
    return groups | market | macro | {
        "credit_rate": rates_credit,
        "usdtry": _path(2.2, 0.30, 0.03, 0.0),
        "eurtry": _path(3.0, 0.29, 0.03, 0.5),
        "cpi_tr": _path(230.0, 0.33, 0.0, 0.0),
        "deposit_rate": rates,
        "gold_gram_tl": _path(90.0, 0.38, 0.05, 1.0),
        "bist100": _path(70.0, 0.30, 0.12, 2.0),
        "sp500_usd": _path(1800.0, 0.10, 0.06, 3.0),
    }


def write(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name, series in build_sample().items():
        (dest / f"{name}.json").write_text(json.dumps(series, indent=0))


def sample_worldbank() -> dict[str, dict[str, dict[str, float]]]:
    """SYNTHETIC annual country data (2005–2024) for the country comparison page. NOT real."""
    from pipeline.worldbank import COUNTRIES, INDICATORS
    out = {}
    for ki, key in enumerate(INDICATORS):
        out[key] = {}
        for ci, (iso, _) in enumerate(COUNTRIES):
            series = {}
            for y in range(2005, 2025):
                t = y - 2005
                w = math.sin(t / 3.0 + ci * 0.7 + ki)
                if key == "inflation":
                    v = 4 + 3 * ci % 9 + 3 * w + (25 * max(0.0, t - 13) / 7 if iso in ("TUR", "ARG") else 0)
                elif key == "gdp_growth":
                    v = 3 + 2.5 * w
                elif key == "gdp_pc_usd":
                    v = (3000 + 1100 * ci) * (1 + 0.03 * t) * (1 + 0.08 * w)
                elif key == "unemployment":
                    v = 6 + (ci * 1.3) % 8 + 1.5 * w
                elif key == "current_account":
                    v = -2 + 3 * w - (ci % 3)
                elif key == "population":
                    v = (20 + 25 * ((ci * 7) % 9)) * 1e6 * (1 + 0.011 * t) * (60 if iso == "IND" else 1)
                elif key in ("exports_gdp", "imports_gdp"):
                    v = 22 + 8 * w + (ci % 5) * 3 + (3 if key == "imports_gdp" else 0)
                elif key == "urban":
                    v = 60 + (ci * 5) % 30 + 0.3 * t
                else:
                    v = 2 + 4 * w - (8 if iso in ("TUR", "ARG") and t > 15 else 0)
                series[str(y)] = round(v, 2)
            out[key][iso] = series
    return out
