"""District ("ilçe") population by year.

Real data: data/manual/ilceler/nufus.csv — columns plaka;ilce;yil;nufus (header optional),
from TÜİK Adrese Dayalı Nüfus Kayıt Sistemi (ADNKS) "il ve ilçe nüfusları" tables.
District names are matched to the boundary file (site/data/tr_ilceler.json) by a normalised
name inside the province; rows that do not match are listed in `unmatched` (shown on the
data status page), never silently dropped.

Without the file, --sample splits each province's (sample) population among its real
districts with SYNTHETIC weights — clearly flagged; only for layout.
"""

from __future__ import annotations

import csv
import io
import math

from pipeline.geo_districts import norm_name
from pipeline.manual import MANUAL, parse_number
from reel import engine as e

PATH = MANUAL / "ilceler" / "nufus.csv"
SOURCE = "TÜİK, Adrese Dayalı Nüfus Kayıt Sistemi — il ve ilçe nüfusları"


def parse_district_csv(text: str) -> dict[int, dict[str, dict[str, float]]]:
    """plaka;ilce;yil;nufus -> {plaka: {district name as written: {year: value}}}."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}
    delim = ";" if ";" in lines[0] else ("\t" if "\t" in lines[0] else ",")
    out: dict[int, dict[str, dict[str, float]]] = {}
    for i, row in enumerate(csv.reader(io.StringIO("\n".join(lines)), delimiter=delim)):
        if len(row) < 4:
            continue
        try:
            plaka = int(row[0].strip())
        except ValueError:
            if i == 0:
                continue
            raise ValueError(f"satır {i + 1}: plaka okunamadı: {row[0]!r}")
        if not 1 <= plaka <= 81:
            raise ValueError(f"satır {i + 1}: plaka 1–81 olmalı: {plaka}")
        v = parse_number(row[3])
        if not math.isnan(v):
            out.setdefault(plaka, {}).setdefault(row[1].strip(), {})[row[2].strip()] = v
    return out


def _noise(a: int, b: int) -> float:
    x = math.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return x - math.floor(x)


def sample_district_history(prov_hist: dict[int, dict[str, float]], geo_districts: dict) -> dict[int, dict[str, dict[str, float]]]:
    """SYNTHETIC: split each province's yearly total among its districts; shares drift with
    district-specific growth so some districts grow and others shrink. NOT real."""
    out = {}
    for key, g in geo_districts["provinces"].items():
        p = int(key)
        if p not in prov_hist:
            continue
        names = [d["name"] for d in g["districts"]]
        w = {n: (3.0 if n == "Merkez" else 0.2) + _noise(p, 7 * k + 1) ** 3 * 4 for k, n in enumerate(names)}
        r = {n: -0.025 + 0.06 * _noise(p, 7 * k + 2) for k, n in enumerate(names)}
        years = sorted(prov_hist[p], key=int)
        last = int(years[-1])
        res: dict[str, dict[str, float]] = {n: {} for n in names}
        for y in years:
            raw = {n: w[n] * (1 + r[n]) ** (int(y) - last) for n in names}
            tot = sum(raw.values())
            for n in names:
                res[n][y] = round(prov_hist[p][y] * raw[n] / tot)
        out[p] = res
    return out


def build_districts(prov_hist: dict[int, dict[str, float]], prov_hist_sample: bool, allow_sample: bool,
                    csv_text: str | None, geo_districts: dict | None) -> dict:
    geo_districts = geo_districts or {"provinces": {}}
    unmatched: list[str] = []
    if csv_text is not None:
        raw, sample = parse_district_csv(csv_text), False
        data: dict[int, dict[str, dict[str, float]]] = {}
        for p, by_name in raw.items():
            known = {norm_name(d["name"]): d["name"] for d in geo_districts["provinces"].get(str(p), {}).get("districts", [])}
            for name, years in by_name.items():
                canon = known.get(norm_name(name))
                if canon is None:
                    unmatched.append(f"{p} {name}")
                    canon = name
                data.setdefault(p, {}).setdefault(canon, {}).update(years)
    elif allow_sample and prov_hist_sample and prov_hist:
        data, sample = sample_district_history(prov_hist, geo_districts), True
    else:
        data, sample = {}, False

    provinces = {}
    for p, by_name in sorted(data.items()):
        areas = {d["name"]: d["area_km2"] for d in geo_districts["provinces"].get(str(p), {}).get("districts", [])}
        latest_year = max((y for ys in by_name.values() for y in ys), key=int)
        total = sum(ys.get(latest_year, 0.0) for ys in by_name.values())
        rows = []
        for name, ys in by_name.items():
            pts = sorted(ys.items(), key=lambda t: int(t[0]))
            last_y, last_v = pts[-1]
            g = e.growth_windows(ys, (1, 5, 10))
            row = {"name": name, "points": [list(t) for t in pts], "year": last_y, "pop": last_v,
                   "share": last_v / total if total and last_y == latest_year else None}
            for n in (1, 5, 10):
                if n in g:
                    row[f"g{n}"] = g[n]["annual_pct"]
            if 10 in g:
                row["c10"] = g[10]["change"]
            if areas.get(name):
                row["area_km2"] = areas[name]
                row["density"] = last_v / areas[name]
            rows.append(row)
        provinces[str(p)] = sorted(rows, key=lambda r: -r["pop"])
    return {"sample": sample, "source": SOURCE if not sample else "örnek (sentetik)", "has_data": bool(provinces),
            "unmatched": unmatched, "provinces": provinces}
