"""Long-run GDP per capita: Maddison Project Database 2020 (Bolt & van Zanden), via Our World in Data's
dataset repository on GitHub. Values: real GDP per capita in 2011 US$ (PPP-based).

Usage:  python -m pipeline.longrun      download into data/raw/maddison.csv
pipeline.build writes site/data/uzun_donem.json from that file; without a download the committed JSON is kept.
License: the Maddison Project states CC BY 4.0 on its website; NOT verified from this pipeline, so the
JSON carries license_verified = False until the owner confirms it.
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
RAW = ROOT / "data" / "raw" / "maddison.csv"
RAW_META = ROOT / "data" / "raw" / "maddison_meta.json"
_DS = "Maddison%20Project%20Database%202020%20(Bolt%20and%20van%20Zanden%20(2020))"
URL = f"https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/{_DS}/{_DS}.csv"
SOURCE_URL = "https://www.rug.nl/ggdc/historicaldevelopment/maddison/releases/maddison-project-database-2020"
CITATION = ("Maddison Project Database, version 2020. Bolt, Jutta and Jan Luiten van Zanden (2020), "
            "“Maddison style estimates of the evolution of the world economy. A new 2020 update”.")

# OWID entity name -> (key, Turkish name)
ENTITIES = {
    "Turkey": ("TUR", "Türkiye"), "Western Europe": ("WEU", "Batı Avrupa"), "World": ("WLD", "Dünya"),
    "Greece": ("GRC", "Yunanistan"), "Bulgaria": ("BGR", "Bulgaristan"), "Romania": ("ROU", "Romanya"),
    "Poland": ("POL", "Polonya"), "Spain": ("ESP", "İspanya"), "Portugal": ("PRT", "Portekiz"), "Italy": ("ITA", "İtalya"),
    "Germany": ("DEU", "Almanya"), "United Kingdom": ("GBR", "Birleşik Krallık"), "United States": ("USA", "ABD"),
    "Japan": ("JPN", "Japonya"), "South Korea": ("KOR", "Güney Kore"), "China": ("CHN", "Çin"), "India": ("IND", "Hindistan"),
    "Iran": ("IRN", "İran"), "Egypt": ("EGY", "Mısır"), "Mexico": ("MEX", "Meksika"), "Brazil": ("BRA", "Brezilya"),
    "Argentina": ("ARG", "Arjantin"),
}
DECADES = [(1923, 1930), (1930, 1940), (1940, 1950), (1950, 1960), (1960, 1970), (1970, 1980),
           (1980, 1990), (1990, 2000), (2000, 2010), (2010, 2018)]


def parse(text: str) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = {}
    for r in csv.DictReader(io.StringIO(text)):
        ent, v = r.get("Entity", ""), (r.get("GDP per capita") or "").strip()
        if ent in ENTITIES and v:
            out.setdefault(ENTITIES[ent][0], {})[int(r["Year"])] = float(v)
    return out


def decade_growth(series: dict[int, float], spans=DECADES) -> list[dict]:
    """Average annual (geometric) growth over each span whose both ends exist."""
    out = []
    for a, b in spans:
        if a in series and b in series:
            out.append({"from": a, "to": b, "annual_pct": 100 * e.annualize(e.total_return(series[a], series[b]), b - a)})
    return out


def build_longrun(text: str, retrieved_at: str | None = None) -> dict:
    data = parse(text)
    if "TUR" not in data:
        raise ValueError("Türkiye serisi yok")
    names = {k: n for k, n in ENTITIES.values()}
    series = {k: {"name": names[k], "points": [[y, round(v, 1)] for y, v in sorted(pts.items()) if y >= 1820]}
              for k, pts in data.items()}
    tr = data["TUR"]
    last = max(tr)
    ratios = {}
    for ref in ("WEU", "WLD", "USA"):
        if ref in data:
            common = sorted(y for y in tr if y in data[ref] and y >= 1923)
            ratios[ref] = [[y, round(100 * tr[y] / data[ref][y], 2)] for y in common]
    first_rep = 1923
    summary = {"first": first_rep, "last": last, "first_value": tr.get(first_rep), "last_value": tr[last],
               "multiple": tr[last] / tr[first_rep] if first_rep in tr else None,
               "annual_pct": 100 * e.annualize(e.total_return(tr[first_rep], tr[last]), last - first_rep) if first_rep in tr else None}
    if summary["annual_pct"] is not None:
        g = summary["annual_pct"] / 100
        summary["doubling_years"] = e.half_life_years(g) if g > 0 else None   # ln2 / ln(1+g): same formula as doubling time
    return {"source": "Maddison Project Database 2020 (Bolt ve van Zanden), Our World in Data üzerinden", "citation": CITATION,
            "url": SOURCE_URL, "license": "CC BY 4.0 (Maddison Project; doğrulanacak)", "license_verified": False,
            "unit": "2011 $ (satın alma gücüne göre, reel)", "retrieved_at": retrieved_at, "sample": False,
            "series": series, "ratios": ratios, "decades": decade_growth(tr), "summary": summary}


def load_raw():
    if not RAW.exists():
        return None
    meta = json.loads(RAW_META.read_text()) if RAW_META.exists() else {}
    return RAW.read_text(encoding="utf-8"), meta.get("retrieved_at")


def main() -> int:
    import requests
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    if "TUR" not in parse(resp.text):
        print("Maddison verisi beklenen biçimde değil; kaydedilmedi.", file=sys.stderr)
        return 1
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(resp.text, encoding="utf-8")
    RAW_META.write_text(json.dumps({"url": URL, "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")}))
    print("Maddison: indirildi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
