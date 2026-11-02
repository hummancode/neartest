"""Big Mac index parsing and build (fixture rows copied from the published CSV, 2026-07)."""

from pipeline import bigmac as bm

CSV = """date,iso_a3,currency_code,name,local_price,dollar_ex,dollar_price,USD_raw,EUR_raw,GBP_raw,JPY_raw,CNY_raw,GDP_bigmac,adj_price,USD_adjusted,EUR_adjusted,GBP_adjusted,JPY_adjusted,CNY_adjusted
2026-01-01,TUR,TRY,Turkey,255,43.1945,5.90352938452812,-0.03537,0,0,0,0,0,0,0.26,0,0,0,0
2026-01-01,USA,USD,United States,6.12,1,6.12,0,0,0,0,0,0,0,0,0,0,0,0
2026-07-01,EUZ,EUR,Euro area,6.19,0.87439,7.07922094259998,0.13814,0,0,0,0,0,0,,0,0,0,0
2026-07-01,TUR,TRY,Turkey,325,47.0275,6.91085003455425,0.11107,0,0,0,0,0,0,0.38699,0,0,0,0
2026-07-01,USA,USD,United States,6.22,1,6.22,0,0,0,0,0,0,0,0,0,0,0,0
2026-07-01,XXX,XXX,Nowhere,NA,1,,,0,0,0,0,0,0,,0,0,0,0
"""


def test_parse_skips_missing_prices():
    rows = bm.parse(CSV)
    assert len(rows) == 5 and all(r["iso"] != "XXX" for r in rows)
    assert rows[2]["usd_adj"] is None


def test_build_recomputes_and_matches_published_index():
    out = bm.build_bigmac(CSV, "2026-11-02")
    assert out["latest_date"] == "2026-07-01" and out["mismatches"] == 0 and out["sample"] is False
    snap = {x["iso"]: x for x in out["snapshot"]}
    assert snap["TUR"]["name"] == "Türkiye" and abs(snap["TUR"]["valuation"] - 0.11107) < 1e-5
    assert [x["iso"] for x in out["snapshot"]] == ["EUZ", "TUR", "USA"]          # by dollar price, high first
    # 2026-01: 255 / 6.12 = 41.667 implied vs 43.1945 actual -> −3.54 %
    tur = out["history"]["TUR"]["points"]
    assert tur[0][0] == "2026-01-01" and abs(tur[0][4] - (255 / 6.12 / 43.1945 - 1)) < 1e-5


def test_build_counts_mismatch():
    bad = CSV.replace("2026-07-01,TUR,TRY,Turkey,325,47.0275,6.91085003455425,0.11107", "2026-07-01,TUR,TRY,Turkey,325,47.0275,6.91085003455425,0.5")
    assert bm.build_bigmac(bad)["mismatches"] == 1


def test_old_lira_converted_before_2005():
    text = CSV.splitlines()[0] + "\n2002-04-01,TUR,TRY,Turkey,4000000,1324500,3.02,0.28511,0,0,0,0,0,0,0.86532,0,0,0,0\n" \
           "2002-04-01,USA,USD,United States,2.35,1,2.35,0,0,0,0,0,0,0,0,0,0,0,0\n"
    r = [x for x in bm.parse(text) if x["iso"] == "TUR"][0]
    assert r["local_price"] == 4.0 and r["fx"] == 1.3245                  # new lira
    out = bm.build_bigmac(text)
    assert out["mismatches"] == 0                                         # ratios unchanged by redenomination
