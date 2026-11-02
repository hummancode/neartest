"""Province geometry processing (no network)."""

from pipeline import geo


def test_simplify_drops_collinear_points():
    line = [(0, 0), (1, 0.001), (2, 0), (3, 5), (4, 0)]
    out = geo.simplify(line, tolerance=0.01)
    assert out[0] == (0, 0) and out[-1] == (4, 0) and (3, 5) in out and (1, 0.001) not in out


def test_project_keeps_turkey_inside_viewbox():
    x, y = geo.project(26.0, 42.1)     # north-west corner area
    x2, y2 = geo.project(44.8, 35.8)   # south-east corner area
    assert 0 <= x < x2 <= geo.WIDTH and 0 <= y < y2


def test_features_to_paths_filters_turkey_and_reads_plate():
    fc = {"features": [
        {"properties": {"adm0_a3": "TUR", "iso_3166_2": "TR-06", "name": "Ankara"},
         "geometry": {"type": "Polygon", "coordinates": [[[32, 39], [33, 39], [33, 40], [32, 40], [32, 39]]]}},
        {"properties": {"adm0_a3": "GRC", "iso_3166_2": "GR-I", "name": "Attiki"},
         "geometry": {"type": "Polygon", "coordinates": [[[23, 38], [24, 38], [24, 39], [23, 38]]]}},
    ]}
    out = geo.features_to_paths(fc)
    assert [p["plaka"] for p in out["provinces"]] == [6]
    assert out["provinces"][0]["d"].startswith("M") and out["provinces"][0]["d"].endswith("Z")
