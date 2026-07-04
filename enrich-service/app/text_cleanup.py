import html as html_lib
import re

# Common boilerplate fragments that survive extraction (nav remnants, cookie banners, etc.)
BOILERPLATE_PATTERNS = [
    re.compile(r"\bcookie(s)?\s+(policy|consent|notice)\b", re.IGNORECASE),
    re.compile(r"\bsubscribe\s+to\s+our\s+newsletter\b", re.IGNORECASE),
    re.compile(r"\ball\s+rights\s+reserved\b", re.IGNORECASE),
    re.compile(r"\bshare\s+on\s+(facebook|twitter|whatsapp)\b", re.IGNORECASE),
]


def clean_enrichment_text(text: str) -> str | None:
    """
    Text quality pass per Team 3's scope: whitespace normalization,
    encoding fixes (mojibake), and secondary boilerplate stripping that
    extraction's own cleanup may have missed.
    """
    if not text or not text.strip():
        return None

    text = html_lib.unescape(text)

    for pattern in BOILERPLATE_PATTERNS:
        text = pattern.sub("", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text or None