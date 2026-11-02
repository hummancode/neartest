"""Foreign-trade breakdowns for the Türkiye profile page.

data/manual/dis_ticaret_ulke.csv  columns: yil;ulke;ihracat_milyon_usd;ithalat_milyon_usd
data/manual/dis_ticaret_urun.csv  columns: yil;urun;ihracat_milyon_usd
(Source: TÜİK dış ticaret istatistikleri.) Missing files -> flagged SYNTHETIC sample.
"""

from __future__ import annotations

import csv
import io
import math

from pipeline.manual import MANUAL, parse_number

SAMPLE_PARTNERS = ["Almanya", "ABD", "Birleşik Krallık", "Irak", "İtalya", "Fransa", "İspanya", "Rusya", "Çin", "BAE"]
SAMPLE_PRODUCTS = ["Motorlu kara taşıtları", "Makineler", "Demir-çelik", "Elektrikli cihazlar", "Mineral yakıtlar",
                   "Örme giyim", "Plastikler", "Kıymetli taşlar ve metaller", "Meyve ve sert kabuklular", "Örülmemiş giyim"]


def _rows(text: str, n: int) -> list[list[str]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    delim = ";" if ";" in lines[0] else ("\t" if "\t" in lines[0] else ",")
    rows = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=delim))
    if rows and not rows[0][0].strip()[:4].isdigit():
        rows = rows[1:]
    return [r for r in rows if len(r) >= n]


def parse_partners(text: str) -> dict:
    rows = _rows(text, 4)
    if not rows:
        return {}
    year = max(r[0].strip() for r in rows)
    items = [{"name": r[1].strip(), "exports": parse_number(r[2]), "imports": parse_number(r[3])}
             for r in rows if r[0].strip() == year]
    return {"year": year, "items": sorted(items, key=lambda x: -x["exports"])}


def parse_products(text: str) -> dict:
    rows = _rows(text, 3)
    if not rows:
        return {}
    year = max(r[0].strip() for r in rows)
    items = [{"name": r[1].strip(), "exports": parse_number(r[2])} for r in rows if r[0].strip() == year]
    return {"year": year, "items": sorted(items, key=lambda x: -x["exports"])}


def build_trade(allow_sample: bool) -> dict:
    out = {"source": "TÜİK dış ticaret istatistikleri"}
    for key, fname, parser in (("partners", "dis_ticaret_ulke.csv", parse_partners), ("products", "dis_ticaret_urun.csv", parse_products)):
        path = MANUAL / fname
        if path.exists():
            out[key] = parser(path.read_text(encoding="utf-8-sig")) | {"sample": False}
        elif allow_sample:
            names = SAMPLE_PARTNERS if key == "partners" else SAMPLE_PRODUCTS
            items = [{"name": nm, "exports": round(20000 * math.exp(-k / 3.5), 1)} | ({"imports": round(15000 * math.exp(-((k * 7) % 10) / 3.0), 1)} if key == "partners" else {})
                     for k, nm in enumerate(names)]
            out[key] = {"year": "2024", "items": items, "sample": True}
    return out
