"""EVDS date parsing (no network)."""

import pytest

from pipeline import fetch


@pytest.mark.parametrize("raw,expected", [
    ("2024-1", "2024-01"),        # monthly
    ("2024-12", "2024-12"),
    ("15-03-2024", "2024-03"),    # daily
    ("2024-Q1", "2024-03"),       # quarterly -> quarter-end month
    ("2024Q4", "2024-12"),
    ("2024-S1", "2024-06"),       # semiannual
    ("2024", "2024-12"),          # annual -> December
])
def test_parse_evds_date(raw, expected):
    assert fetch.parse_evds_date(raw) == expected


def test_parse_evds_date_rejects_garbage():
    with pytest.raises(ValueError):
        fetch.parse_evds_date("dün")


def test_frequency_codes():
    assert fetch.frequency_for({"freq": "Q"}) == 6
    assert fetch.frequency_for({"freq": "A"}) == 8
    assert fetch.frequency_for({}) == 5
