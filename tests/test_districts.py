"""District population: CSV parsing, name matching, sample consistency, growth."""

import math

import pytest

from pipeline import districts as dz
from pipeline.geo_districts import clean_name, norm_name, point_in_polygon, ring_area_km2

GEO = {"provinces": {"6": {"bbox": [0, 0, 1, 1], "districts": [
    {"name": "Çankaya", "d": "M0,0Z", "area_km2": 100.0, "cx": 0, "cy": 0},
    {"name": "Keçiören", "d": "M0,0Z", "area_km2": 50.0, "cx": 0, "cy": 0}]}}}


def test_norm_name_turkish_aware():
    assert norm_name("İSTANBUL") == norm_name("istanbul") == "istanbul"
    assert norm_name("Keçiören") == norm_name("KEÇİÖREN") == "kecioren"
    assert norm_name("Hakkâri") == norm_name("Hakkari")
    assert norm_name("19 Mayıs") == "19mayis"


def test_clean_name_central_districts():
    assert clean_name("Adıyaman merkez", "Adıyaman") == "Merkez"
    assert clean_name("Afyonkarahisar (Merkez İlçe)", "Afyonkarahisar") == "Merkez"
    assert clean_name("Giresun District", "Giresun") == "Merkez"
    assert clean_name("Gediz Merkez", "Kütahya") == "Gediz"
    assert clean_name("Prince Islands", "İstanbul") == "Adalar"
    assert clean_name("Merkezefendi", "Denizli") == "Merkezefendi"


def test_point_in_polygon_with_hole():
    poly = [[[0, 0], [10, 0], [10, 10], [0, 10]], [[4, 4], [6, 4], [6, 6], [4, 6]]]
    assert point_in_polygon(1, 1, poly) and not point_in_polygon(5, 5, poly) and not point_in_polygon(11, 5, poly)


def test_ring_area_one_degree_cell_at_equator():
    # 1°×1° at the equator: R² · Δλ · (sin 1° − sin 0°) ≈ 12 364 km² (R = 6371.0088 km)
    a = ring_area_km2([[0, 0], [1, 0], [1, 1], [0, 1]])
    expected = 6371.0088 ** 2 * math.radians(1) * math.sin(math.radians(1))
    assert abs(a - expected) / expected < 1e-9


def test_parse_district_csv_and_match():
    text = "plaka;ilce;yil;nufus\n6;ÇANKAYA;2023;900.000\n6;Çankaya;2024;950.000\n6;Keçiören;2024;940000\n6;Yokilce;2024;5\n"
    raw = dz.parse_district_csv(text)
    assert raw[6]["ÇANKAYA"] == {"2023": 900000.0} and raw[6]["Çankaya"] == {"2024": 950000.0}
    out = dz.build_districts({}, False, allow_sample=False, csv_text=text, geo_districts=GEO)
    ank = {d["name"]: d for d in out["provinces"]["6"]}
    assert ank["Çankaya"]["points"] == [["2023", 900000.0], ["2024", 950000.0]]   # merged by normalised name
    assert ank["Çankaya"]["g1"] == pytest.approx(100 * (950 / 900 - 1))
    assert ank["Çankaya"]["density"] == pytest.approx(9500.0)
    assert out["unmatched"] == ["6 Yokilce"] and out["sample"] is False
    assert ank["Keçiören"]["share"] == pytest.approx(940 / (950 + 940 + 0.005))


def test_sample_districts_sum_to_province():
    prov = {6: {"2023": 1000.0, "2024": 1100.0}}
    out = dz.build_districts(prov, True, allow_sample=True, csv_text=None, geo_districts=GEO)
    ds = out["provinces"]["6"]
    assert out["sample"] is True
    for i, y in enumerate(("2023", "2024")):
        assert sum(d["points"][i][1] for d in ds) == pytest.approx(prov[6][y], abs=1)


def test_no_data_without_sample():
    out = dz.build_districts({}, False, allow_sample=False, csv_text=None, geo_districts=GEO)
    assert out["provinces"] == {} and out["has_data"] is False
