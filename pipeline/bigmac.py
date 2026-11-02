"""The Economist's Big Mac index (data CC BY 4.0, github.com/TheEconomist/big-mac-data).

Usage:  python -m pipeline.bigmac          download the full index CSV into data/raw/
The site JSON (site/data/bigmac.json) is built by pipeline.build from that file. If the download
is missing, the last committed JSON is kept (never replaced with sample data).

Every raw valuation is recomputed with reel.engine.big_mac and compared with the published
USD_raw column; rows that disagree are counted in `mismatches` (shown on the page).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from reel import engine as e

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "bigmac_full.csv"
RAW_META = ROOT / "data" / "raw" / "bigmac_meta.json"
URL = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"
REPO = "https://github.com/TheEconomist/big-mac-data"
LICENSE = "CC BY 4.0 — The Economist"

# Comparison set shown over time (ISO3 -> Turkish name); every country appears in the latest snapshot.
TR_NAMES = {
    "TUR": "Türkiye", "USA": "ABD", "EUZ": "Euro bölgesi", "GBR": "Birleşik Krallık", "JPN": "Japonya", "CHN": "Çin",
    "BRA": "Brezilya", "MEX": "Meksika", "ARG": "Arjantin", "ZAF": "Güney Afrika", "IND": "Hindistan", "IDN": "Endonezya",
    "POL": "Polonya", "HUN": "Macaristan", "CZE": "Çekya", "ROU": "Romanya", "EGY": "Mısır", "SAU": "Suudi Arabistan",
    "ARE": "BAE", "ISR": "İsrail", "CHE": "İsviçre", "NOR": "Norveç", "SWE": "İsveç", "DNK": "Danimarka", "CAN": "Kanada",
    "AUS": "Avustralya", "NZL": "Yeni Zelanda", "KOR": "Güney Kore", "TWN": "Tayvan", "HKG": "Hong Kong", "SGP": "Singapur",
    "THA": "Tayland", "MYS": "Malezya", "PHL": "Filipinler", "VNM": "Vietnam", "PAK": "Pakistan", "CHL": "Şili",
    "COL": "Kolombiya", "PER": "Peru", "URY": "Uruguay", "CRI": "Kosta Rika", "GTM": "Guatemala", "HND": "Honduras",
    "NIC": "Nikaragua", "VEN": "Venezuela", "LKA": "Sri Lanka", "UKR": "Ukrayna", "RUS": "Rusya", "AZE": "Azerbaycan",
    "MDA": "Moldova", "JOR": "Ürdün", "KWT": "Kuveyt", "BHR": "Bahreyn", "OMN": "Umman", "QAT": "Katar", "LBN": "Lübnan",
}
# Currency redenominations: before the date, prices are in the old unit (old/new ratio).
REDENOMINATION = {"TUR": ("2005-01-01", 1_000_000)}   # 1 YTL = 1.000.000 TL (5260 sayılı Kanun)
HISTORY = ["TUR", "USA", "EUZ", "BRA", "MEX", "ZAF", "POL", "HUN", "IND", "CHN", "ARG", "GBR", "JPN"]


def _num(s: str) -> float | None:
    s = (s or "").strip()
    if not s or s.upper() == "NA":
        return None
    return float(s)


def parse(text: str) -> list[dict]:
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        lp, fx = _num(r.get("local_price", "")), _num(r.get("dollar_ex", ""))
        if lp is None or fx is None:
            continue
        redo = REDENOMINATION.get(r["iso_a3"])
        if redo and r["date"] < redo[0]:
            lp, fx = lp / redo[1], fx / redo[1]
        rows.append({"date": r["date"], "iso": r["iso_a3"], "name": r["name"], "currency": r["currency_code"],
                     "local_price": lp, "fx": fx, "usd_raw": _num(r.get("USD_raw", "")), "usd_adj": _num(r.get("USD_adjusted", ""))})
    return rows


def build_bigmac(text: str, retrieved_at: str | None = None) -> dict:
    rows = parse(text)
    us = {r["date"]: r["local_price"] for r in rows if r["iso"] == "USA"}
    out_rows, mismatches = [], 0
    for r in rows:
        if r["date"] not in us:
            continue
        b = e.big_mac(local_price=r["local_price"], fx=r["fx"], us_price=us[r["date"]])
        if r["usd_raw"] is not None and abs(b["valuation"] - r["usd_raw"]) > 5e-4:
            mismatches += 1
        out_rows.append({**r, **b, "us_price": us[r["date"]]})
    dates = sorted({r["date"] for r in out_rows})
    latest = dates[-1]
    r4 = lambda v: None if v is None else round(v, 5)
    snapshot = sorted(({"iso": r["iso"], "name": TR_NAMES.get(r["iso"], r["name"]), "currency": r["currency"],
                        "local_price": r["local_price"], "fx": r["fx"], "dollar_price": r4(r["dollar_price"]),
                        "valuation": r4(r["valuation"]), "valuation_adj": r4(r["usd_adj"])}
                       for r in out_rows if r["date"] == latest), key=lambda x: -x["dollar_price"])
    history = {}
    for iso in HISTORY:
        pts = [r for r in out_rows if r["iso"] == iso]
        if pts:
            history[iso] = {"name": TR_NAMES.get(iso, pts[0]["name"]), "currency": pts[0]["currency"],
                            "points": [[r["date"], r["local_price"], r["fx"], r4(r["dollar_price"]), r4(r["valuation"]), r4(r["usd_adj"])] for r in pts]}
    return {"source": "The Economist, Big Mac endeksi", "url": REPO, "license": LICENSE, "retrieved_at": retrieved_at,
            "latest_date": latest, "first_date": dates[0], "dates": len(dates), "mismatches": mismatches,
            "columns": ["date", "local_price", "fx", "dollar_price", "valuation", "valuation_adj"],
            "snapshot": snapshot, "history": history, "sample": False}


def load_raw() -> tuple[str, str | None] | None:
    if not RAW.exists():
        return None
    meta = json.loads(RAW_META.read_text()) if RAW_META.exists() else {}
    return RAW.read_text(encoding="utf-8"), meta.get("retrieved_at")


def main() -> int:
    import requests
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    text = resp.text
    rows = parse(text)                       # validate before saving
    if not any(r["iso"] == "TUR" for r in rows) or not any(r["iso"] == "USA" for r in rows):
        print("Big Mac verisi beklenen biçimde değil; kaydedilmedi.", file=sys.stderr)
        return 1
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(text, encoding="utf-8")
    RAW_META.write_text(json.dumps({"url": URL, "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "rows": len(rows)}))
    print(f"Big Mac: {len(rows)} satır, son tarih {max(r['date'] for r in rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
