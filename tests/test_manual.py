"""Tests for manual CSV import (data/manual/<series>.csv)."""

import math

import pytest

from pipeline import manual


def test_simple_month_value():
    assert manual.parse_csv("month,value\n2024-01,100\n2024-02,101.5\n") == {"2024-01": 100.0, "2024-02": 101.5}


def test_evds_style_semicolon_decimal_comma_and_short_month():
    # EVDS web export: "Tarih;TP_XXX" with "2024-1" and decimal commas
    text = "Tarih;TP_FG_J0\n2024-1;2.000,50\n2024-2;2.050,25\n"
    assert manual.parse_csv(text) == {"2024-01": 2000.5, "2024-02": 2050.25}


def test_daily_values_are_averaged_per_month():
    text = "Tarih,TP_DK_USD_A_YTL\n01-01-2024,30\n02-01-2024,32\n01-02-2024,31\n"
    out = manual.parse_csv(text)
    assert out == {"2024-01": 31.0, "2024-02": 31.0}


def test_other_date_formats():
    text = "date,v\n2024-03-15,10\n15.04.2024,20\n05-2024,30\n2024/06,40\n"
    assert manual.parse_csv(text) == {"2024-03": 10.0, "2024-04": 20.0, "2024-05": 30.0, "2024-06": 40.0}


def test_skips_blank_and_missing_values():
    text = "Tarih,v\n2024-01,10\n2024-02,\n2024-03,ND\n\n2024-04,12\n"
    assert manual.parse_csv(text) == {"2024-01": 10.0, "2024-04": 12.0}


def test_no_header_is_fine():
    assert manual.parse_csv("2024-01,5\n2024-02,6\n") == {"2024-01": 5.0, "2024-02": 6.0}


def test_rejects_garbage_dates():
    with pytest.raises(manual.ManualDataError):
        manual.parse_csv("Tarih,v\nbugün,5\n")


def test_number_parsing():
    assert manual.parse_number("1.234,5") == 1234.5
    assert manual.parse_number("1,234.5") == 1234.5
    assert manual.parse_number("45,25") == 45.25
    assert manual.parse_number("45.25") == 45.25
    assert manual.parse_number("1.000") == 1000.0     # thousands, Turkish style
    assert math.isnan(manual.parse_number("ND"))
