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
