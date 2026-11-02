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


# --- credit card minimum payment -----------------------------------------------

def test_card_minimum_payoff_zero_interest():
    # 1000 TL, pay half (at least 100) each month: 500, 250, 125, 100, 25 -> 5 months
    r = e.card_minimum_payoff(balance=1000, monthly_rate=0.0, kkdf=0, bsmv=0, min_share=0.5, min_floor=100)
    assert r["months"] == 5 and r["paid_off"] and close(r["total_paid"], 1000.0)
    assert [round(b, 6) for b in r["balances"]] == [1000.0, 500.0, 250.0, 125.0, 25.0, 0.0]


def test_card_full_payment_pays_one_month_interest():
    r = e.card_minimum_payoff(balance=1000, monthly_rate=0.1, kkdf=0.15, bsmv=0.15, min_share=1.0, min_floor=0)
    assert r["months"] == 1 and close(r["total_interest"], 100.0) and close(r["total_tax"], 30.0)


def test_card_minimum_never_pays_off_when_below_interest():
    # 5 % of (balance x 1.1) < interest -> balance grows; stops at max_months
    r = e.card_minimum_payoff(balance=1000, monthly_rate=0.1, kkdf=0, bsmv=0, min_share=0.05, min_floor=0, max_months=24)
    assert not r["paid_off"] and r["months"] == 24 and r["balances"][-1] > 1000


# --- loan restructuring -------------------------------------------------------------

def _refi(**kw):
    p = dict(balance=1200.0, rate_old=0.0, months_old=12, rate_new=0.0, months_new=24, kkdf=0.0, bsmv=0.0,
             prepay_penalty=0.0, new_fees=0.0, fees_financed=False, annual_discount=0.0)
    p.update(kw)
    return e.refinance_compare(**p)


def test_refinance_longer_term_same_cost_at_zero_rates():
    r = _refi()
    assert close(r["old_payment"], 100.0) and close(r["new_payment"], 50.0)
    assert close(r["pv_old"], 1200.0) and close(r["pv_new"], 1200.0) and r["better"] == "equal"


def test_refinance_cheaper_rate_wins_and_penalty_counts():
    r = _refi(rate_old=0.01, months_new=12)
    old = 1200 * 0.01 / (1 - 1.01 ** -12)
    assert close(r["old_payment"], old) and close(r["saving_pv"], 12 * old - 1200) and r["better"] == "new"
    p = _refi(rate_old=0.01, months_new=12, prepay_penalty=0.02, new_fees=50, fees_financed=True)
    assert close(p["new_principal"], 1200 * 1.02 + 50) and close(p["new_payment"], (1224 + 50) / 12)


# --- deposit net return, savings goal, half-life ---------------------------------------

def test_deposit_net_one_year():
    r = e.deposit_net(principal=100000, gross_annual=0.50, days=365, withholding=0.10, inflation=0.0)
    assert close(r["net_interest_term"], 45000.0) and close(r["net_annual"], 0.45)


def test_deposit_net_monthly_rollover_compounds():
    r = e.deposit_net(principal=100000, gross_annual=0.50, days=30, withholding=0.10, inflation=0.40)
    term = 0.50 * 30 / 365 * 0.9
    assert close(r["net_annual"], (1 + term) ** (365 / 30) - 1)
    assert close(r["real_annual"], (1 + r["net_annual"]) / 1.40 - 1)


def test_required_saving_simple():
    assert close(e.required_saving(target_today=1200, years=1, inflation=0, nominal_return=0, current=0,
                                   grow_with_inflation=False)["monthly"], 100.0)
    assert close(e.required_saving(target_today=1200, years=1, inflation=0, nominal_return=0, current=600,
                                   grow_with_inflation=False)["monthly"], 50.0)
    assert e.required_saving(target_today=1000, years=1, inflation=0, nominal_return=0.5, current=1000,
                             grow_with_inflation=False)["monthly"] == 0.0


def test_required_saving_reaches_target():
    r = e.required_saving(target_today=100000, years=3, inflation=0.3, nominal_return=0.4, current=5000, grow_with_inflation=True)
    mi, mr = 1.3 ** (1 / 12) - 1, 1.4 ** (1 / 12) - 1
    fv = 5000 * (1 + mr) ** 36 + sum(r["monthly"] * (1 + mi) ** (t - 1) * (1 + mr) ** (36 - t) for t in range(1, 37))
    assert close(fv, 100000 * 1.3 ** 3, tol=1e-6)


def test_half_life():
    assert close(e.half_life_years(1.0), 1.0)                # 100 % inflation halves money in a year
    assert close(e.half_life_years(0.5), math.log(2) / math.log(1.5))
    with pytest.raises(e.SeriesError):
        e.half_life_years(0.0)


def test_breakeven_gross_rate_round_trips():
    g = e.breakeven_gross_rate(inflation=0.40, days=30, withholding=0.10)
    r = e.deposit_net(principal=1, gross_annual=g, days=30, withholding=0.10, inflation=0.40)
    assert close(r["real_annual"], 0.0, tol=1e-12)
    assert close(e.breakeven_gross_rate(inflation=0.45, days=365, withholding=0.10), 0.5)   # 0.45 / 0.9


# --- province wealth estimate (model, not an official statistic) -----------------

def test_province_wealth_hand_case():
    # 1000 people / 4 = 250 households; 60 % own -> 150 x 100 m² x 10.000 TL = 150 M TL housing;
    # deposits 50 M x 50 % household share = 25 M TL financial; total 175 M.
    r = e.province_wealth(population=1000, deposits_tl=50e6, m2_price=10000, household_size=4,
                          ownership_rate=0.6, dwelling_m2=100, household_deposit_share=0.5)
    assert close(r["households"], 250.0)
    assert close(r["housing"], 150e6) and close(r["financial"], 25e6) and close(r["total"], 175e6)
    assert close(r["per_household"], 700000.0) and close(r["per_capita"], 175000.0)


def test_province_wealth_rejects_bad_inputs():
    with pytest.raises(e.SeriesError):
        e.province_wealth(population=0, deposits_tl=1, m2_price=1, household_size=3, ownership_rate=0.5,
                          dwelling_m2=100, household_deposit_share=0.5)
    with pytest.raises(e.SeriesError):
        e.province_wealth(population=10, deposits_tl=1, m2_price=1, household_size=3, ownership_rate=1.5,
                          dwelling_m2=100, household_deposit_share=0.5)


# --- distributions: normal CDF / inverse, lognormal inequality ---------------------

def test_normal_cdf_and_inverse():
    assert close(e.normal_cdf(0.0), 0.5)
    assert close(e.normal_cdf(1.959963984540054), 0.975, tol=1e-9)
    for p in (0.001, 0.025, 0.3, 0.5, 0.8, 0.999):
        assert close(e.normal_cdf(e.normal_ppf(p)), p, tol=1e-9)


def test_lognormal_gini_round_trip():
    # Gini of a lognormal is 2*Phi(sigma/sqrt2) - 1; sigma = 1 -> 2*Phi(0.7071) - 1 = 0.5205
    assert close(e.gini_from_sigma(1.0), 2 * e.normal_cdf(1 / math.sqrt(2)) - 1)
    assert close(e.sigma_from_gini(e.gini_from_sigma(0.8)), 0.8, tol=1e-9)


def test_top_share_lognormal():
    # sigma -> 0 means perfect equality: top 10 % holds 10 %
    assert close(e.top_share_lognormal(1e-9, 0.10), 0.10, tol=1e-6)
    # known: sigma = 1, top 10 % share = 1 - Phi(Phi^-1(0.9) - 1) = 1 - Phi(0.2816) = 0.389
    assert close(e.top_share_lognormal(1.0, 0.10), 1 - e.normal_cdf(e.normal_ppf(0.9) - 1.0), tol=1e-12)


def test_wealth_inequality_from_income_gini():
    r = e.wealth_inequality(income_gini=0.40, multiplier=1.0)
    assert close(r["wealth_gini"], 0.40, tol=1e-9)           # multiplier 1: same dispersion as income
    r2 = e.wealth_inequality(income_gini=0.40, multiplier=1.8)
    assert r2["wealth_gini"] > 0.40 and r2["top10_share"] > r["top10_share"]
    assert close(r2["median_to_mean"], math.exp(-r2["sigma_wealth"] ** 2 / 2))


# --- gold allocation and housing affordability ------------------------------------

def test_gold_allocation():
    # beta 0: by household count only -> 1:3 split of 400 g
    assert e.gold_allocation([100, 300], [5.0, 1.0], beta=0.0, total=400.0) == [100.0, 300.0]
    # beta 1: by total wealth (households x wealth): 500 vs 300 -> 250 / 150
    out = e.gold_allocation([100, 300], [5.0, 1.0], beta=1.0, total=400.0)
    assert close(out[0], 250.0) and close(out[1], 150.0)


def test_housing_affordability():
    # 100 m2 at 20.000 TL/m2 = 2M TL; rent 100 TL/m2 -> 10.000/month -> 6 % gross yield, 16.7 years;
    # wage 25.000/month -> 2M / 300k = 6.67 years of salary; rent / wage = 40 %
    r = e.housing_affordability(m2_price=20000, rent_m2=100, monthly_wage=25000, dwelling_m2=100)
    assert close(r["gross_yield"], 0.06) and close(r["amortization_years"], 2e6 / 120000)
    assert close(r["price_to_annual_wage"], 2e6 / 300000) and close(r["rent_to_wage"], 0.4)


# --- economic structure: shares, specialization, concentration ---------------------

def test_shares():
    assert e.shares({"a": 30.0, "b": 10.0}) == {"a": 0.75, "b": 0.25}
    with pytest.raises(e.SeriesError):
        e.shares({"a": 0.0})


def test_location_quotients():
    # province: industry 50 %, services 50 %; country: industry 25 %, services 75 %
    lq = e.location_quotients({"ind": 0.5, "srv": 0.5}, {"ind": 0.25, "srv": 0.75})
    assert close(lq["ind"], 2.0) and close(lq["srv"], 2 / 3)


def test_hhi():
    assert close(e.hhi({"a": 1.0}), 1.0)                     # one sector: fully concentrated
    assert close(e.hhi({"a": 0.5, "b": 0.5}), 0.5)
    assert close(e.hhi({k: 0.1 for k in "abcdefghij"}), 0.1)  # ten equal sectors


def test_lorenz_lognormal():
    # sigma -> 0: perfect equality, L(p) = p
    assert close(e.lorenz_lognormal(0.3, 1e-12), 0.3, tol=1e-9)
    # L(0.5) for sigma = 1 is Phi(0 - 1) = Phi(-1) = 0.158655...
    assert close(e.lorenz_lognormal(0.5, 1.0), 0.15865525393145707, tol=1e-9)
    assert e.lorenz_lognormal(0.0, 1.0) == 0.0 and e.lorenz_lognormal(1.0, 1.0) == 1.0


# --- population growth windows ------------------------------------------------

def test_growth_windows_hand_computed():
    pts = {"2014": 100.0, "2019": 110.0, "2023": 121.0, "2024": 133.1}
    g = e.growth_windows(pts, (1, 5, 10))
    # 1 y: 121 -> 133.1 = +12.1 = +10 %
    assert g[1]["from"] == "2023" and g[1]["to"] == "2024"
    assert close(g[1]["change"], 12.1, 1e-9) and close(g[1]["change_pct"], 10.0, 1e-9) and close(g[1]["annual_pct"], 10.0, 1e-9)
    # 5 y: 110 -> 133.1 = 1.21 = 1.1² -> annual 1.1^(2/5) - 1
    assert close(g[5]["change_pct"], 21.0, 1e-9) and close(g[5]["annual_pct"], 100 * (1.1 ** 0.4 - 1), 1e-9)
    # 10 y: 100 -> 133.1 = 1.1³ -> annual 1.1^(3/10) - 1
    assert close(g[10]["change_pct"], 33.1, 1e-9) and close(g[10]["annual_pct"], 100 * (1.1 ** 0.3 - 1), 1e-9)


def test_growth_windows_shrinking_and_missing_base():
    g = e.growth_windows({"2019": 1000.0, "2024": 900.0}, (1, 5))
    assert 1 not in g                                  # no 2023 value
    assert close(g[5]["change"], -100.0) and close(g[5]["change_pct"], -10.0, 1e-9)
    assert close(g[5]["annual_pct"], 100 * (0.9 ** 0.2 - 1), 1e-9)
    assert e.growth_windows({}, (1,)) == {}
    assert e.growth_windows({"2023": 0.0, "2024": 5.0}, (1,)) == {}   # zero base: undefined


# --- Big Mac index -------------------------------------------------------------

def test_big_mac_valuation_turkey_july_2026():
    # The Economist, 2026-07: Türkiye 325 TL, USD/TRY 47.0275, ABD 6.22 $.
    # dollar price = 325 / 47.0275 = 6.91085…; implied rate = 325 / 6.22 = 52.2508…;
    # valuation = 52.2508 / 47.0275 − 1 = +0.11107 (the published USD_raw value).
    b = e.big_mac(local_price=325, fx=47.0275, us_price=6.22)
    assert close(b["dollar_price"], 6.910850034550, 1e-9)
    assert close(b["implied_rate"], 52.250803858521, 1e-9)
    assert abs(b["valuation"] - 0.11107) < 5e-6


def test_big_mac_us_is_zero_and_undervalued_is_negative():
    assert e.big_mac(local_price=6.22, fx=1.0, us_price=6.22)["valuation"] == 0.0
    # 100 local, 50 per $, US 4 $: dollar price 2 $ -> half the US price -> −50 %
    b = e.big_mac(local_price=100, fx=50, us_price=4)
    assert close(b["dollar_price"], 2.0) and close(b["implied_rate"], 25.0) and close(b["valuation"], -0.5)
    with pytest.raises(e.SeriesError):
        e.big_mac(local_price=100, fx=0, us_price=4)


# --- change over n periods (quarterly/monthly series) --------------------------

def test_change_over_quarters_hand_computed():
    # 9 quarters: 100 … 121; 4 quarters back from the last (121) is 110 -> +10 %; 8 back is 100 -> +21 %, annual 10 %
    pts = [100.0, 102.0, 104.0, 106.0, 110.0, 113.0, 115.0, 118.0, 121.0]
    a = e.change_over(pts, periods_back=4, periods_per_year=4)
    assert close(a["change_pct"], 100 * (121 / 110 - 1), 1e-9) and close(a["annual_pct"], a["change_pct"], 1e-9)
    b = e.change_over(pts, periods_back=8, periods_per_year=4)
    assert close(b["change_pct"], 21.0, 1e-9) and close(b["annual_pct"], 10.0, 1e-9)
    assert e.change_over(pts, periods_back=9, periods_per_year=4) is None     # not enough history


def test_drawdown_from_peak():
    # peak 216.6, last 211.2 -> 211.2/216.6 − 1
    d = e.drawdown([98.7, 150.0, 216.6, 211.2])
    assert close(d["peak"], 216.6) and d["peak_index"] == 2 and close(d["drawdown_pct"], 100 * (211.2 / 216.6 - 1), 1e-9)
    assert e.drawdown([1.0, 2.0])["drawdown_pct"] == 0.0
