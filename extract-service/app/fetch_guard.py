from typing import Optional

KNOWN_FETCH_ERRORS = {
    "TIMEOUT", "BLOCKED", "CAPTCHA", "DNS_FAIL",
    "INVALID_URL", "ROBOTS_DISALLOWED", "NO_PROXIES_AVAILABLE",
}

# Cheap heuristics to catch cases where blockDetector.js let something bad through
CAPTCHA_MARKERS = [
    "captcha", "are you a robot", "verify you are human",
    "access denied", "unusual traffic",
]

MIN_PLAUSIBLE_HTML_LENGTH = 500  # bytes; real pages are rarely this short


def should_skip_extraction(error: Optional[str]) -> bool:
    """If Team 1 reports any error, html will be null - never attempt extraction."""
    return error is not None


def looks_suspect(html: Optional[str]) -> bool:
    """
    Cheap sanity check for cases where error was null but content still looks broken.
    Not a replacement for Team 1's blockDetector - just a second, independent check
    since they've told us it has known false positives.
    """
    if not html or len(html) < MIN_PLAUSIBLE_HTML_LENGTH:
        return True
    lower = html.lower()
    return any(marker in lower for marker in CAPTCHA_MARKERS)