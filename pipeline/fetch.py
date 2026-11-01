"""Fetch real series from EVDS into data/raw/<name>.json as {"YYYY-MM": value}.

Usage:  EVDS_API_KEY=... python -m pipeline.fetch
Series whose code is still None are skipped with a warning.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pipeline.series import SERIES

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
START = "01-01-2014"


def _to_month_map(df, code: str) -> dict[str, float]:
    col = code.replace(".", "_")
    out = {}
    for _, row in df.iterrows():
        value = row.get(col)
        if value is None or value != value:  # NaN check
            continue
        tarih = str(row["Tarih"])  # monthly: "2024-1"; daily: "01-01-2024"
        if tarih.count("-") == 1:
            year, month = tarih.split("-")
        else:
            _, month, year = tarih.split("-")
        out[f"{int(year):04d}-{int(month):02d}"] = float(value)
    return out


def main() -> int:
    key = os.environ.get("EVDS_API_KEY")
    if not key:
        print("EVDS_API_KEY yok. Örnek veri için: python -m pipeline.build --sample")
        return 1
    from evds import evdsAPI

    api = evdsAPI(key)
    RAW.mkdir(parents=True, exist_ok=True)
    for name, meta in SERIES.items():
        code = meta["code"]
        if meta["source"] != "TCMB EVDS" and not meta["source"].endswith("EVDS üzerinden"):
            print(f"skip {name}: kaynak EVDS değil ({meta['source']})")
            continue
        if not code:
            print(f"skip {name}: seri kodu henüz doğrulanmadı")
            continue
        # Monthly average for everything (aggregation 'avg', frequency 5 = monthly).
        df = api.get_data([code], startdate=START, enddate="", aggregation_types="avg", frequency=5)
        series = _to_month_map(df, code)
        if not series:
            print(f"UYARI {name}: boş veri döndü")
            continue
        (RAW / f"{name}.json").write_text(json.dumps(series, indent=0))
        print(f"ok {name}: {len(series)} ay")
    return 0


if __name__ == "__main__":
    sys.exit(main())
