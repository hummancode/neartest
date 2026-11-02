"""Commodity prices (gold, Brent, gas) — parsing and summary with hand-computed values."""

from pipeline import commodities as cm


def monthly(start_year, values, day=""):
    out, y, m = ["Date,Price"], start_year, 1
    for v in values:
        out.append(f"{y}-{m:02d}{day},{v}")
        m += 1
        if m == 13:
            m, y = 1, y + 1
    return "\n".join(out) + "\n"


def test_parse_monthly_and_daily_dates():
    assert cm.parse("Date,Price\n2026-08-15,91.08\n2026-09-15,114.16\n") == [("2026-08", 91.08), ("2026-09", 114.16)]
    assert cm.parse("Month,Price\n1997-01,3.45\n1997-02,\n") == [("1997-01", 3.45)]
    assert cm.parse("Date,Price\n1959-12,35\n1960-01,35.1\n", first="1960-01") == [("1960-01", 35.1)]


def test_summary_and_ratio():
    # gold: 61 months 2021-01..2026-01, 100 → 200 linearly in steps of 100/60; brent constant 50
    gold = monthly(2021, [100 + i * 100 / 60 for i in range(61)])
    brent = monthly(2021, [50] * 61, day="-15")
    out = cm.build_commodities({"gold": gold, "brent": brent}, "2026-11-02")
    g = out["series"]["gold"]
    assert g["last"] == "2026-01" and abs(g["latest"] - 200) < 1e-9
    assert abs(g["y5"] - 100.0) < 1e-6                       # 100 -> 200
    assert abs(g["y1"] - 100 * (200 / (100 + 48 * 100 / 60) - 1)) < 0.01
    assert g["drawdown_pct"] == 0.0
    assert abs(out["gold_gram_usd"] - 200 / 31.1034768) < 1e-3
    gb = out["gold_brent"]
    assert gb["latest"] == 4.0 and gb["first"] == "2021-01" and abs(gb["median"] - 3.0) < 0.02   # ratio 2 → 4, median ≈ 3
