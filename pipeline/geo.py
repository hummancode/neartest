"""Turkey province outlines as ready-to-draw SVG paths, from Natural Earth (public domain).

Usage:  python -m pipeline.geo path/to/ne_10m_admin_1_states_provinces.geojson
        (download: github.com/nvkelso/natural-earth-vector — geojson/ne_10m_admin_1_states_provinces.geojson)
Writes site/data/tr_iller.json: {width, height, provinces: [{plaka, name, d, cx, cy}]}.
Province id = plate number from ISO 3166-2 (TR-34 -> 34).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "tr_iller.json"

# Equirectangular projection scaled by cos(latitude ~39°): fine for a country Turkey's size.
LON0, LON1, LAT0, LAT1 = 25.5, 45.0, 35.7, 42.3
K = math.cos(math.radians(39.0))
WIDTH = 1000.0
SCALE = WIDTH / ((LON1 - LON0) * K)
HEIGHT = round((LAT1 - LAT0) * SCALE, 1)


def project(lon: float, lat: float) -> tuple[float, float]:
    return ((lon - LON0) * K * SCALE, (LAT1 - lat) * SCALE)


def _perp(p, a, b) -> float:
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return math.hypot(x - x1, y - y1)
    return abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.hypot(dx, dy)


def simplify(points: list[tuple[float, float]], tolerance: float) -> list[tuple[float, float]]:
    """Douglas–Peucker line simplification (iterative)."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i, j = stack.pop()
        best, idx = 0.0, None
        for k in range(i + 1, j):
            d = _perp(points[k], points[i], points[j])
            if d > best:
                best, idx = d, k
        if idx is not None and best > tolerance:
            keep[idx] = True
            stack += [(i, idx), (idx, j)]
    return [p for p, k in zip(points, keep) if k]


def _ring_path(ring, tolerance) -> tuple[str, float, list]:
    pts = simplify([project(lon, lat) for lon, lat in ring], tolerance)
    if len(pts) < 3:
        return "", 0.0, []
    area = 0.5 * abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])))
    d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    return d, area, pts


def features_to_paths(fc: dict, tolerance: float = 0.6) -> dict:
    provinces = []
    for f in fc["features"]:
        props = f.get("properties") or {}
        if props.get("adm0_a3") != "TUR":
            continue
        iso = props.get("iso_3166_2", "")
        if not iso.startswith("TR-"):
            continue
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        parts, biggest = [], (0.0, [])
        for poly in polys:
            for ring in poly[:1]:                      # outer rings only; islands are separate polygons
                d, area, pts = _ring_path(ring, tolerance)
                if d and area > 4:                     # drop specks (tiny islets) at this scale
                    parts.append(d)
                    if area > biggest[0]:
                        biggest = (area, pts)
        if not parts:
            continue
        pts = biggest[1]
        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        provinces.append({"plaka": int(iso[3:]), "name": props.get("name", iso), "d": "".join(parts),
                          "cx": round(cx, 1), "cy": round(cy, 1)})
    provinces.sort(key=lambda p: p["plaka"])
    return {"width": WIDTH, "height": HEIGHT, "source": "Natural Earth (kamu malı)", "provinces": provinces}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    fc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    out = features_to_paths(fc)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"yazıldı: {OUT.relative_to(ROOT)} — {len(out['provinces'])} il, {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
