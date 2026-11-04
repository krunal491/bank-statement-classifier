from datetime import date

import pytest

from src.utils import is_amount, parse_amount, parse_date


@pytest.mark.parametrize("text, expected", [
    ("01/04/2024", date(2024, 4, 1)),
    ("01-04-24", date(2024, 4, 1)),
    ("01 Apr 2024", date(2024, 4, 1)),
    ("01-APR-2024", date(2024, 4, 1)),
    ("1.4.2024", date(2024, 4, 1)),
    ("2024-04-01", date(2024, 4, 1)),
])
def test_parse_date_formats(text, expected):
    assert parse_date(text) == expected


def test_parse_date_rejects_non_dates():
    assert parse_date("UPI/DR/123") is None
    assert parse_date("500.00") is None


@pytest.mark.parametrize("text, value, marker", [
    ("1,23,456.78", 123456.78, None),
    ("500.00", 500.0, None),
    ("500.00Cr", 500.0, "CR"),
    ("2,000.00 Dr", 2000.0, "DR"),
    ("-250.00", -250.0, None),
    ("(250.00)", -250.0, None),
])
def test_parse_amount(text, value, marker):
    assert parse_amount(text) == (value, marker)


def test_reference_numbers_are_not_amounts():
    assert is_amount("1,234.50")
    assert not is_amount("412345678901")   # UPI reference
    assert not is_amount("2024")
