"""Build site/data/reel_tablo.json from raw series.

Usage:
  python -m pipeline.build            # real data only (data/raw/), fails if missing
  python -m pipeline.build --sample   # fill missing series with SYNTHETIC data, flagged
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline import sample
from pipeline.series import ASSETS, SERIES
from reel import engine as e

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "site" / "data" / "reel_tablo.json"


def load_series(allow_sample: bool) -> tuple[dict, dict]:
    """Return (series_by_name, is_sample_by_name)."""
    synthetic = sample.build_sample() if allow_sample else {}
    data, is_sample = {}, {}
    for name in SERIES:
        path = RAW / f"{name}.json"
        if path.exists():
            data[name] = json.loads(path.read_text())
            is_sample[name] = False
        elif allow_sample:
            data[name] = synthetic[name]
            is_sample[name] = True
        else:
            raise SystemExit(f"Eksik seri: {name} ({path}). Örnek veri için --sample kullan.")
    return data, is_sample


def asset_tl_series(asset: dict, data: dict) -> dict[str, float]:
    raw = data[asset["series"]]
    if asset["kind"] == "rate":
        return e.deposit_index(raw)
    if asset["kind"] == "usd_level":
        return e.to_tl(raw, data["usdtry"])
    return raw


def build(allow_sample: bool) -> dict:
    data, is_sample = load_series(allow_sample)
    cpi, usdtry = data["cpi_tr"], data["usdtry"]
    # Common end month: the latest month every input has.
    end = min(e.last_month(s) for s in data.values())

    rows = []
    for asset in ASSETS:
        tl = asset_tl_series(asset, data)
        used = {asset["series"], "cpi_tr", "usdtry"}
        windows = e.asset_windows(tl, cpi, usdtry, end)
        trend_months = [e.shift_month(end, -k) for k in range(59, -1, -1)]
        trend = [round(tl[m] / cpi[m], 6) for m in trend_months if m in tl and m in cpi]
        rows.append({
            "id": asset["id"],
            "label": asset["label"],
            "sample": any(is_sample[s] for s in used),
            "windows": [w.__dict__ for w in windows],
            "real_trend_5y": trend,   # TL level deflated by CPI, last 60 months
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "end_month": end,
        "sample": any(r["sample"] for r in rows),
        "sources": {
            name: {k: SERIES[name][k] for k in ("label", "source", "code", "verified")}
            | {"sample": is_sample[name]}
            for name in SERIES
        },
        "notes": [
            "Getiriler kümülatif ve yıllık bileşik olarak verilir.",
            "Reel getiri: (1 + nominal) / (1 + TÜFE değişimi) − 1.",
            "Mevduat: aylık bileşik, stopaj hariç.",
            "Vergi, komisyon ve kur makası dahil değildir.",
            "Yatırım tavsiyesi değildir.",
        ],
        "rows": rows,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    args = p.parse_args()
    result = build(args.sample)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    flag = "  [ÖRNEK VERİ]" if result["sample"] else ""
    print(f"yazıldı: {OUT.relative_to(ROOT)}  bitiş ayı: {result['end_month']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
