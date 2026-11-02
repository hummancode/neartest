"""Engine tests. Every expected value below is computed by hand in the comment."""

import math

import pytest

from reel import engine as e


def close(a, b, tol=1e-12):
    return math.isclose(a, b, rel_tol=0, abs_tol=tol)


# --- scalar building blocks -------------------------------------------------

def test_total_return_doubling():
    assert e.total_return(100, 200) == 1.0


def test_total_return_rejects_nonpositive_start():
    with pytest.raises(e.SeriesError):
        e.total_return(0, 10)


def test_annualize_doubling_over_two_years():
    # 2x in 2 years -> sqrt(2) - 1 = 0.41421356...
    assert close(e.annualize(1.0, 2), math.sqrt(2) - 1)


def test_annualize_total_loss_is_minus_one():
    assert e.annualize(-1.0, 5) == -1.0


def test_real_return_is_fisher_not_subtraction():
    # 50 % nominal, 40 % inflation: 1.5/1.4 - 1 = 0.0714285..., NOT 0.10
    r = e.real_return(0.50, 0.40)
    assert close(r, 1.5 / 1.4 - 1)
    assert not close(r, 0.10, tol=1e-3)


def test_real_return_zero_when_nominal_equals_inflation():
    assert e.real_return(0.65, 0.65) == 0.0


def test_house_example_from_twitter_log():
    # Twitter log #1: 1M TL -> 10M TL while USD/TRY went 8.4739 -> 47.5379.
    # USD return: 10 / (47.5379/8.4739) - 1 = 0.78256...
    fx = 47.5379 / 8.4739 - 1
    u = e.currency_return(9.0, fx)
    assert close(u, 10 * 8.4739 / 47.5379 - 1)
    assert 0.78 < u < 0.79


# --- month arithmetic -------------------------------------------------------

def test_shift_month_across_year():
    assert e.shift_month("2024-01", -1) == "2023-12"
    assert e.shift_month("2024-03", -12) == "2023-03"
    assert e.shift_month("2023-12", 1) == "2024-01"


def test_bad_month_rejected():
    with pytest.raises(e.SeriesError):
        e.shift_month("2024-13", 0)


def test_window_return_requires_both_ends():
    s = {"2024-01": 100.0, "2025-01": 130.0}
    assert close(e.window_return(s, "2025-01", 12), 0.30)
    with pytest.raises(e.SeriesError):
        e.window_return(s, "2025-01", 24)


# --- deposit index ----------------------------------------------------------

def test_deposit_index_compounds_monthly():
    # 12 % annual for 3 months: 100 -> 101 -> 102.01 (third month has no prior-rate step yet)
    rates = {"2024-01": 0.12, "2024-02": 0.12, "2024-03": 0.12}
    idx = e.deposit_index(rates)
    assert idx["2024-01"] == 100.0
    assert close(idx["2024-02"], 101.0)
    assert close(idx["2024-03"], 102.01)


def test_deposit_index_rejects_gaps():
    with pytest.raises(e.SeriesError):
        e.deposit_index({"2024-01": 0.1, "2024-03": 0.1})


# --- asset windows ----------------------------------------------------------

def _flat_series(start, months, start_value, monthly_growth):
    out, v = {}, start_value
    for k in range(months + 1):
        out[e.shift_month(start, k)] = v
        v *= 1 + monthly_growth
    return out


def test_asset_windows_known_values():
    # Asset +100 % in 1 year, CPI +60 %, USD/TRY +25 %.
    asset = {"2024-06": 100.0, "2025-06": 200.0}
    cpi = {"2024-06": 1000.0, "2025-06": 1600.0}
    fx = {"2024-06": 32.0, "2025-06": 40.0}
    [w] = e.asset_windows(asset, cpi, fx, "2025-06", years_list=(1,))
    assert close(w.nominal_tl, 1.0)
    assert close(w.real_tl, 2.0 / 1.6 - 1)   # 0.25
    assert close(w.usd, 2.0 / 1.25 - 1)      # 0.60
    assert close(w.real_tl_annual, w.real_tl)  # 1 year: annual == cumulative


def test_asset_windows_skips_uncovered_windows():
    asset = _flat_series("2022-01", 36, 100, 0.01)
    cpi = _flat_series("2022-01", 36, 100, 0.02)
    fx = _flat_series("2022-01", 36, 10, 0.015)
    res = e.asset_windows(asset, cpi, fx, "2025-01")
    assert [w.years for w in res] == [1, 3]   # no 5- or 10-year data


def test_asset_matching_inflation_has_zero_real_return():
    s = _flat_series("2020-01", 60, 100, 0.03)
    res = e.asset_windows(s, s, s, "2025-01")
    for w in res:
        assert close(w.real_tl, 0.0, tol=1e-12)
        assert close(w.usd, 0.0, tol=1e-12)


def test_to_tl():
    assert e.to_tl({"2024-01": 10.0}, {"2024-01": 30.0}) == {"2024-01": 300.0}


def test_value_today():
    # 100 TL when CPI was 500 is 300 TL when CPI is 1500.
    assert e.value_today(100, 500, 1500) == 300.0


# --- personal inflation (Aşama 5) -------------------------------------------

def test_normalize_shares():
    # 750 + 250 = 1000 -> 0.75 / 0.25
    assert e.normalize_shares({"a": 750, "b": 250}) == {"a": 0.75, "b": 0.25}


def test_normalize_shares_rejects_negative_and_empty():
    with pytest.raises(e.SeriesError):
        e.normalize_shares({"a": -1, "b": 5})
    with pytest.raises(e.SeriesError):
        e.normalize_shares({"a": 0, "b": 0})


def test_personal_inflation_equal_split():
    # half in a group at +10 %, half at +30 % -> +20 %
    assert close(e.personal_inflation({"a": 1, "b": 1}, {"a": 0.10, "b": 0.30}), 0.20)


def test_personal_inflation_weighted():
    # 0.75 * 0.40 + 0.25 * 0.80 = 0.30 + 0.20 = 0.50
    assert close(e.personal_inflation({"a": 750, "b": 250}, {"a": 0.40, "b": 0.80}), 0.50)


def test_personal_inflation_ignores_zero_share_without_data():
    # group "c" has no price data, but the user spends nothing there
    assert close(e.personal_inflation({"a": 100, "c": 0}, {"a": 0.35}), 0.35)


def test_personal_inflation_requires_data_for_spent_groups():
    with pytest.raises(e.SeriesError):
        e.personal_inflation({"a": 100, "c": 50}, {"a": 0.35})


def test_contributions_sum_to_personal_inflation():
    # 0.75 * 0.40 = 0.30 and 0.25 * 0.80 = 0.20
    c = e.inflation_contributions({"a": 750, "b": 250}, {"a": 0.40, "b": 0.80})
    assert close(c["a"], 0.30) and close(c["b"], 0.20)


# --- real interest rates (Aşama 6) ------------------------------------------

def test_trailing_real_rate():
    # Rate quoted 2025-01 = 50 %, CPI over 2024-01 -> 2025-01 = +40 %: 1.5/1.4 - 1 = 0.0714285...
    rates = {"2024-01": 0.45, "2025-01": 0.50}
    cpi = {"2024-01": 100.0, "2025-01": 140.0}
    out = e.trailing_real_rates(rates, cpi)
    assert list(out) == ["2025-01"]          # 2024-01 has no CPI a year earlier
    assert close(out["2025-01"], 1.5 / 1.4 - 1)


def test_ex_post_real_rate():
    # Rate quoted 2024-01 = 45 %, CPI over the following year = +40 %: 1.45/1.4 - 1 = 0.0357142...
    rates = {"2024-01": 0.45, "2025-01": 0.50}
    cpi = {"2024-01": 100.0, "2025-01": 140.0}
    out = e.ex_post_real_rates(rates, cpi)
    assert list(out) == ["2025-01"]          # keyed by the month the year ends
    assert close(out["2025-01"], 1.45 / 1.4 - 1)


def test_real_rates_skip_months_without_data():
    rates = {"2025-01": 0.50}                # no rate a year earlier -> no ex-post value
    cpi = {"2024-01": 100.0, "2025-01": 150.0}
    assert e.ex_post_real_rates(rates, cpi) == {}
    assert close(e.trailing_real_rates(rates, cpi)["2025-01"], 0.0)   # 1.5/1.5 - 1


# --- index paths for asset detail charts ------------------------------------

def test_index_paths_start_at_100_and_match_windows():
    # Asset doubles, CPI +60 %, USD/TRY +25 % over one year (same as test_asset_windows_known_values).
    asset = {"2024-06": 100.0, "2025-06": 200.0}
    cpi = {"2024-06": 1000.0, "2025-06": 1600.0}
    fx = {"2024-06": 32.0, "2025-06": 40.0}
    # Fill the months in between so the path is contiguous (values don't matter for the ends).
    for k in range(1, 12):
        m = e.shift_month("2024-06", k)
        asset[m], cpi[m], fx[m] = 150.0, 1300.0, 36.0
    p = e.index_paths(asset, cpi, fx, "2025-06", 1)
    assert p["months"][0] == "2024-06" and p["months"][-1] == "2025-06" and len(p["months"]) == 13
    assert p["nominal"][0] == p["real"][0] == p["usd"][0] == 100.0
    assert close(p["nominal"][-1], 200.0)          # 100 * 200/100
    assert close(p["real"][-1], 125.0)             # 100 * (2.0 / 1.6)
    assert close(p["usd"][-1], 160.0)              # 100 * (2.0 / 1.25)


def test_index_paths_require_contiguous_months():
    asset = {"2024-06": 100.0, "2025-06": 200.0}   # 11 months missing
    with pytest.raises(e.SeriesError):
        e.index_paths(asset, asset, asset, "2025-06", 1)


# --- ratio charts: "X priced in Y" ------------------------------------------

def test_ratio_index_rebases_to_100():
    # X doubles in TL, Y (e.g. gold) goes up 4x -> X in Y terms halves: 100 -> 50
    x = {"2024-01": 10.0, "2024-02": 15.0, "2024-03": 20.0}
    y = {"2024-01": 2.0, "2024-02": 4.0, "2024-03": 8.0}
    out = e.ratio_index(x, y, "2024-01", "2024-03")
    assert out["months"] == ["2024-01", "2024-02", "2024-03"]
    assert out["values"] == [100.0, 75.0, 50.0]      # 100*(15/4)/(10/2) = 75


def test_ratio_index_needs_every_month():
    with pytest.raises(e.SeriesError):
        e.ratio_index({"2024-01": 1.0, "2024-03": 1.0}, {"2024-01": 1.0, "2024-02": 1.0, "2024-03": 1.0}, "2024-01", "2024-03")


# --- rent vs buy -------------------------------------------------------------

def test_mortgage_payment_textbook():
    # 1000 at 1 %/month over 12 months: 1000*0.01/(1-1.01**-12) = 88.8487886...
    assert close(e.mortgage_payment(1000, 0.01, 12), 1000 * 0.01 / (1 - 1.01 ** -12))
    assert close(e.mortgage_payment(1200, 0.0, 12), 100.0)    # zero rate: straight division


def _rvb(**kw):
    p = dict(price=1200.0, rent=10.0, down_share=1.0, loan_rate_monthly=0.0, loan_months=12,
             house_growth=0.0, rent_growth=0.0, invest_return=0.0, inflation=0.0,
             buy_cost=0.0, sell_cost=0.0, upkeep=0.0, years=1)
    p.update(kw)
    return e.rent_vs_buy(**p)


def test_rent_vs_buy_cash_no_growth():
    # Buyer pays 1200 cash, owns a 1200 house. Renter keeps 1200 but pays 12 x 10 rent -> 1080.
    r = _rvb()
    assert close(r["buy_wealth"], 1200.0) and close(r["rent_wealth"], 1080.0)
    assert r["breakeven_year"] == 1


def test_rent_vs_buy_investment_return():
    # No rent, 12 %/year on the renter's 1200 -> 1344 after a year; house flat -> buyer 1200.
    r = _rvb(rent=0.0, invest_return=0.12)
    assert close(r["rent_wealth"], 1344.0, tol=1e-9) and close(r["buy_wealth"], 1200.0)
    assert r["breakeven_year"] is None


def test_rent_vs_buy_mortgage_fully_repaid():
    # 50 % down, rest at 0 % over 12 months: buyer pays 50/month; renter invests the 600 down payment
    # and pays 10 rent while the buyer pays 50 -> renter adds 40/month: 600 + 12*40 = 1080.
    r = _rvb(down_share=0.5)
    assert close(r["buy_wealth"], 1200.0) and close(r["rent_wealth"], 1080.0)


def test_rent_vs_buy_costs_and_real_terms():
    # 4 % purchase cost, 2 % selling cost, 10 % inflation, cash, no rent, nothing else moves:
    # buyer: 1200*(1-0.02) = 1176; renter keeps 1200 + 48 (the purchase cost he didn't pay) = 1248.
    r = _rvb(rent=0.0, buy_cost=0.04, sell_cost=0.02, inflation=0.10)
    assert close(r["buy_wealth"], 1176.0) and close(r["rent_wealth"], 1248.0)
    assert close(r["buy_wealth_real"], 1176.0 / 1.10) and close(r["rent_wealth_real"], 1248.0 / 1.10)


def test_rent_steps_up_once_a_year():
    # 2 years, rent 10 rising 50 % after year one: rents = 12*10 + 12*15 = 300 -> renter 1200 - 300.
    r = _rvb(rent_growth=0.5, years=2, loan_months=12)
    assert close(r["rent_wealth"], 900.0)
    assert len(r["yearly"]) == 2 and close(r["yearly"][0]["rent_wealth"], 1080.0)


def test_breakeven_means_buying_stays_ahead():
    # Cash purchase, house +30 %/yr, renter earns 50 %/yr on 1200 with no rent:
    # renter ahead every year -> None. With 0 % return the buyer is ahead from year 1.
    assert _rvb(rent=0.0, house_growth=0.30, invest_return=0.50, years=3)["breakeven_year"] is None
    assert _rvb(rent=0.0, house_growth=0.30, years=3)["breakeven_year"] == 1


# --- price basket index (new-car list prices) --------------------------------

def test_jevons_chain_geometric_mean_of_relatives():
    # model A 100 -> 110 (x1.1), model B 200 -> 180 (x0.9): sqrt(1.1*0.9) = sqrt(0.99)
    idx = e.jevons_chain_index({"2024-01": {"A": 100, "B": 200}, "2024-02": {"A": 110, "B": 180}})
    assert idx["2024-01"] == 100.0
    assert close(idx["2024-02"], 100 * math.sqrt(0.99))


def test_jevons_new_model_counts_only_from_its_second_month():
    prices = {
        "2024-01": {"A": 100},
        "2024-02": {"A": 110, "C": 500},     # C enters: no relative yet -> index 110
        "2024-03": {"A": 110, "C": 550},     # A flat, C x1.1 -> sqrt(1.0*1.1)
    }
    idx = e.jevons_chain_index(prices)
    assert close(idx["2024-02"], 110.0)
    assert close(idx["2024-03"], 110.0 * math.sqrt(1.1))


def test_jevons_chains_over_months():
    idx = e.jevons_chain_index({"2024-01": {"A": 100}, "2024-02": {"A": 150}, "2024-03": {"A": 200}})
    assert close(idx["2024-03"], 200.0)


def test_jevons_rejects_gaps_and_no_overlap():
    with pytest.raises(e.SeriesError):
        e.jevons_chain_index({"2024-01": {"A": 100}, "2024-03": {"A": 120}})
    with pytest.raises(e.SeriesError):
        e.jevons_chain_index({"2024-01": {"A": 100}, "2024-02": {"B": 120}})


# --- co-movement (İlişkiler) -------------------------------------------------

def test_pearson_known_values():
    assert close(e.pearson([1, 2, 3], [2, 4, 6]), 1.0)
    assert close(e.pearson([1, 2, 3], [3, 2, 1]), -1.0)
    # dx = dy pattern (-1.5,-.5,.5,1.5) vs (-1.5,.5,-.5,1.5): sum 4 / sqrt(5*5) = 0.8
    assert close(e.pearson([1, 2, 3, 4], [1, 3, 2, 4]), 0.8)


def test_pearson_rejects_flat_or_short():
    with pytest.raises(e.SeriesError):
        e.pearson([1, 1, 1], [1, 2, 3])
    with pytest.raises(e.SeriesError):
        e.pearson([1, 2], [1, 2])


def test_paired_changes_level_vs_rate():
    a = {"2024-01": 100.0, "2024-02": 110.0, "2024-03": 121.0}   # level: % change
    b = {"2024-01": 10.0, "2024-02": 12.0, "2024-03": 11.0}      # rate: point change
    p = e.paired_changes(a, b, "level", "rate", 1)
    assert p["months"] == ["2024-02", "2024-03"]
    assert all(close(x, 0.1) for x in p["a"])
    assert p["b"] == [2.0, -1.0]


def test_paired_changes_quarterly_alignment():
    a = {e.shift_month("2024-01", k): 100.0 + k for k in range(6)}   # monthly 2024-01..06
    b = {"2024-03": 5.0, "2024-06": 4.0}                             # quarterly
    p = e.paired_changes(a, b, "level", "rate", 3)
    assert p["months"] == ["2024-06"]
    assert close(p["a"][0], 105.0 / 102.0 - 1) and p["b"] == [-1.0]


def test_rolling_correlation():
    p = {"months": ["m1", "m2", "m3", "m4"], "a": [1, 2, 3, 4], "b": [2, 4, 6, 1]}
    out = e.rolling_correlation(p, 3)
    assert list(out) == ["m3", "m4"]
    assert close(out["m3"], 1.0)
    assert close(out["m4"], e.pearson([2, 3, 4], [4, 6, 1]))


def test_same_direction_share():
    # signs: (+,+) (-,+) (+,+) (0,-) -> same in 2 of 4 (zero counts as not same)
    p = {"months": ["a", "b", "c", "d"], "a": [1, -1, 2, 0], "b": [3, 2, 1, -1]}
    assert e.same_direction_share(p) == 0.5


# --- portfolio (Portföyüm) ---------------------------------------------------

def _lot(**kw):
    p = dict(amount=1000.0, quantity=None, level_then=10.0, level_now=20.0,
             cpi_then=100.0, cpi_now=150.0, usd_then=10.0, usd_now=16.0, gold_then=100.0, gold_now=250.0)
    p.update(kw)
    return e.holding_returns(**p)


def test_holding_returns_from_amount():
    # 1000 TL bought at level 10 -> now 20: value 2000 (+100 %).
    # Real: 2000 / (1000*1.5) - 1 = 1/3. USD: (2000/16)/(1000/10) - 1 = 0.25. Gold: (2000/250)/(1000/100) - 1 = -0.2
    r = _lot()
    assert close(r["value"], 2000.0)
    assert close(r["nominal"], 1.0)
    assert close(r["real"], 2000 / 1500 - 1)
    assert close(r["usd"], 0.25)
    assert close(r["gold"], -0.2)
    assert close(r["inflation_gap_tl"], 500.0)        # 2000 - 1000*1.5


def test_holding_returns_from_quantity():
    # 40 units at today's level 20 -> 800 TL, paid 1000 -> -20 %
    r = _lot(quantity=40.0)
    assert close(r["value"], 800.0) and close(r["nominal"], -0.2)


def test_portfolio_summary_weights_by_money():
    a = _lot()                                   # cost 1000 -> 2000, cpi-adjusted cost 1500
    b = _lot(amount=3000.0, level_now=10.0)      # cost 3000 -> 3000, cpi-adjusted cost 4500
    s = e.portfolio_summary([a, b])
    assert close(s["cost"], 4000.0) and close(s["value"], 5000.0)
    assert close(s["nominal"], 0.25)
    assert close(s["real"], 5000 / 6000 - 1)     # value / sum of inflated costs
    assert close(s["inflation_gap_tl"], -1000.0)


# --- loan true cost (KKDF, BSMV, fees) ----------------------------------------

def test_amortization_without_taxes_is_plain_annuity():
    rows = e.amortization(1000, 0.01, 12)
    a = 1000 * 0.01 / (1 - 1.01 ** -12)
    assert all(close(r["installment"], a, tol=1e-9) for r in rows)
    assert close(rows[0]["interest"], 10.0) and close(rows[-1]["balance"], 0.0, tol=1e-9)


def test_amortization_taxes_on_interest():
    # Taxes are charged on each interest payment: installment = annuity at r*(1+kkdf+bsmv)
    rows = e.amortization(1000, 0.01, 12, kkdf=0.15, bsmv=0.15)
    a = 1000 * 0.013 / (1 - 1.013 ** -12)
    assert close(rows[0]["installment"], a, tol=1e-9)
    assert close(rows[0]["kkdf"], 1.5) and close(rows[0]["bsmv"], 1.5)       # 15 % of 10 TL interest
    assert close(sum(r["principal"] for r in rows), 1000.0, tol=1e-9)


def test_irr_closed_form():
    # receive 900, pay 500 twice: 500x^2 + 500x - 900 = 0, x = 1/(1+i)
    x = (-500 + math.sqrt(500 ** 2 + 4 * 500 * 900)) / (2 * 500)
    assert close(e.irr([900, -500, -500]), 1 / x - 1, tol=1e-10)
    with pytest.raises(e.SeriesError):
        e.irr([100, 50])                      # no sign change -> no rate


def test_loan_cost_fee_raises_effective_rate():
    r = e.loan_cost(principal=1000, monthly_rate=0.0, months=2, kkdf=0.0, bsmv=0.0,
                    upfront_fees=100, monthly_fees=0.0, inflation=0.0)
    x = (-500 + math.sqrt(500 ** 2 + 4 * 500 * 900)) / 1000
    assert close(r["monthly_cost"], 1 / x - 1, tol=1e-10)
    assert close(r["annual_cost"], (1 / x) ** 12 - 1, tol=1e-9)
    assert r["advertised_annual"] == 0.0
    assert close(r["total_paid"], 1100.0)


def test_loan_cost_zero_everything():
    r = e.loan_cost(principal=1200, monthly_rate=0.0, months=12, kkdf=0, bsmv=0, upfront_fees=0, monthly_fees=0, inflation=0.1)
    assert close(r["annual_cost"], 0.0, tol=1e-9) and close(r["real_annual_cost"], 1 / 1.1 - 1, tol=1e-9)


# --- installment vs cash ------------------------------------------------------

def test_installment_vs_cash_hidden_rate():
    # Cash 900 or 2 x 500 starting next month: hidden monthly rate solves the same quadratic.
    r = e.installment_vs_cash(cash_price=900, installment=500, count=2, first_offset=1,
                              annual_discount=0.0, inflation=0.0)
    x = (-500 + math.sqrt(500 ** 2 + 4 * 500 * 900)) / 1000
    assert close(r["hidden_monthly_rate"], 1 / x - 1, tol=1e-10)
    assert close(r["pv_installments"], 1000.0) and r["cheaper"] == "cash"


def test_zero_interest_installments_win_with_positive_discount():
    r = e.installment_vs_cash(cash_price=1200, installment=100, count=12, first_offset=1,
                              annual_discount=0.12, inflation=0.0)
    m = 1.12 ** (1 / 12) - 1
    assert close(r["pv_installments"], sum(100 / (1 + m) ** k for k in range(1, 13)))
    assert r["cheaper"] == "installments" and r["hidden_monthly_rate"] == 0.0


# --- real salary ----------------------------------------------------------------

def test_salary_analysis():
    cpi = {"2023-01": 100.0, "2024-01": 150.0, "2025-01": 180.0}
    usd = {"2023-01": 20.0, "2024-01": 30.0, "2025-01": 36.0}
    out = e.salary_analysis({"2023-01": 10000.0, "2024-01": 14000.0}, cpi, "2025-01", usd=usd)
    first, second = out["rows"]
    assert close(first["today_tl"], 18000.0)                 # 10000 * 180/100
    assert close(second["raise_nominal"], 0.4)
    assert close(second["raise_real"], 1.4 / 1.5 - 1)        # raise lost to 50 % inflation
    assert close(first["usd"], 500.0)
    assert close(out["real_change_total"], 14000 * 180 / 150 / 18000 - 1)


# --- event study ----------------------------------------------------------------

def test_event_study_level_and_rate():
    s = {e.shift_month("2024-01", k): 100.0 + 10 * k for k in range(8)}   # 100,110,...,170
    out = e.event_study(s, "level", ["2024-04"], before=1, after=2)
    # base = month before event (2024-03 = 120): offsets -1..2 -> 120,130,140,150
    assert out["offsets"] == [-1, 0, 1, 2]
    assert out["mean"][0] == 0.0 and close(out["mean"][3], 150 / 120 - 1)
    r = e.event_study(s, "rate", ["2024-04", "2024-05"], before=1, after=1)
    assert r["n"] == 2 and r["mean"] == [0.0, 10.0, 20.0]
    assert e.event_study(s, "rate", ["2024-08"], before=1, after=1)["n"] == 0   # not enough data after


def test_derive_rate_events():
    pr = {"2024-01": 45.0, "2024-02": 45.0, "2024-03": 50.0, "2024-04": 47.5}
    ev = e.derive_rate_events(pr, threshold=1.0)
    assert ev == [{"month": "2024-03", "change": 5.0, "type": "hike"},
                  {"month": "2024-04", "change": -2.5, "type": "cut"}]
