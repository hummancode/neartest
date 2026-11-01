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
import csv

from pipeline.series import ALL_SERIES, ASSETS, CPI_GROUPS, CPI_WEIGHTS_SOURCE, SERIES
from reel import engine as e

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "site" / "data" / "reel_tablo.json"
OUT_LEVELS = ROOT / "site" / "data" / "seviyeler.json"
OUT_GROUPS = ROOT / "site" / "data" / "tufe_gruplari.json"
OUT_RATES = ROOT / "site" / "data" / "reel_faiz.json"
WEIGHTS_CSV = ROOT / "data" / "manual" / "tufe_agirliklari.csv"

# Series the in-browser "nominal illusion" calculator needs, as raw monthly levels.
LEVEL_SERIES = ("cpi_tr", "usdtry", "gold_gram_tl")


def load_series(allow_sample: bool) -> tuple[dict, dict]:
    """Return (series_by_name, is_sample_by_name)."""
    synthetic = sample.build_sample() if allow_sample else {}
    data, is_sample = {}, {}
    for name in ALL_SERIES:
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


def build(allow_sample: bool) -> tuple[dict, dict, dict, dict]:
    data, is_sample = load_series(allow_sample)
    cpi, usdtry = data["cpi_tr"], data["usdtry"]
    # Common end month: the latest month every input has.
    end = min(e.last_month(s) for s in data.values())
    weights, weights_sample = load_weights(allow_sample)

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

    tablo = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "end_month": end,
        "sample": any(r["sample"] for r in rows),
        "sources": {
            name: {k: SERIES[name][k] for k in ("label", "source", "code", "verified")}
            | {"sample": is_sample[name], "last_month": e.last_month(data[name])}
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
    levels = build_levels(data, is_sample, end)
    levels["generated_at"] = tablo["generated_at"]
    groups = build_cpi_groups(data, is_sample, end, weights, weights_sample)
    groups["generated_at"] = tablo["generated_at"]
    rates = build_real_rates(data, is_sample, end)
    rates["generated_at"] = tablo["generated_at"]
    return tablo, levels, groups, rates


def load_weights(allow_sample: bool) -> tuple[dict[str, float], bool]:
    """Official CPI group weights from the manual CSV, or sample weights (flagged)."""
    if WEIGHTS_CSV.exists():
        with WEIGHTS_CSV.open(newline="", encoding="utf-8") as f:
            weights = {row["id"]: float(row["weight"]) for row in csv.DictReader(f)}
        missing = {g["id"] for g in CPI_GROUPS} - set(weights)
        if missing:
            raise SystemExit(f"{WEIGHTS_CSV} eksik gruplar: {sorted(missing)}")
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}, False
    if allow_sample:
        return dict(sample.SAMPLE_WEIGHTS), True
    raise SystemExit(f"Eksik: {WEIGHTS_CSV}. Örnek veri için --sample kullan.")


def build_cpi_groups(data: dict, is_sample: dict, end: str, weights: dict, weights_sample: bool) -> dict:
    """12-month inflation per CPI group plus headline, for the personal inflation page."""
    groups = []
    for g in CPI_GROUPS:
        name = f"cpi_{g['id']}"
        try:
            change = e.window_return(data[name], end, 12)
        except e.SeriesError:
            change = None
        groups.append({
            "id": g["id"],
            "label": g["label"],
            "weight": weights.get(g["id"]),
            "change_12m": change,
            "sample": is_sample[name],
        })
    group_names = [f"cpi_{g['id']}" for g in CPI_GROUPS]
    return {
        "end_month": end,
        "start_month": e.shift_month(end, -12),
        "headline_change_12m": e.window_return(data["cpi_tr"], end, 12),
        "sample": weights_sample or is_sample["cpi_tr"] or any(is_sample[n] for n in group_names),
        "weights_sample": weights_sample,
        "sources": {
            "cpi_tr": {k: SERIES["cpi_tr"][k] for k in ("label", "source", "code", "verified")} | {"sample": is_sample["cpi_tr"]},
            "groups": {
                "label": "TÜFE ana harcama grupları",
                "source": ALL_SERIES[group_names[0]]["source"],
                "codes": {n: ALL_SERIES[n]["code"] for n in group_names},
                "verified": all(ALL_SERIES[n]["verified"] for n in group_names),
                "sample": any(is_sample[n] for n in group_names),
            },
            "weights": CPI_WEIGHTS_SOURCE | {"sample": weights_sample},
        },
        "groups": groups,
    }


def build_real_rates(data: dict, is_sample: dict, end: str, months: int = 36) -> dict:
    """Trailing and ex-post real deposit/credit rates for the last `months` months, newest first."""
    cpi = data["cpi_tr"]
    cut = lambda d: {m: v for m, v in d.items() if e._month_index(m) <= e._month_index(end)}
    dep, cre = cut(data["deposit_rate"]), cut(data["credit_rate"])
    dep_tr, cre_tr = e.trailing_real_rates(dep, cpi), e.trailing_real_rates(cre, cpi)
    dep_ep, cre_ep = e.ex_post_real_rates(dep, cpi), e.ex_post_real_rates(cre, cpi)
    rows = []
    for k in range(months):
        m = e.shift_month(end, -k)
        try:
            infl = e.window_return(cpi, m, 12)
        except e.SeriesError:
            infl = None
        rows.append({
            "month": m,
            "deposit_rate": dep.get(m),
            "credit_rate": cre.get(m),
            "cpi_12m": infl,
            "deposit_real_trailing": dep_tr.get(m),
            "credit_real_trailing": cre_tr.get(m),
            "deposit_rate_12m_ago": dep.get(e.shift_month(m, -12)),
            "credit_rate_12m_ago": cre.get(e.shift_month(m, -12)),
            "deposit_real_ex_post": dep_ep.get(m),
            "credit_real_ex_post": cre_ep.get(m),
        })
    used = ("deposit_rate", "credit_rate", "cpi_tr")
    return {
        "end_month": end,
        "sample": any(is_sample[n] for n in used),
        "ex_ante": None,   # needs TCMB Market Participants Survey expectations; not added yet
        "sources": {
            n: {k: SERIES[n][k] for k in ("label", "source", "code", "verified")} | {"sample": is_sample[n]}
            for n in used
        },
        "rows": rows,
    }


def build_levels(data: dict, is_sample: dict, end: str) -> dict:
    """Monthly levels for the browser calculator, up to the common end month.

    Each series keeps only months <= end; the calculator only offers months
    where every series has a value.
    """
    end_idx = e._month_index(end)
    series = {
        name: {m: data[name][m] for m in sorted(data[name], key=e._month_index) if e._month_index(m) <= end_idx}
        for name in LEVEL_SERIES
    }
    return {
        "end_month": end,
        "sample": any(is_sample[n] for n in LEVEL_SERIES),
        "sources": {
            n: {k: SERIES[n][k] for k in ("label", "source", "code", "verified")} | {"sample": is_sample[n]}
            for n in LEVEL_SERIES
        },
        "missing": ["asgari_ucret"],   # minimum wage series not added yet
        "series": series,
    }


def write_if_changed(path: Path, result: dict) -> None:
    """Write JSON, but keep the old `generated_at` when nothing else changed.

    Otherwise the daily job would commit a new file every day even when the
    data is identical.
    """
    if path.exists():
        try:
            old = json.loads(path.read_text())
        except ValueError:
            old = None
        if old is not None:
            strip = lambda d: {k: v for k, v in d.items() if k != "generated_at"}
            if strip(old) == strip(result):
                result["generated_at"] = old.get("generated_at", result["generated_at"])
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    args = p.parse_args()
    result, levels, groups, rates = build(args.sample)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_if_changed(OUT, result)
    write_if_changed(OUT_LEVELS, levels)
    write_if_changed(OUT_GROUPS, groups)
    write_if_changed(OUT_RATES, rates)
    flag = "  [ÖRNEK VERİ]" if result["sample"] else ""
    print(f"yazıldı: {OUT.relative_to(ROOT)}, {OUT_LEVELS.relative_to(ROOT)}, {OUT_GROUPS.relative_to(ROOT)}, {OUT_RATES.relative_to(ROOT)}  bitiş ayı: {result['end_month']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
