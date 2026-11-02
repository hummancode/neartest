"""Long-run GDP per capita (Maddison via OWID) — fixture with hand-computed values."""

import math

from pipeline import longrun as lr

CSV = """Entity,Year,GDP per capita,Population,GDP
Turkey,1913,1000,1,1
Turkey,1923,1000,1,1
Turkey,1930,1210,1,1
Turkey,2018,8000,1,1
Western Europe,1923,4000,1,1
Western Europe,2018,16000,1,1
Atlantis,2018,5,1,1
Turkey,1950,,1,1
"""


def test_parse_keeps_known_entities_and_skips_blanks():
    d = lr.parse(CSV)
    assert set(d) == {"TUR", "WEU"} and 1950 not in d["TUR"]


def test_build_summary_ratios_decades():
    out = lr.build_longrun(CSV, "2026-11-02")
    s = out["summary"]
    # 1923 -> 2018: 1000 -> 8000 = ×8 in 95 years; annual = 8^(1/95) − 1; doubling = ln2/ln(1+g) = 95/3 years
    assert s["multiple"] == 8.0
    assert abs(s["annual_pct"] - 100 * (8 ** (1 / 95) - 1)) < 1e-9
    assert abs(s["doubling_years"] - 95 / 3) < 1e-9
    assert out["ratios"]["WEU"] == [[1923, 25.0], [2018, 50.0]]   # from 1923 (1913 dropped)           # 1000/4000, 8000/16000
    dec = {(x["from"], x["to"]): x["annual_pct"] for x in out["decades"]}
    assert abs(dec[(1923, 1930)] - 100 * (1.21 ** (1 / 7) - 1)) < 1e-9     # 1000 -> 1210 over 7 years
    assert (2010, 2018) not in dec                                       # 2010 missing
    assert out["license_verified"] is False and out["series"]["TUR"]["name"] == "Türkiye"
