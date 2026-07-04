import time
from app.fallback_product import PRICE_PATTERN
from app.normalizer import clean_text

# Adversarial inputs designed to trigger catastrophic backtracking
# if a regex is vulnerable. A safe regex should handle these in milliseconds.
ADVERSARIAL_INPUTS = [
    "$" * 10000,                          # repeated currency symbols, no digits
    "1" * 50000,                          # huge digit run, no currency symbol
    ("₹" + "9" * 100 + ".") * 500,        # many partial price-like fragments
    " " * 100000,                         # whitespace flood, targets clean_text's \s+
    "a" * 50000 + "$" + "1" * 50000,      # currency symbol buried deep in noise
]

MAX_ALLOWED_SECONDS = 1.0  # generous ceiling; a safe regex finishes in milliseconds


def test_price_pattern_resists_redos():
    for payload in ADVERSARIAL_INPUTS:
        start = time.monotonic()
        PRICE_PATTERN.search(payload)
        elapsed = time.monotonic() - start
        assert elapsed < MAX_ALLOWED_SECONDS, (
            f"PRICE_PATTERN took {elapsed:.2f}s on adversarial input "
            f"(len={len(payload)}) - possible ReDoS vulnerability"
        )


def test_clean_text_resists_redos():
    for payload in ADVERSARIAL_INPUTS:
        start = time.monotonic()
        clean_text(payload)
        elapsed = time.monotonic() - start
        assert elapsed < MAX_ALLOWED_SECONDS, (
            f"clean_text took {elapsed:.2f}s on adversarial input "
            f"(len={len(payload)}) - possible ReDoS vulnerability"
        )