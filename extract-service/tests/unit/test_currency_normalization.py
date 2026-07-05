import pytest
from app.normalizer import extract_price_and_currency


@pytest.mark.parametrize("raw_input,expected_price,expected_currency", [
    ("₹1,999.00", "1999.00", "INR"),
    ("$1,299.99", "1299.99", "USD"),
    ("£45.50", "45.50", "GBP"),
    ("1.999,00", "1999.00", None),          # European format, no currency indicator present
    ("Rs. 2500", "2500", "INR"),
    ("INR 3,450", "3450", "INR"),
    ("45000", "45000", None),               # bare number, correctly no currency
])
def test_extract_price_and_currency_formats(raw_input, expected_price, expected_currency):
    price, currency = extract_price_and_currency(raw_input)
    assert price == expected_price
    assert currency == expected_currency