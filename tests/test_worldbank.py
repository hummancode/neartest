"""World Bank fetch parsing (no network: a fixture in the API's JSON shape)."""

import pytest

from pipeline import worldbank as wb

FIXTURE = [
    {"page": 1, "pages": 1, "per_page": 2000, "total": 4},
    [
        {"indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation, consumer prices (annual %)"},
         "country": {"id": "TR", "value": "Turkiye"}, "countryiso3code": "TUR", "date": "2024", "value": 58.5},
        {"indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation, consumer prices (annual %)"},
         "country": {"id": "TR", "value": "Turkiye"}, "countryiso3code": "TUR", "date": "2023", "value": 53.9},
        {"indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation, consumer prices (annual %)"},
         "country": {"id": "BR", "value": "Brazil"}, "countryiso3code": "BRA", "date": "2024", "value": None},
        {"indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation, consumer prices (annual %)"},
         "country": {"id": "BR", "value": "Brazil"}, "countryiso3code": "BRA", "date": "2023", "value": 4.6},
    ],
]


def test_parse_keeps_values_and_skips_nulls():
    out = wb.parse(FIXTURE, "FP.CPI.TOTL.ZG", "Inflation, consumer prices")
    assert out == {"TUR": {"2023": 53.9, "2024": 58.5}, "BRA": {"2023": 4.6}}


def test_parse_rejects_wrong_indicator_name():
    with pytest.raises(wb.WorldBankError):
        wb.parse(FIXTURE, "FP.CPI.TOTL.ZG", "GDP growth")


def test_parse_rejects_api_error_message():
    with pytest.raises(wb.WorldBankError):
        wb.parse([{"message": [{"id": "120", "value": "Invalid value"}]}], "X", "Y")
