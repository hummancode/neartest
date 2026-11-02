"""Residential property prices across countries: BIS selected series (2010 = 100), via the
`datasets/house-prices-global` repository on GitHub (a mirror of the BIS SPP dataflow).

Usage:  python -m pipeline.houseprices     download real + nominal index CSVs into data/raw/
Terms: BIS Terms of Permitted Use of Statistics — attribution required:
"National sources, BIS Residential Property Price database". For Türkiye the national source is TCMB (KFE).
Real = nominal deflated by the consumer price index (done by BIS, not by us).
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
RAW = ROOT / "data" / "raw"
BASE = "https://raw.githubusercontent.com/datasets/house-prices-global/main/data/"
FILES = {"real": "real_index.csv", "nominal": "nominal_index.csv"}
ATTRIBUTION = "National sources, BIS Residential Property Price database"
TR_NAMES = {
    "TR": "Türkiye", "US": "ABD", "GB": "Birleşik Krallık", "DE": "Almanya", "FR": "Fransa", "IT": "İtalya", "ES": "İspanya",
    "PT": "Portekiz", "NL": "Hollanda", "BE": "Belçika", "AT": "Avusturya", "CH": "İsviçre", "IE": "İrlanda", "DK": "Danimarka",
    "SE": "İsveç", "NO": "Norveç", "FI": "Finlandiya", "IS": "İzlanda", "GR": "Yunanistan", "CY": "Kıbrıs (GKRY)", "MT": "Malta",
    "LU": "Lüksemburg", "PL": "Polonya", "CZ": "Çekya", "SK": "Slovakya", "HU": "Macaristan", "RO": "Romanya", "BG": "Bulgaristan",
    "HR": "Hırvatistan", "SI": "Slovenya", "RS": "Sırbistan", "MK": "Kuzey Makedonya", "EE": "Estonya", "LV": "Letonya", "LT": "Litvanya",
    "RU": "Rusya", "IL": "İsrail", "MA": "Fas", "ZA": "Güney Afrika", "JP": "Japonya", "KR": "Güney Kore", "CN": "Çin", "HK": "Hong Kong",
    "SG": "Singapur", "MY": "Malezya", "TH": "Tayland", "ID": "Endonezya", "PH": "Filipinler", "IN": "Hindistan", "AU": "Avustralya",
    "NZ": "Yeni Zelanda", "CA": "Kanada", "MX": "Meksika", "BR": "Brezilya", "CL": "Şili", "CO": "Kolombiya", "PE": "Peru",
    "XM": "Euro bölgesi", "XW": "Dünya (BIS ortalaması)", "4T": "Gelişmekte olan ekonomiler", "5R": "Gelişmiş ekonomiler",
}
AGGREGATES = {"XM", "XW", "4T", "5R"}


def _quarter(d: str) -> int:
    y, m = int(d[:4]), int(d[5:7])
    return y * 4 + (m - 1) // 3


def parse(text: str) -> dict[str, list[tuple[str, float]]]:
    out: dict[str, list[tuple[str, float]]] = {}
    for r in csv.DictReader(io.StringIO(text)):
        v = (r.get("price") or "").strip()
        if v:
            out.setdefault(r["country_code"], []).append((r["date"], float(v)))
    for k in out:
        out[k].sort()
    return out


def contiguous_tail(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Last run of consecutive quarters (so 'n quarters back' means n quarters of time)."""
    if not pts:
        return pts
    i = len(pts) - 1
    while i > 0 and _quarter(pts[i][0]) - _quarter(pts[i - 1][0]) == 1:
        i -= 1
    return pts[i:]


def build_houseprices(real_text: str, nominal_text: str, retrieved_at: str | None = None) -> dict:
    real, nominal = parse(real_text), parse(nominal_text)
    countries = []
    for code, pts in real.items():
        pts = contiguous_tail(pts)
        vals = [v for _, v in pts]
        if len(vals) < 5:
            continue
        row = {"code": code, "name": TR_NAMES.get(code, code), "aggregate": code in AGGREGATES,
               "first": pts[0][0][:7], "last": pts[-1][0][:7], "latest": round(vals[-1], 2),
               "since2010_pct": round(vals[-1] - 100.0, 2)}   # index is 2010 = 100
        for n, key in ((1, "real_1y"), (5, "real_5y"), (10, "real_10y")):
            c = e.change_over(vals, 4 * n, 4)
            if c:
                row[key] = round(c["change_pct"], 2)
                row[key + "_annual"] = round(c["annual_pct"], 3)
        dd = e.drawdown(vals)
        row["peak"] = pts[dd["peak_index"]][0][:7]
        row["drawdown_pct"] = round(dd["drawdown_pct"], 2)
        npts = contiguous_tail(nominal.get(code, []))
        if npts:
            row["nominal_latest"] = round(npts[-1][1], 2)
            c = e.change_over([v for _, v in npts], 20, 4)
            if c:
                row["nominal_5y"] = round(c["change_pct"], 2)
        row["series"] = [[d[:7], round(v, 2)] for d, v in pts if d >= "1990"]
        row["nominal_series"] = [[d[:7], round(v, 2)] for d, v in npts if d >= "1990"]
        countries.append(row)
    countries.sort(key=lambda r: r["name"])
    return {"source": "BIS, seçilmiş konut fiyatı endeksleri (2010 = 100)", "attribution": ATTRIBUTION,
            "mirror": "github.com/datasets/house-prices-global", "terms": "https://www.bis.org/terms_statistics.htm",
            "retrieved_at": retrieved_at, "sample": False, "countries": countries}


def load_raw():
    paths = {k: RAW / f"bis_house_{k}.csv" for k in FILES}
    if not all(p.exists() for p in paths.values()):
        return None
    meta_p = RAW / "bis_house_meta.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    return paths["real"].read_text(encoding="utf-8"), paths["nominal"].read_text(encoding="utf-8"), meta.get("retrieved_at")


def main() -> int:
    import requests
    texts = {}
    for k, f in FILES.items():
        r = requests.get(BASE + f, timeout=60)
        r.raise_for_status()
        if "TR" not in parse(r.text):
            print(f"{f}: Türkiye serisi yok; kaydedilmedi.", file=sys.stderr)
            return 1
        texts[k] = r.text
    RAW.mkdir(parents=True, exist_ok=True)
    for k, t in texts.items():
        (RAW / f"bis_house_{k}.csv").write_text(t, encoding="utf-8")
    (RAW / "bis_house_meta.json").write_text(json.dumps({"retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")}))
    print("BIS konut fiyatları: indirildi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
