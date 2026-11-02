"""Fetch real series from EVDS into data/raw/<name>.json as {"YYYY-MM": value}.

Usage:  EVDS_API_KEY=... python -m pipeline.fetch
Series whose code is still None are skipped with a warning.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from pipeline.series import ALL_SERIES as SERIES

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
START = "01-01-2014"


# EVDS frequency codes (evds library): 5 monthly, 6 quarterly, 7 semiannual, 8 annual.
FREQ_CODE = {"M": 5, "Q": 6, "S": 7, "A": 8}


def frequency_for(meta: dict) -> int:
    return FREQ_CODE.get(meta.get("freq", "M"), 5)


def parse_evds_date(tarih: str) -> str:
    """EVDS 'Tarih' -> "YYYY-MM". Quarters/halves map to their last month, years to December."""
    t = tarih.strip().upper()
    m = re.fullmatch(r"(\d{4})-?Q([1-4])", t)
    if m:
        return f"{m[1]}-{int(m[2]) * 3:02d}"
    m = re.fullmatch(r"(\d{4})-?S([12])", t)
    if m:
        return f"{m[1]}-{int(m[2]) * 6:02d}"
    if re.fullmatch(r"\d{4}", t):
        return f"{t}-12"
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", t)
    if m and 1 <= int(m[2]) <= 12:
        return f"{m[1]}-{int(m[2]):02d}"
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{4})", t)
    if m and 1 <= int(m[2]) <= 12:
        return f"{m[3]}-{int(m[2]):02d}"
    raise ValueError(f"tanınmayan EVDS tarihi: {tarih!r}")


def _to_month_map(df, code: str) -> dict[str, float]:
    col = code.replace(".", "_")
    out = {}
    for _, row in df.iterrows():
        value = row.get(col)
        if value is None or value != value:  # NaN check
            continue
        out[parse_evds_date(str(row["Tarih"]))] = float(value)
    return out


def main() -> int:
    key = os.environ.get("EVDS_API_KEY")
    if not key:
        print("EVDS_API_KEY yok. Örnek veri için: python -m pipeline.build --sample")
        return 1
    from evds import evdsAPI

    api = evdsAPI(key)
    RAW.mkdir(parents=True, exist_ok=True)
    failures = 0
    for name, meta in SERIES.items():
        code = meta["code"]
        if "EVDS" not in meta["source"]:
            print(f"skip {name}: kaynak EVDS değil ({meta['source']})")
            continue
        if not code:
            print(f"skip {name}: seri kodu henüz doğrulanmadı")
            continue
        try:
            # Monthly series as monthly averages; quarterly/annual series at their own frequency.
            df = api.get_data([code], startdate=START, enddate="", aggregation_types="avg", frequency=frequency_for(meta))
            series = _to_month_map(df, code)
        except Exception as exc:  # one bad series must not stop the rest
            failures += 1
            print(f"HATA {name} ({code}): {exc}")
            continue
        if not series:
            print(f"UYARI {name}: boş veri döndü")
            continue
        (RAW / f"{name}.json").write_text(json.dumps(series, indent=0))
        print(f"ok {name}: {len(series)} dönem, son {max(series)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
