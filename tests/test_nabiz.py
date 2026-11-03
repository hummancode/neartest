"""Ekonomik Nabız: neutral indicator summaries from macro + country JSON."""

from pipeline import nabiz as nz


def macro(points, freq="M", unit="%", iid="inflation"):
    return {"end_month": points[-1][0], "sample": True,
            "indicators": [{"id": iid, "label": "X", "unit": unit, "freq": freq, "points": points, "sample": True}]}


def test_monthly_card_window_change_and_percentile():
    pts = [[f"{2010 + i // 12}-{i % 12 + 1:02d}", float(i)] for i in range(150)]   # rising 0 … 149
    out = nz.build_nabiz(macro(pts), {"indicators": [], "countries": []})
    c = out["cards"][0]
    assert c["value"] == 149.0 and c["change_1y"] == 12.0 and c["change_1y_pct"] is None    # % unit → change in points
    assert c["window"]["n"] == 120 and c["window"]["min"] == 30.0 and c["window"]["percentile"] == 1.0
    assert c["group"] == "Fiyatlar ve faiz" and c["sample"] is True and len(c["spark"]) == 120


def test_peer_rank():
    countries = {"countries": [{"iso": "TUR", "name": "Türkiye"}, {"iso": "BRA", "name": "Brezilya"}, {"iso": "MEX", "name": "Meksika"}],
                 "indicators": [{"id": "inflation", "label": "Enflasyon", "unit": "%", "sample": False,
                                 "series": {"TUR": [["2024", 50.0]], "BRA": [["2024", 4.0]], "MEX": [["2024", 60.0]]}}]}
    out = nz.build_nabiz(macro([["2025-01", 1.0], ["2025-02", 2.0]]), countries)
    p = out["cards"][0]["peer"]
    assert p["rank"] == 2 and p["n"] == 3 and p["highest"] == "Meksika" and p["median"] == 50.0 and p["year"] == "2024"


def test_level_unit_gets_percent_change_and_unknown_ids_skipped():
    pts = [[f"2024-{m:02d}", 100.0] for m in range(1, 13)] + [["2025-01", 110.0]]
    out = nz.build_nabiz(macro(pts, unit="milyar $", iid="reserves"), {})
    assert abs(out["cards"][0]["change_1y_pct"] - 10.0) < 1e-9
    assert nz.build_nabiz(macro(pts, iid="nope"), {})["cards"] == []


def test_series_card_semiannual_and_extras():
    pts = [["2024-01", 10.0], ["2024-07", 12.0], ["2025-01", 15.0]]
    c = nz.series_card(cid="x", label="X", unit="%", group="G", reading="", points=pts, per_year=2, source="s")
    assert c["change_1y"] == 5.0 and c["change_1y_pct"] is None and c["freq"] == "S" and c["window"]["percentile"] == 1.0
    assert nz.series_card(cid="x", label="X", unit="$", group="G", reading="", points=[["2024-01", 1.0]], per_year=12, source="s") is None
    house = {"countries": [{"code": "TR", "series": [["2025-03", 200.0], ["2025-06", 210.0]]}]}
    ex = nz.real_extras(None, house, None)
    assert ex[0]["id"] == "house_real" and ex[0]["sample"] is False
