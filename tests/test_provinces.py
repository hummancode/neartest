"""Province factbook builder."""

from pipeline import provinces as pv


def test_names_and_regions_cover_81_provinces():
    assert len(pv.NAMES) == 81 and pv.NAMES[33] == "İstanbul" and pv.NAMES[80] == "Düzce"
    assert sorted(pv.REGION_OF) == list(range(1, 82))


def test_parse_province_csv_latest_year_wins():
    text = "plaka;yil;deger\n6;2023;100\n6;2024;120\n34;2024;1.500,5\n"
    assert pv.parse_province_csv(text) == {6: ("2024", 120.0), 34: ("2024", 1500.5)}


def test_build_with_manual_and_derived(tmp_path):
    (tmp_path / "population.csv").write_text("6;2024;1000\n", encoding="utf-8")
    (tmp_path / "gdp_mn_tl.csv").write_text("6;2024;2\n", encoding="utf-8")            # 2 M TL
    (tmp_path / "exports_mn_usd.csv").write_text("6;2024;0.01\n", encoding="utf-8")    # 10.000 $
    usd = {f"2024-{m:02d}": 30.0 for m in range(1, 13)}
    out = pv.build_provinces(usd, allow_sample=False, directory=tmp_path)
    ank = next(p for p in out["provinces"] if p["plaka"] == 6)["values"]
    assert ank["gdp_per_capita_tl"]["value"] == 2000.0                    # 2e6 / 1000
    assert abs(ank["exports_gdp"]["value"] - 15.0) < 1e-12                # 0.01 M$ x 30 / 2 M TL = 15 %
    assert ank["exports_per_capita"]["value"] == 10.0
    assert "wealth_total_bn" not in ank and out["sample"] is False


def test_sample_build_is_flagged_and_complete():
    usd = {f"2024-{m:02d}": 30.0 for m in range(1, 13)}
    out = pv.build_provinces(usd, allow_sample=True, directory=pv.MANUAL / "no-such-dir")
    assert out["sample"] is True and len(out["provinces"]) == 81
    ist = next(p for p in out["provinces"] if p["plaka"] == 34)["values"]
    assert ist["population"]["sample"] is True and "wealth_per_household" in ist


def test_new_derived_and_estimates(tmp_path):
    for name, val in (("population", 1000), ("household_size", 4), ("deposits_mn_tl", 50), ("m2_price_tl", 20000),
                      ("rent_m2_tl", 100), ("avg_wage_tl", 25000), ("income_gini", 0.4), ("cars", 200)):
        (tmp_path / f"{name}.csv").write_text(f"6;2024;{val}\n", encoding="utf-8")
    (tmp_path / "bist_sirketler.csv").write_text("plaka;kod;unvan;sektor\n6;AAAA;A A.Ş.;Sanayi\n6;BBBB;B A.Ş.;Banka\n", encoding="utf-8")
    out = pv.build_provinces({}, allow_sample=False, directory=tmp_path, gold_gram_tl=4000.0, gold_sample=False)
    v = next(p for p in out["provinces"] if p["plaka"] == 6)["values"]
    assert abs(v["gross_rent_yield"]["value"] - 6.0) < 1e-12 and abs(v["rent_to_wage"]["value"] - 40.0) < 1e-12
    assert v["cars_per_1000"]["value"] == 200.0
    assert v["listed_companies"]["value"] == 2 and out["has_company_list"]
    assert v["wealth_gini"]["value"] > 0.4                       # multiplier 1.8 > 1
    assert abs(v["gold_tonnes"]["value"] - pv.WEALTH_DEFAULTS["gold_total_tonnes"]) < 1e-9   # only province with data
    assert abs(v["gold_value_bn"]["value"] - v["gold_tonnes"]["value"] * 1e6 * 4000 / 1e9) < 1e-9


def test_breakdowns_shares_lq_and_history(tmp_path):
    (tmp_path / "gsyh_sektor.csv").write_text(
        "plaka;yil;sektor;deger\n6;2024;Sanayi;50\n6;2024;Hizmet;50\n34;2024;Sanayi;0\n34;2024;Hizmet;100\n", encoding="utf-8")
    (tmp_path / "ihracat_sektor.csv").write_text("6;2024;Otomotiv;3\n6;2024;Kimya;1\n", encoding="utf-8")
    (tmp_path / "ihracat_ulke.csv").write_text("6;2024;Almanya;3\n6;2024;ABD;1\n", encoding="utf-8")
    (tmp_path / "exports_mn_usd.csv").write_text("6;2019;2\n6;2024;4\n", encoding="utf-8")
    out = pv.build_provinces({}, allow_sample=False, directory=tmp_path)
    ank = next(p for p in out["provinces"] if p["plaka"] == 6)
    gva = {x["name"]: x for x in ank["structure"]["gva"]["items"]}
    # national: Sanayi 50/200 = 25 %, Hizmet 75 %; Ankara 50 % / 50 % -> LQ 2 and 2/3
    assert abs(gva["Sanayi"]["lq"] - 2.0) < 1e-12 and abs(gva["Hizmet"]["lq"] - 2 / 3) < 1e-12
    assert abs(ank["values"]["export_hhi"]["value"] - (0.75 ** 2 + 0.25 ** 2)) < 1e-12
    assert ank["values"]["top_market_share"]["value"] == 75.0
    assert ank["values"]["exports_growth_5y"]["value"] == 100.0
    assert ank["summary"]["top_exports"] == ["Otomotiv", "Kimya"]


def test_sample_breakdowns_add_up():
    out = pv.build_provinces({f"2024-{m:02d}": 30.0 for m in range(1, 13)}, allow_sample=True, directory=pv.MANUAL / "no-such")
    ist = out["provinces"][33]
    gva_total = sum(x["value"] for x in ist["structure"]["gva"]["items"])
    assert abs(gva_total - ist["values"]["gdp_mn_tl"]["value"]) / gva_total < 1e-3
    assert ist["structure"]["exports_country"]["sample"] is True and "exports_mn_usd" in ist["history"]
