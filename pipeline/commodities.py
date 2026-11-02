"""Monthly world commodity prices in US dollars, from Datahub mirrors on GitHub (ODC-PDDL 1.0):
  gold  — datasets/gold-prices  (1960+: World Bank Commodity Price Data "Pink Sheet"), USD per troy ounce
  brent — datasets/oil-prices   (U.S. EIA, Europe Brent spot), USD per barrel
  gas   — datasets/natural-gas  (U.S. EIA, Henry Hub spot), USD per million Btu

Usage:  python -m pipeline.commodities     download into data/raw/
pipeline.build writes site/data/emtia.json; without a download the committed JSON is kept.
"""

from __future__ import annotations

import csv
import io
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from reel import engine as e

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
TROY_OUNCE_G = 31.1034768
GH = "https://raw.githubusercontent.com/datasets/"
SERIES = {
    # key: (url, label, unit, original source, first month used)
    "gold": (GH + "gold-prices/main/data/monthly.csv", "Altın", "$/ons", "World Bank Commodity Price Data (Pink Sheet)", "1960-01"),
    "brent": (GH + "oil-prices/main/data/brent-monthly.csv", "Brent petrol", "$/varil", "U.S. Energy Information Administration (EIA)", "1987-01"),
    "gas": (GH + "natural-gas/main/data/monthly.csv", "Doğal gaz (Henry Hub)", "$/MMBtu", "U.S. Energy Information Administration (EIA)", "1997-01"),
}


def parse(text: str, first: str = "0000-00") -> list[tuple[str, float]]:
    """Date/Month,Price CSV -> sorted [(YYYY-MM, price)], one value per month (last wins)."""
    out: dict[str, float] = {}
    for r in csv.reader(io.StringIO(text)):
        if len(r) < 2 or not r[1].strip():
            continue
        try:
            v = float(r[1])
        except ValueError:
            continue                       # header
        m = r[0].strip()[:7]
        if m >= first and v > 0:
            out[m] = v
    return sorted(out.items())


def _months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])


def summarize(pts: list[tuple[str, float]]) -> dict:
    # keep the last run of consecutive months so "n months back" is n months of time
    i = len(pts) - 1
    while i > 0 and _months_between(pts[i - 1][0], pts[i][0]) == 1:
        i -= 1
    pts = pts[i:]
    vals = [v for _, v in pts]
    out = {"first": pts[0][0], "last": pts[-1][0], "latest": vals[-1]}
    for n, key in ((1, "y1"), (5, "y5"), (10, "y10"), (20, "y20")):
        c = e.change_over(vals, 12 * n, 12)
        if c:
            out[key] = round(c["change_pct"], 2)
            out[key + "_annual"] = round(c["annual_pct"], 3)
    dd = e.drawdown(vals)
    out["peak"], out["peak_value"], out["drawdown_pct"] = pts[dd["peak_index"]][0], dd["peak"], round(dd["drawdown_pct"], 2)
    return out, pts


def build_commodities(texts: dict[str, str], retrieved_at: str | None = None) -> dict:
    series = {}
    for key, (_url, label, unit, source, first) in SERIES.items():
        if key not in texts:
            continue
        summary, pts = summarize(parse(texts[key], first))
        series[key] = {"label": label, "unit": unit, "source": source, **summary, "points": [[m, round(v, 3)] for m, v in pts]}
    out = {"license": "ODC-PDDL 1.0 (Datahub kopyaları); asıl kaynaklar: Dünya Bankası, ABD EIA", "retrieved_at": retrieved_at,
           "sample": False, "series": series}
    if "gold" in series:
        out["gold_gram_usd"] = round(series["gold"]["latest"] / TROY_OUNCE_G, 3)
    if "gold" in series and "brent" in series:
        b = dict(series["brent"]["points"])
        ratio = [[m, round(v / b[m], 2)] for m, v in series["gold"]["points"] if m in b]
        if ratio:
            out["gold_brent"] = {"points": ratio, "latest": ratio[-1][1], "median": round(statistics.median(r[1] for r in ratio), 2),
                                 "first": ratio[0][0], "last": ratio[-1][0]}
    return out


def load_raw():
    paths = {k: RAW / f"commodity_{k}.csv" for k in SERIES}
    have = {k: p.read_text(encoding="utf-8") for k, p in paths.items() if p.exists()}
    if not have:
        return None
    meta_p = RAW / "commodity_meta.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    return have, meta.get("retrieved_at")


def main() -> int:
    import requests
    RAW.mkdir(parents=True, exist_ok=True)
    ok = 0
    for key, (url, *_r) in SERIES.items():
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            if len(parse(r.text)) < 24:
                raise ValueError("beklenen biçimde değil")
            (RAW / f"commodity_{key}.csv").write_text(r.text, encoding="utf-8")
            ok += 1
        except Exception as ex:  # one failing source must not block the others
            print(f"{key}: {ex}", file=sys.stderr)
    (RAW / "commodity_meta.json").write_text(json.dumps({"retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")}))
    print(f"Emtia: {ok}/{len(SERIES)} seri indirildi")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
