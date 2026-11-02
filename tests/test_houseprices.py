"""BIS residential property prices (mirror on GitHub) — parsing, gaps, summary."""

from pipeline import houseprices as hp

HEAD = "date,country_code,country,price\n"


def rows(code, start_year, values):
    out, y, q = [], start_year, 1
    for v in values:
        m = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}[q]
        out.append(f"{y}-{m},{code},X,{v}")
        q += 1
        if q == 5:
            q, y = 1, y + 1
    return "\n".join(out) + "\n"


def test_contiguous_tail_drops_history_before_a_gap():
    pts = [("2009-03-31", 1.0), ("2010-03-31", 2.0), ("2010-06-30", 3.0), ("2010-09-30", 4.0)]
    assert hp.contiguous_tail(pts) == pts[1:]


def test_build_summary_hand_computed():
    # 21 quarters 2021Q1..2026Q1: 100, 101, …, 120 (real); last 120, 4 back 116, 20 back 100
    real = HEAD + rows("TR", 2021, [100 + i for i in range(21)]) + "2026-06-30,TR,X,\n"
    nominal = HEAD + rows("TR", 2021, [100 * 1.1 ** i for i in range(21)])
    out = hp.build_houseprices(real, nominal, "2026-11-02")
    tr = out["countries"][0]
    assert tr["name"] == "Türkiye" and tr["last"] == "2026-03" and tr["latest"] == 120.0
    assert tr["since2010_pct"] == 20.0
    assert abs(tr["real_1y"] - 100 * (120 / 116 - 1)) < 0.01
    assert abs(tr["real_5y"] - 20.0) < 1e-9 and "real_10y" not in tr
    assert abs(tr["nominal_5y"] - 100 * (1.1 ** 20 - 1)) < 0.01
    assert tr["drawdown_pct"] == 0.0 and out["sample"] is False
