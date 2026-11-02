"""Country comparison data from the World Bank (World Development Indicators).

Usage:  python -m pipeline.worldbank      (no API key needed; CC BY 4.0 licensed data)
Writes data/raw/wb_<indicator>.json as {ISO3: {"YYYY": value}} and data/raw/wb_meta.json.

Each indicator code is checked against the name the API returns ("verified" only if
it matches); a mismatch is reported and the indicator is skipped, never guessed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
API = "https://api.worldbank.org/v2/country/{countries}/indicator/{code}?format=json&per_page=5000&date=2000:2030"

COUNTRIES = [
    ("TUR", "Türkiye"), ("BRA", "Brezilya"), ("MEX", "Meksika"), ("ZAF", "Güney Afrika"),
    ("IND", "Hindistan"), ("IDN", "Endonezya"), ("POL", "Polonya"), ("HUN", "Macaristan"),
    ("CHL", "Şili"), ("COL", "Kolombiya"), ("ARG", "Arjantin"), ("EGY", "Mısır"),
]

# key: (World Bank code, expected start of the API's indicator name, Turkish label, unit, kind)
INDICATORS = {
    "inflation": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices", "Enflasyon (TÜFE, yıllık)", "%", "rate"),
    "gdp_growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth", "GSYH büyümesi (reel)", "%", "rate"),
    "gdp_pc_usd": ("NY.GDP.PCAP.CD", "GDP per capita (current US$)", "Kişi başı GSYH", "$", "level"),
    "unemployment": ("SL.UEM.TOTL.ZS", "Unemployment, total", "İşsizlik oranı", "%", "rate"),
    "current_account": ("BN.CAB.XOKA.GD.ZS", "Current account balance (% of GDP)", "Cari denge / GSYH", "%", "rate"),
    "real_interest": ("FR.INR.RINR", "Real interest rate", "Reel faiz oranı", "%", "rate"),
    "population": ("SP.POP.TOTL", "Population, total", "Nüfus", "kişi", "level"),
    "exports_gdp": ("NE.EXP.GNFS.ZS", "Exports of goods and services (% of GDP)", "Mal ve hizmet ihracatı / GSYH", "%", "rate"),
    "imports_gdp": ("NE.IMP.GNFS.ZS", "Imports of goods and services (% of GDP)", "Mal ve hizmet ithalatı / GSYH", "%", "rate"),
    "urban": ("SP.URB.TOTL.IN.ZS", "Urban population (% of total", "Kentli nüfus oranı", "%", "rate"),
}


class WorldBankError(ValueError):
    pass


def parse(payload, code: str, expected_name: str) -> dict[str, dict[str, float]]:
    """API JSON -> {ISO3: {year: value}}; checks the indicator really is what we expect."""
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise WorldBankError(f"{code}: beklenmeyen yanıt: {str(payload)[:200]}")
    out: dict[str, dict[str, float]] = {}
    for row in payload[1]:
        name = (row.get("indicator") or {}).get("value", "")
        if not name.lower().startswith(expected_name.lower()):
            raise WorldBankError(f"{code}: gösterge adı beklenenle uyuşmuyor: {name!r}")
        if row.get("value") is None:
            continue
        out.setdefault(row["countryiso3code"], {})[str(row["date"])] = float(row["value"])
    return {iso: dict(sorted(years.items())) for iso, years in out.items()}


def main() -> int:
    import requests

    RAW.mkdir(parents=True, exist_ok=True)
    meta, failures = {}, 0
    countries = ";".join(c for c, _ in COUNTRIES)
    for key, (code, expected, label, unit, kind) in INDICATORS.items():
        try:
            resp = requests.get(API.format(countries=countries, code=code), timeout=60)
            resp.raise_for_status()
            data = parse(resp.json(), code, expected)
        except Exception as exc:  # one failing indicator must not stop the others
            failures += 1
            print(f"HATA {key} ({code}): {exc}")
            continue
        (RAW / f"wb_{key}.json").write_text(json.dumps(data, indent=0))
        meta[key] = {"code": code, "verified": True}
        print(f"ok {key}: {len(data)} ülke")
    (RAW / "wb_meta.json").write_text(json.dumps(meta, indent=1))
    return 1 if failures == len(INDICATORS) else 0


if __name__ == "__main__":
    sys.exit(main())
