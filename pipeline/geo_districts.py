"""Turkey district ("ilçe") outlines as SVG paths, grouped by province.

Source: geoBoundaries gbOpen TUR ADM2 + ADM1 (derived from OpenStreetMap, ODbL 1.0 —
attribution "© OpenStreetMap katkıcıları" is shown wherever the map is drawn).

Usage:  python -m pipeline.geo_districts ADM2.geojson ADM1.geojson
        (download: github.com/wmgeolab/geoBoundaries — releaseData/gbOpen/TUR/ADM{1,2}/
         geoBoundaries-TUR-ADM{1,2}_simplified.geojson; the files are Git LFS objects)
Writes site/data/tr_ilceler.json:
    {scale, source, license, provinces: {plaka: {bbox, districts: [{name, d, area_km2, cx, cy}]}}}
Coordinates use pipeline.geo's projection multiplied by `scale`, so a province page can zoom
to its own bounding box. The province of each district = the ADM1 polygon containing an
interior point of the district (district features carry no province code).
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from pathlib import Path

from pipeline import geo
from pipeline.provinces import NAMES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "tr_ilceler.json"
SCALE = 10
EARTH_R = 6371.0088

_TR = str.maketrans({"İ": "i", "I": "ı", "Ç": "ç", "Ğ": "ğ", "Ö": "ö", "Ş": "ş", "Ü": "ü"})
_ASCII = str.maketrans({"ı": "i", "ç": "c", "ğ": "g", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"})


def norm_name(s: str) -> str:
    """Name key for matching across sources: Turkish-aware lowercase, no diacritics/spaces/punctuation."""
    s = s.strip().translate(_TR).lower().translate(_ASCII)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if c.isalnum() and not unicodedata.combining(c))


RENAME = {"Prince Islands": "Adalar"}


def clean_name(name: str, province: str) -> str:
    """OSM names -> TÜİK style: '<İl> merkez', '<İl> (Merkez İlçe)', 'Giresun District' -> 'Merkez'."""
    name = RENAME.get(name.strip(), name.strip())
    base = re.sub(r"\s*\((merkez[^)]*)\)\s*$", "", name, flags=re.I)
    base = re.sub(r"\s+(merkezi?|district)$", "", base, flags=re.I).strip()
    if not base or norm_name(base) == norm_name(province):
        return "Merkez"
    return base


def point_in_ring(x: float, y: float, ring) -> bool:
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def point_in_polygon(x: float, y: float, poly) -> bool:
    """poly = [outer, hole, ...] (GeoJSON Polygon coordinates)."""
    return point_in_ring(x, y, poly[0]) and not any(point_in_ring(x, y, h) for h in poly[1:])


def _polys(geom) -> list:
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]


def ring_area_km2(ring) -> float:
    """Spherical polygon area (km²) of a lon/lat ring — sum of (λ2−λ1)(2 + sinφ1 + sinφ2)·R²/2."""
    total = 0.0
    for (l1, p1), (l2, p2) in zip(ring, ring[1:] + ring[:1]):
        total += math.radians(l2 - l1) * (2 + math.sin(math.radians(p1)) + math.sin(math.radians(p2)))
    return abs(total) * EARTH_R ** 2 / 2


def geom_area_km2(geom) -> float:
    return sum(ring_area_km2(p[0]) - sum(ring_area_km2(h) for h in p[1:]) for p in _polys(geom))


def interior_point(poly) -> tuple[float, float]:
    """A point inside the polygon: the vertex mean if inside, else the midpoint of the widest
    inside span of the horizontal line through it."""
    ring = poly[0]
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    if point_in_polygon(cx, cy, poly):
        return cx, cy
    xs = []
    for r in poly:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            if (y1 > cy) != (y2 > cy):
                xs.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    spans = [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]
    if not spans:
        return cx, cy
    a, b = max(spans, key=lambda s: s[1] - s[0])
    return (a + b) / 2, cy


def province_lookup(adm1: dict) -> list[tuple[int, list]]:
    """[(plaka, polygons)] from ADM1 features matched to plate numbers by name."""
    by_key = {norm_name(n): i + 1 for i, n in enumerate(NAMES)}
    out = []
    for f in adm1["features"]:
        name = f["properties"].get("shapeName", "")
        plaka = by_key.get(norm_name(name))
        if plaka is None:
            raise ValueError(f"il adı eşleşmedi: {name!r}")
        out.append((plaka, _polys(f["geometry"])))
    return out


def find_province(x: float, y: float, lookup) -> int | None:
    for plaka, polys in lookup:
        if any(point_in_polygon(x, y, p) for p in polys):
            return plaka
    return None


def districts_to_paths(adm2: dict, adm1: dict, tolerance: float = 2.0) -> dict:
    lookup = province_lookup(adm1)
    provinces: dict[int, dict] = {}
    unassigned = []
    for f in adm2["features"]:
        name = f["properties"].get("shapeName", "").strip()
        polys = _polys(f["geometry"])
        biggest = max(polys, key=lambda p: ring_area_km2(p[0]))
        lon, lat = interior_point(biggest)
        plaka = find_province(lon, lat, lookup)
        if plaka is None:
            unassigned.append(name)
            continue
        parts, pts_big, area_big = [], [], 0.0
        for poly in polys:
            pts = geo.simplify([tuple(v * SCALE for v in geo.project(x, y)) for x, y in poly[0]], tolerance)
            if len(pts) < 3:
                continue
            area = 0.5 * abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])))
            if area < 40:                          # drop specks
                continue
            parts.append("M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + "Z")
            if area > area_big:
                area_big, pts_big = area, pts
        if not parts:
            continue
        lx, ly = (v * SCALE for v in geo.project(lon, lat))
        provinces.setdefault(plaka, {"districts": []})["districts"].append(
            {"name": clean_name(name, NAMES[plaka - 1]), "d": "".join(parts), "area_km2": round(geom_area_km2(f["geometry"]), 1),
             "cx": round(lx), "cy": round(ly)})
    for plaka, p in provinces.items():
        p["districts"].sort(key=lambda d: d["name"])
        nums = [float(v) for d in p["districts"] for v in d["d"].replace("M", " ").replace("L", " ").replace("Z", " ").replace(",", " ").split()]
        xs, ys = nums[0::2], nums[1::2]
        p["bbox"] = [min(xs), min(ys), max(xs), max(ys)]
    return {"scale": SCALE, "source": "geoBoundaries (OpenStreetMap tabanlı)",
            "license": "ODbL 1.0 — © OpenStreetMap katkıcıları",
            "unassigned": unassigned,
            "provinces": {str(k): provinces[k] for k in sorted(provinces)}}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    adm2, adm1 = (json.loads(Path(a).read_text(encoding="utf-8")) for a in argv[:2])
    out = districts_to_paths(adm2, adm1)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    n = sum(len(p["districts"]) for p in out["provinces"].values())
    print(f"yazıldı: {OUT.relative_to(ROOT)} — {n} ilçe, {len(out['provinces'])} il, "
          f"{OUT.stat().st_size // 1024} KB; eşleşmeyen: {out['unassigned']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
