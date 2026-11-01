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
    return groups | {
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
