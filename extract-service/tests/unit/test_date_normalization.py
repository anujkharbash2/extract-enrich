import pytest
from app.normalizer import normalize_date


@pytest.mark.parametrize("raw_input,expected", [
    ("2026-07-03T06:50:11+05:30", "2026-07-03T06:50:11+05:30"),  # ISO with tz - must stay exact
    ("2026-07-03", "2026-07-03T00:00:00+00:00"),
    ("03/07/2026", "2026-07-03T00:00:00+00:00"),                  # ambiguous - dayfirst assumption
    ("July 3, 2026", "2026-07-03T00:00:00+00:00"),
    ("3 July 2026", "2026-07-03T00:00:00+00:00"),
    ("2026-07-03 06:50:11", "2026-07-03T06:50:11+00:00"),
    ("not a date at all", None),
    ("", None),
    (None, None),
])
def test_normalize_date_formats(raw_input, expected):
    assert normalize_date(raw_input) == expected