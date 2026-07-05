from typing import Optional
import re
TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

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
    Scoped to the <title> tag only, not the full page - full-page keyword scans
    produce false positives on legitimate sites that mention CAPTCHA/blocking
    terminology in their own JS/module code (e.g. Wikipedia/MediaWiki's
    ConfirmEdit extension). This mirrors Team 1's own fix for the same problem
    in their blockDetector.
    """
    if not html or len(html) < MIN_PLAUSIBLE_HTML_LENGTH:
        return True

    title_match = TITLE_PATTERN.search(html)
    title_text = title_match.group(1).lower() if title_match else ""
    return any(marker in title_text for marker in CAPTCHA_MARKERS)