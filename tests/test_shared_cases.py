"""Run tests/cases.json against the Python engine.

The same file is run against the TypeScript port (site/tests/engine.test.ts),
so both implementations are held to identical, hand-computed expectations.
"""

import dataclasses
import json
import math
from pathlib import Path

import pytest

from reel import engine as e

CASES = json.loads((Path(__file__).parent / "cases.json").read_text())["cases"]


def expand(arg):
    """Turn {"$flat": [start, months, start_value, monthly_growth]} into a series."""
    if isinstance(arg, dict) and "$flat" in arg:
        start, months, value, growth = arg["$flat"]
        out = {}
        for k in range(months + 1):
            out[e.shift_month(start, k)] = value
            value *= 1 + growth
        return out
    return arg


def call(fn, args):
    args = [expand(a) for a in args]
    if fn in ("rent_vs_buy", "holding_returns", "loan_cost", "installment_vs_cash", "card_minimum_payoff",
              "refinance_compare", "deposit_net", "required_saving", "breakeven_gross_rate", "province_wealth", "wealth_inequality", "housing_affordability", "rental_income_tax"):
        return getattr(e, fn)(**args[0])
    if fn == "gold_allocation":
        return e.gold_allocation(args[0], args[1], **args[2])
    if fn == "asset_windows":
        if len(args) == 5:
            args[4] = tuple(args[4])
        return [dataclasses.asdict(w) for w in e.asset_windows(*args)]
    return getattr(e, fn)(*args)


def matches(actual, expected, tol, subset=False):
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        return actual == expected
    if isinstance(expected, (int, float)):
        return isinstance(actual, (int, float)) and math.isclose(actual, expected, rel_tol=0, abs_tol=tol)
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            matches(a, x, tol) for a, x in zip(actual, expected))
    if isinstance(expected, dict):
        # Window rows: expected keys are a subset. Plain series: keys must match exactly.
        if isinstance(actual, dict) and not subset and "years" not in expected and set(actual) != set(expected):
            return False
        return isinstance(actual, dict) and all(k in actual and matches(actual[k], v, tol) for k, v in expected.items())
    raise TypeError(expected)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_case(case):
    if case.get("raises"):
        with pytest.raises(e.SeriesError):
            call(case["fn"], case["args"])
    else:
        assert matches(call(case["fn"], case["args"]), case["expect"], case["tol"], case.get("subset", False))
