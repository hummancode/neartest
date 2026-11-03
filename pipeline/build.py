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

import csv

from pipeline import manual, sample
from pipeline.series import (ALL_SERIES, ASSETS, CITIES, CPI_GROUPS, CPI_WEIGHTS_SOURCE, MACRO_SERIES,
                             OPTIONAL_SERIES, SERIES)
from reel import engine as e

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "site" / "data" / "reel_tablo.json"
OUT_LEVELS = ROOT / "site" / "data" / "seviyeler.json"
OUT_GROUPS = ROOT / "site" / "data" / "tufe_gruplari.json"
OUT_RATES = ROOT / "site" / "data" / "reel_faiz.json"
OUT_STATUS = ROOT / "site" / "data" / "durum.json"
OUT_PATHS = ROOT / "site" / "data" / "seriler.json"
OUT_PRICES = ROOT / "site" / "data" / "fiyatlar.json"
OUT_HOUSING = ROOT / "site" / "data" / "konut.json"
OUT_MACRO = ROOT / "site" / "data" / "makro.json"
OUT_STOCKS = ROOT / "site" / "data" / "borsa.json"
OUT_EVENTS = ROOT / "site" / "data" / "olaylar.json"
OUT_COUNTRIES = ROOT / "site" / "data" / "ulkeler.json"
OUT_PROVINCES = ROOT / "site" / "data" / "iller.json"
OUT_TRADE = ROOT / "site" / "data" / "dis_ticaret.json"
OUT_DISTRICTS = ROOT / "site" / "data" / "ilceler.json"
GEO_DISTRICTS = ROOT / "site" / "data" / "tr_ilceler.json"

# Instruments of the "X priced in Y" chart tool: (id, label, group, source series).
INSTRUMENTS = [
    ("tl", "TL (nominal)", "Ölçü", None),
    ("cpi", "TÜFE sepeti (reel TL)", "Ölçü", "cpi_tr"),
    ("usd", "Dolar", "Döviz", "usdtry"),
    ("eur", "Euro", "Döviz", "eurtry"),
    ("gold", "Gram altın", "Emtia", "gold_gram_tl"),
    ("bist100", "BIST 100", "Borsa", "bist100"),
    ("sp500", "S&P 500 (TL)", "Borsa", "sp500_usd"),
    ("deposit", "TL mevduat (faiz getirisi)", "Faiz", "deposit_rate"),
    ("car", "Otomobil (TÜFE alt endeksi)", "Tüketim", "car_cpi"),
    ("car_new", "0 km otomobil (bayi liste fiyatı)", "Tüketim", "car_new"),
    ("rent", "Kira (TÜFE alt endeksi)", "Tüketim", "rent_cpi"),
    ("house_ist", "Konut — İstanbul", "Konut", "house_ist"),
    ("house_ank", "Konut — Ankara", "Konut", "house_ank"),
    ("house_izm", "Konut — İzmir", "Konut", "house_izm"),
    ("house_tr", "Konut — Türkiye", "Konut", "house_tr"),
    *[(f"betam_sale_{k}", f"Konut (BETAM satılık) — {n}", "Konut", f"betam_sale_{k}") for k, n in
      (("ist", "İstanbul"), ("ank", "Ankara"), ("izm", "İzmir"), ("tr", "Türkiye"))],
    *[(f"betam_rent_{k}", f"Kira (BETAM kiralık) — {n}", "Konut", f"betam_rent_{k}") for k, n in
      (("ist", "İstanbul"), ("ank", "Ankara"), ("izm", "İzmir"), ("tr", "Türkiye"))],
    ("min_wage", "Net asgari ücret", "Gelir", "min_wage_net"),
]
WEIGHTS_CSV = ROOT / "data" / "manual" / "tufe_agirliklari.csv"

# Series the in-browser "nominal illusion" calculator needs, as raw monthly levels.
LEVEL_SERIES = ("cpi_tr", "usdtry", "gold_gram_tl")


# Effective metadata per series (series.py, overridden by data/manual/<name>.meta.json)
# and where each series came from: "evds" (data/raw), "manual" (data/manual), "sample".
META: dict[str, dict] = {k: dict(v) for k, v in (ALL_SERIES | OPTIONAL_SERIES).items()}
ORIGIN: dict[str, str] = {}

ORIGIN_LABEL = {"evds": "TCMB EVDS API", "manual": "Elle yüklendi", "sample": "ÖRNEK (sentetik)", "missing": "Yok"}


def _real_series(name: str) -> tuple[dict, str, dict] | None:
    """Real data for `name` from data/raw (API fetch) or data/manual (CSV), scaled."""
    scale = META[name].get("scale", 1.0)
    path = RAW / f"{name}.json"
    if path.exists():
        raw = json.loads(path.read_text())
        return {m: v * scale for m, v in raw.items()}, "evds", {}
    loaded = manual.load(name)
    if loaded:
        series, meta = loaded
        return {m: v * scale for m, v in series.items()}, "manual", meta
    if name == "car_new":
        basket = manual.MANUAL / "car_new_basket.csv"
        if basket.exists():
            prices = manual.parse_basket_csv(basket.read_text(encoding="utf-8-sig"))
            meta_path = manual.MANUAL / "car_new_basket.meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            return e.jevons_chain_index(prices), "manual", meta
    return None


def load_series(allow_sample: bool) -> tuple[dict, dict]:
    """Return (series_by_name, is_sample_by_name). Optional series appear only if real."""
    synthetic = sample.build_sample() if allow_sample else {}
    data, is_sample = {}, {}
    for name in ALL_SERIES | OPTIONAL_SERIES:
        real = _real_series(name)
        if real:
            data[name], ORIGIN[name], override = real
            META[name].update({k: override[k] for k in ("source", "code", "verified", "label") if k in override})
            is_sample[name] = False
        elif name in OPTIONAL_SERIES:
            ORIGIN[name] = "missing"
        elif allow_sample:
            data[name] = synthetic[name]
            is_sample[name] = True
            ORIGIN[name] = "sample"
        else:
            raise SystemExit(f"Eksik seri: {name} (data/raw/{name}.json veya data/manual/{name}.csv). "
                             "Örnek veri için --sample kullan.")
    return data, is_sample


def src(name: str, is_sample: dict) -> dict:
    """Source block shown on the site for one series."""
    m = META[name]
    return {"label": m["label"], "source": m["source"], "code": m["code"], "verified": bool(m["verified"]),
            "sample": bool(is_sample.get(name, False))}


def asset_tl_series(asset: dict, data: dict) -> dict[str, float]:
    raw = data[asset["series"]]
    if asset["kind"] == "rate":
        return e.deposit_index(raw)
    if asset["kind"] == "usd_level":
        return e.to_tl(raw, data["usdtry"])
    return raw


def build(allow_sample: bool) -> tuple[dict, ...]:
    data, is_sample = load_series(allow_sample)
    cpi, usdtry = data["cpi_tr"], data["usdtry"]
    # Common end month: the latest month every input has.
    # Macro series (quarterly/annual, published with lags) don't hold back the market end month.
    end = min(e.last_month(s) for n, s in data.items() if n not in OPTIONAL_SERIES and n not in MACRO_SERIES)
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
            name: src(name, is_sample) | {"last_month": e.last_month(data[name])}
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
    status = build_status(data, weights_sample, end)
    status["generated_at"] = tablo["generated_at"]
    paths = build_paths(data, is_sample, end)
    paths["generated_at"] = tablo["generated_at"]
    stocks = manual.load_stocks()
    prices = build_prices(data, is_sample, end, stocks)
    stocks_out = build_stocks(data, is_sample, end, stocks)
    housing = build_housing(data, is_sample, end)
    macro = build_macro(data, is_sample, end)
    events = build_events(data, is_sample)
    countries = build_countries(allow_sample) or {"sample": True, "indicators": [], "countries": [], "source": ""}
    from pipeline.provinces import build_provinces
    geo_districts = json.loads(GEO_DISTRICTS.read_text(encoding="utf-8")) if GEO_DISTRICTS.exists() else None
    provinces = build_provinces(data["usdtry"], allow_sample, gold_gram_tl=data["gold_gram_tl"].get(end),
                                gold_sample=is_sample.get("gold_gram_tl", True), geo_districts=geo_districts)
    from pipeline.districts import PATH as DISTRICT_CSV, build_districts
    prov_hist = {x["plaka"]: dict(x["history"]["population"]["points"]) for x in provinces["provinces"] if "population" in x["history"]}
    districts = build_districts(prov_hist, provinces["population_history_sample"], allow_sample,
                                DISTRICT_CSV.read_text(encoding="utf-8-sig") if DISTRICT_CSV.exists() else None, geo_districts)
    from pipeline.trade import build_trade
    trade = build_trade(allow_sample)
    for d in (prices, housing, macro, stocks_out, events, countries, provinces, trade, districts):
        d["generated_at"] = tablo["generated_at"]
    return tablo, levels, groups, rates, status, paths, prices, housing, macro, stocks_out, events, countries, provinces, trade, districts


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
            "cpi_tr": src("cpi_tr", is_sample),
            "groups": {
                "label": "TÜFE ana harcama grupları",
                "source": META[group_names[0]]["source"],
                "codes": {n: META[n]["code"] for n in group_names},
                "verified": all(META[n]["verified"] for n in group_names),
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
            n: src(n, is_sample) for n in used
        },
        "rows": rows,
    }


def build_paths(data: dict, is_sample: dict, end: str) -> dict:
    """Monthly index paths (100 at window start) per asset and window, for detail charts."""
    cpi, usdtry = data["cpi_tr"], data["usdtry"]
    assets = {}
    for asset in ASSETS:
        tl = asset_tl_series(asset, data)
        windows = {}
        for years in (1, 3, 5, 10):
            try:
                p = e.index_paths(tl, cpi, usdtry, end, years)
            except e.SeriesError:
                continue
            windows[str(years)] = {
                "months": p["months"],
                **{k: [round(v, 4) for v in p[k]] for k in ("nominal", "real", "usd")},
            }
        assets[asset["id"]] = {
            "label": asset["label"],
            "kind": asset["kind"],
            "series": asset["series"],
            "sample": any(is_sample[s] for s in (asset["series"], "cpi_tr", "usdtry")),
            "windows": windows,
        }
    return {"end_month": end, "sample": any(a["sample"] for a in assets.values()), "assets": assets}


def _instrument_tl(source: str | None, data: dict, end: str) -> dict[str, float] | None:
    """TL price level (or index) of one chart instrument, cut at `end`."""
    end_idx = e._month_index(end)
    if source is None:  # plain TL: a constant, so "X in TL" is X's nominal price
        months = sorted(data["cpi_tr"], key=e._month_index)
        out = {m: 1.0 for m in months}
    elif source not in data:
        return None
    elif source == "deposit_rate":
        out = e.deposit_index(data[source])
    elif source == "sp500_usd":
        out = e.to_tl(data[source], data["usdtry"])
    elif source == "min_wage_net":
        out = forward_fill(data[source], end)
    else:
        out = data[source]
    return {m: v for m, v in out.items() if e._month_index(m) <= end_idx}


def build_prices(data: dict, is_sample: dict, end: str, stocks: dict | None = None) -> dict:
    """Monthly TL levels of every chart instrument (contiguous runs: start month + values)."""
    instruments, series = [], {}
    for iid, label, group, source in INSTRUMENTS:
        tl = _instrument_tl(source, data, end)
        if not tl:
            continue
        months = sorted(tl, key=e._month_index)
        # Keep the longest contiguous run that ends at the last month.
        run = [months[-1]]
        for m in reversed(months[:-1]):
            if e.shift_month(m, 1) != run[0]:
                break
            run.insert(0, m)
        used = [] if source is None else [source] + (["usdtry"] if source == "sp500_usd" else [])
        instruments.append({
            "id": iid, "label": label, "group": group,
            "sample": any(is_sample.get(u, False) for u in used),
            "sources": [src(u, is_sample) for u in used],
        })
        series[iid] = {"start": run[0], "values": [round(tl[m], 8) for m in run]}
    for ticker, (prices_tl, meta) in (stocks or {}).items():
        tl = {m: v for m, v in prices_tl.items() if e._month_index(m) <= e._month_index(end)}
        if not tl or max(tl, key=e._month_index) != end:
            continue  # stale file: must reach the common end month to sit on the same footing
        months = sorted(tl, key=e._month_index)
        run = [months[-1]]
        for m in reversed(months[:-1]):
            if e.shift_month(m, 1) != run[0]:
                break
            run.insert(0, m)
        instruments.append({
            "id": f"stk_{ticker}", "label": f"{ticker}" + (f" — {meta['name']}" if meta.get("name") else ""),
            "group": "Hisse", "sample": False,
            "sources": [{"label": ticker, "source": meta.get("source", "Elle yüklendi (data/manual/stocks)"),
                         "code": ticker, "verified": bool(meta.get("verified", False)), "sample": False}],
        })
        series[f"stk_{ticker}"] = {"start": run[0], "values": [round(tl[m], 8) for m in run]}
    return {
        "end_month": end,
        "sample": any(i["sample"] for i in instruments),
        "instruments": instruments,
        "series": series,
    }


def build_stocks(data: dict, is_sample: dict, end: str, stocks: dict) -> dict:
    """BIST 100 and manually loaded stocks: nominal / real / USD / gold returns."""
    rows = [{
        "id": "bist100", "ticker": "XU100", "label": "BIST 100 endeksi",
        "sample": any(is_sample.get(s, False) for s in ("bist100", "cpi_tr", "usdtry", "gold_gram_tl")),
        "last_month": e.last_month(data["bist100"]),
        "windows": _house_windows(data["bist100"], data, end),
        "source": src("bist100", is_sample),
    }]
    for ticker, (prices_tl, meta) in stocks.items():
        rows.append({
            "id": f"stk_{ticker}", "ticker": ticker, "label": meta.get("name", ticker),
            "sample": any(is_sample.get(s, False) for s in ("cpi_tr", "usdtry", "gold_gram_tl")),
            "last_month": e.last_month(prices_tl),
            "windows": _house_windows(prices_tl, data, end),
            "source": {"label": ticker, "source": meta.get("source", "Elle yüklendi (data/manual/stocks)"),
                       "code": ticker, "verified": bool(meta.get("verified", False)), "sample": False},
        })
    return {"end_month": end, "sample": any(r["sample"] for r in rows), "stock_count": len(stocks), "rows": rows}


def _house_windows(house: dict, data: dict, end: str) -> list[dict]:
    cpi, fx, gold = data["cpi_tr"], data["usdtry"], data["gold_gram_tl"]
    out = []
    for w in e.asset_windows(house, cpi, fx, end):
        try:
            g = e.currency_return(w.nominal_tl, e.window_return(gold, end, 12 * w.years))
        except e.SeriesError:
            g = None
        out.append(w.__dict__ | {"gold": g, "gold_annual": None if g is None else e.annualize(g, w.years)})
    return out


def build_housing(data: dict, is_sample: dict, end: str) -> dict:
    """House price returns per city (nominal / real / USD / gold), per source, and reference rates.

    Sources: TCMB KFE (always; sample until verified) and BETAM sale index (only if entered).
    """
    def change_12m(name):
        if name not in data:
            return None
        try:
            return e.window_return(data[name], end, 12)
        except e.SeriesError:
            return None

    base = ("cpi_tr", "usdtry", "gold_gram_tl")
    cities = []
    for c in CITIES:
        sources = {"kfe": {
            "label": "TCMB Konut Fiyat Endeksi",
            "series": c["series"],
            "sample": any(is_sample.get(s, False) for s in (c["series"], *base)),
            "windows": _house_windows(data[c["series"]], data, end),
        }}
        if c["betam_sale"] in data:
            sources["betam"] = {
                "label": "BETAM satılık konut endeksi",
                "series": c["betam_sale"],
                "sample": any(is_sample.get(s, False) for s in base),
                "windows": _house_windows(data[c["betam_sale"]], data, end),
            }
        cities.append({
            "id": c["id"], "label": c["label"], "sources": sources,
            "rent_12m_betam": change_12m(c["betam_rent"]),
            "house_12m": {k: change_12m(v["series"]) for k, v in sources.items()},
        })

    used = ["cpi_tr", "usdtry", "gold_gram_tl", "rent_cpi", "deposit_rate", "credit_rate"]
    used += [c["series"] for c in CITIES]
    used += [n for c in CITIES for n in (c["betam_sale"], c["betam_rent"]) if n in data]
    return {
        "end_month": end,
        "sample": any(is_sample.get(n, False) for n in used),
        "cities": cities,
        "reference": {
            "cpi_12m": change_12m("cpi_tr"),
            "rent_12m": change_12m("rent_cpi"),
            "deposit_rate": data["deposit_rate"].get(end),
            "credit_rate": data["credit_rate"].get(end),
            "sample": any(is_sample[n] for n in ("cpi_tr", "rent_cpi", "deposit_rate", "credit_rate")),
        },
        "sources": {n: src(n, is_sample) for n in used},
    }


def latest_and_change(points: list[list], kind: str) -> dict:
    """Latest point and its change vs. the same month a year earlier.

    rate -> difference in points; level -> % change (as a fraction). None if no
    point exists exactly 12 months earlier.
    """
    if not points:
        return {"latest": None, "prev_year": None, "change_12m": None}
    m, v = points[-1]
    prev = dict((pm, pv) for pm, pv in points).get(e.shift_month(m, -12))
    if prev is None:
        change = None
    elif kind == "rate":
        change = v - prev
    else:
        change = v / prev - 1.0 if prev > 0 else None
    return {"latest": [m, v], "prev_year": None if prev is None else [e.shift_month(m, -12), prev], "change_12m": change}


def build_macro(data: dict, is_sample: dict, end: str) -> dict:
    """Indicators for the macro dashboard and co-movement tool (raw points, display units).

    Includes the macro series plus a few market-derived indicators on the same footing.
    """
    def pts(series: dict, cut: str | None = end) -> list[list]:
        months = sorted(series, key=e._month_index)
        if cut:
            months = [m for m in months if e._month_index(m) <= e._month_index(cut)]
        return [[m, round(series[m], 6)] for m in months]

    indicators = []
    for name, m in MACRO_SERIES.items():
        if name not in data:
            continue
        indicators.append({
            "id": name, "label": m["label"], "unit": m["unit"], "kind": m["kind"], "freq": m["freq"],
            "group": m["group"], "sample": is_sample.get(name, False), "sources": [src(name, is_sample)],
            "points": pts(data[name], cut=None),
        })
        indicators[-1] |= latest_and_change(indicators[-1]["points"], m["kind"])

    cpi, fx = data["cpi_tr"], data["usdtry"]
    inflation = {}
    for mth in cpi:
        try:
            inflation[mth] = 100 * e.window_return(cpi, mth, 12)
        except e.SeriesError:
            pass
    real_dep = {k: 100 * v for k, v in e.trailing_real_rates(data["deposit_rate"], cpi).items()}
    bist_usd = {k: data["bist100"][k] / fx[k] for k in data["bist100"] if k in fx}
    gold_usd = {k: data["gold_gram_tl"][k] / fx[k] for k in data["gold_gram_tl"] if k in fx}
    derived = [
        ("inflation", "Yıllık TÜFE enflasyonu", "%", "rate", "Fiyatlar", inflation, ["cpi_tr"]),
        ("real_deposit", "Reel mevduat faizi (son 12 ay TÜFE'ye göre)", "%", "rate", "Para politikası", real_dep, ["deposit_rate", "cpi_tr"]),
        ("usdtry", "USD/TRY", "TL", "level", "Piyasalar", fx, ["usdtry"]),
        ("bist100_usd", "BIST 100 (dolar bazında)", "$", "level", "Piyasalar", bist_usd, ["bist100", "usdtry"]),
        ("gold_usd", "Gram altın (dolar)", "$", "level", "Piyasalar", gold_usd, ["gold_gram_tl", "usdtry"]),
    ]
    for iid, label, unit, kind, group, series, used in derived:
        indicators.append({
            "id": iid, "label": label, "unit": unit, "kind": kind, "freq": "M", "group": group,
            "sample": any(is_sample.get(u, False) for u in used), "sources": [src(u, is_sample) for u in used],
            "points": pts(series),
        })
        indicators[-1] |= latest_and_change(indicators[-1]["points"], kind)
    return {"end_month": end, "sample": any(i["sample"] for i in indicators), "indicators": indicators}


def build_events(data: dict, is_sample: dict, threshold: float = 1.0) -> dict:
    """Event months for the event-study page.

    Derived: months where the policy rate moved by >= `threshold` points (from the
    policy_rate series itself, so they are only as real as that series).
    Manual: data/manual/events.csv (date; type; title) — official dated facts only.
    """
    events = []
    if "policy_rate" in data:
        for ev in e.derive_rate_events(data["policy_rate"], threshold):
            events.append({"month": ev["month"], "type": ev["type"], "change": ev["change"],
                           "title": f"Politika faizi {'artışı' if ev['type'] == 'hike' else 'indirimi'}",
                           "origin": "derived"})
    path = manual.MANUAL / "events.csv"
    if path.exists():
        for ev in manual.parse_events_csv(path.read_text(encoding="utf-8-sig")):
            events.append(ev | {"change": None, "origin": "manual"})
    events.sort(key=lambda x: e._month_index(x["month"]))
    return {
        "threshold": threshold,
        "sample": is_sample.get("policy_rate", False),
        "source": src("policy_rate", is_sample) if "policy_rate" in data else None,
        "events": events,
    }


def build_countries(allow_sample: bool) -> dict | None:
    """World Bank indicators per country (data/raw/wb_*.json from pipeline.worldbank, or sample)."""
    from pipeline import worldbank as wb

    meta_path = RAW / "wb_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    synthetic = sample.sample_worldbank() if allow_sample else {}
    indicators = []
    for key, (code, _expected, label, unit, kind) in wb.INDICATORS.items():
        path = RAW / f"wb_{key}.json"
        if path.exists():
            data, is_sample = json.loads(path.read_text()), False
        elif allow_sample:
            data, is_sample = synthetic[key], True
        else:
            continue
        latest = {}
        for iso, years in data.items():
            if years:
                y = max(years)
                latest[iso] = [y, years[y]]
        indicators.append({
            "id": key, "label": label, "unit": unit, "kind": kind, "code": code,
            "verified": bool(meta.get(key, {}).get("verified")), "sample": is_sample,
            "series": {iso: [[y, v] for y, v in sorted(years.items())] for iso, years in data.items()},
            "latest": latest,
        })
    if not indicators:
        return None
    return {
        "source": "Dünya Bankası, World Development Indicators (CC BY 4.0)",
        "countries": [{"iso": iso, "name": name} for iso, name in wb.COUNTRIES],
        "sample": any(i["sample"] for i in indicators),
        "indicators": indicators,
    }


USED_BY = {
    "cpi_tr": "Tüm reel hesaplar", "usdtry": "USD getirisi, nominal illüzyon", "eurtry": "Reel Tablo",
    "deposit_rate": "Reel Tablo, reel faiz", "credit_rate": "Reel Tablo, reel faiz",
    "gold_gram_tl": "Reel Tablo, nominal illüzyon", "bist100": "Reel Tablo", "sp500_usd": "Reel Tablo",
    "min_wage_net": "Nominal illüzyon, grafik",
    "car_cpi": "Grafik", "rent_cpi": "Konut, grafik", "car_new": "Grafik",
    **{k: "Makro pano, ilişkiler, Türkiye profili" for k in MACRO_SERIES},
    "house_tr": "Konut, grafik", "house_ist": "Konut, grafik", "house_ank": "Konut, grafik", "house_izm": "Konut, grafik",
}


def build_status(data: dict, weights_sample: bool, end: str) -> dict:
    """Where every series comes from, for the /veri page."""
    rows = []
    for name in ALL_SERIES | OPTIONAL_SERIES:
        m, origin = META[name], ORIGIN.get(name, "missing")
        used_by = USED_BY.get(name) or ("Konut, grafik" if name.startswith("betam_") else "Kişisel enflasyon")
        s = data.get(name, {})
        months = sorted(s, key=e._month_index)
        rows.append({
            "name": name,
            "label": m["label"],
            "source": m["source"],
            "code": m["code"],
            "verified": bool(m["verified"]),
            "origin": origin,
            "origin_label": ORIGIN_LABEL[origin],
            "first_month": months[0] if months else None,
            "last_month": months[-1] if months else None,
            "months": len(months),
            "used_by": used_by,
        })
    counts = {k: sum(r["origin"] == k for r in rows) for k in ORIGIN_LABEL}
    return {
        "end_month": end,
        "sample": counts["sample"] > 0 or weights_sample,
        "counts": counts,
        "weights": CPI_WEIGHTS_SOURCE | {"sample": weights_sample},
        "rows": rows,
    }


def build_levels(data: dict, is_sample: dict, end: str) -> dict:
    """Monthly levels for the browser calculator, up to the common end month.

    Each series keeps only months <= end; the calculator only offers months
    where every series has a value.
    """
    end_idx = e._month_index(end)
    names = [*LEVEL_SERIES]
    series = {
        name: {m: data[name][m] for m in sorted(data[name], key=e._month_index) if e._month_index(m) <= end_idx}
        for name in names
    }
    missing = []
    if "min_wage_net" in data:
        # Listed only in the months it changed; it applies until the next change.
        series["min_wage_net"] = forward_fill(data["min_wage_net"], end)
        names.append("min_wage_net")
    else:
        missing.append("min_wage_net")
    return {
        "end_month": end,
        "sample": any(is_sample.get(n, False) for n in names),
        "sources": {n: src(n, is_sample) for n in names},
        "missing": missing,
        "series": series,
    }


def forward_fill(series: dict[str, float], end: str) -> dict[str, float]:
    """Monthly series from the first listed month to `end`, carrying the last value forward."""
    months = sorted(series, key=e._month_index)
    if not months or e._month_index(months[0]) > e._month_index(end):
        return {}
    out, m, value = {}, months[0], series[months[0]]
    while e._month_index(m) <= e._month_index(end):
        value = series.get(m, value)
        out[m] = value
        m = e.shift_month(m, 1)
    return out


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


OUT_BIGMAC = ROOT / "site" / "data" / "bigmac.json"


def write_bigmac() -> str:
    """Big Mac JSON from the downloaded CSV; keeps the committed file when there is no download."""
    from pipeline.bigmac import build_bigmac, load_raw
    raw = load_raw()
    if raw is None:
        return "Big Mac: indirme yok, mevcut dosya korundu" if OUT_BIGMAC.exists() else "Big Mac: veri yok"
    out = build_bigmac(*raw)
    out["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_if_changed(OUT_BIGMAC, out)
    return f"Big Mac: {out['latest_date']} ({out['mismatches']} uyuşmazlık)"


OUT_LONGRUN = ROOT / "site" / "data" / "uzun_donem.json"


def write_longrun() -> str:
    from pipeline.longrun import build_longrun, load_raw
    raw = load_raw()
    if raw is None:
        return "Uzun dönem: indirme yok, mevcut dosya korundu" if OUT_LONGRUN.exists() else "Uzun dönem: veri yok"
    out = build_longrun(*raw)
    out["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_if_changed(OUT_LONGRUN, out)
    return f"Uzun dönem: {out['summary']['first']}–{out['summary']['last']}"


OUT_HOUSE_WORLD = ROOT / "site" / "data" / "konut_dunya.json"


def write_houseprices() -> str:
    from pipeline.houseprices import build_houseprices, load_raw
    raw = load_raw()
    if raw is None:
        return "Konut (BIS): indirme yok, mevcut dosya korundu" if OUT_HOUSE_WORLD.exists() else "Konut (BIS): veri yok"
    out = build_houseprices(*raw)
    out["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_if_changed(OUT_HOUSE_WORLD, out)
    tr = next((c for c in out["countries"] if c["code"] == "TR"), None)
    return f"Konut (BIS): {len(out['countries'])} ülke/bölge, Türkiye son {tr['last'] if tr else '—'}"


OUT_COMMODITIES = ROOT / "site" / "data" / "emtia.json"


def write_commodities() -> str:
    from pipeline.commodities import build_commodities, load_raw
    raw = load_raw()
    if raw is None:
        return "Emtia: indirme yok, mevcut dosya korundu" if OUT_COMMODITIES.exists() else "Emtia: veri yok"
    out = build_commodities(*raw)
    out["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_if_changed(OUT_COMMODITIES, out)
    return "Emtia: " + ", ".join(f"{k} {v['last']}" for k, v in out["series"].items())


OUT_NABIZ = ROOT / "site" / "data" / "nabiz.json"


def write_nabiz(macro: dict, countries: dict) -> str:
    """Neutral indicator board from the macro/country outputs plus the real-data JSON files already on disk."""
    from pipeline.nabiz import build_nabiz, real_extras
    load = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    extras = real_extras(load(OUT_BIGMAC), load(OUT_HOUSE_WORLD), load(OUT_COMMODITIES))
    out = build_nabiz(macro, countries, extras)
    out["generated_at"] = macro.get("generated_at") or datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_if_changed(OUT_NABIZ, out)
    return f"Nabız: {len(out['cards'])} gösterge"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    args = p.parse_args()
    result, levels, groups, rates, status, paths, prices, housing, macro, stocks_out, events, countries, provinces, trade, districts = build(args.sample)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_if_changed(OUT, result)
    write_if_changed(OUT_LEVELS, levels)
    write_if_changed(OUT_GROUPS, groups)
    write_if_changed(OUT_RATES, rates)
    write_if_changed(OUT_STATUS, status)
    write_if_changed(OUT_PATHS, paths)
    write_if_changed(OUT_PRICES, prices)
    write_if_changed(OUT_HOUSING, housing)
    write_if_changed(OUT_MACRO, macro)
    write_if_changed(OUT_STOCKS, stocks_out)
    write_if_changed(OUT_EVENTS, events)
    write_if_changed(OUT_COUNTRIES, countries)
    write_if_changed(OUT_PROVINCES, provinces)
    write_if_changed(OUT_TRADE, trade)
    write_if_changed(OUT_DISTRICTS, districts)
    print(write_bigmac())
    print(write_longrun())
    print(write_houseprices())
    print(write_commodities())
    print(write_nabiz(macro, countries))
    flag = "  [ÖRNEK VERİ]" if result["sample"] else ""
    print(f"yazıldı: site/data/*.json (15 dosya)  bitiş ayı: {result['end_month']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
