import re
import logging
from bs4 import BeautifulSoup
from app.schemas import ProductFields
from app.normalizer import clean_text, extract_price_and_currency

logger = logging.getLogger(__name__)

PRICE_PATTERN = re.compile(r"[₹$£€]\s?[\d,]+\.?\d*")

# Common, specific price-container class names across major e-commerce sites.
# Checking these FIRST avoids picking up nav/category links, "was" prices in
# unrelated widgets, or unrelated ₹-prefixed text elsewhere on the page.
PRICE_SELECTORS = [
    ".a-price .a-offscreen",  # Amazon (screen-reader price, usually the cleanest single string, e.g. "₹469.00")
    ".a-price",                # Amazon (parent container - combines symbol + whole + fraction spans)
    "[class*='selling-price']",  # Meesho/Myntra-style
    "[class*='discounted-price']",
    "[itemprop='price']",
]


def _pick_best_h1(soup) -> str | None:
    """
    Pages can have multiple <h1> tags (nav widgets, UI labels, etc.)
    alongside the real product title. Prefer the longest one, since
    product titles are typically much longer than UI labels like
    'Follow the authors' or 'Replacement Instructions'.
    """
    h1_tags = soup.find_all("h1")
    candidates = [tag.get_text(strip=True) for tag in h1_tags]
    candidates = [text for text in candidates if text]
    if not candidates:
        return None
    return max(candidates, key=len)


def _find_price_via_selectors(soup) -> str | None:
    """Try known price-container CSS classes before falling back to a blind
    regex scan of the whole page's text, which is prone to matching nav/
    category links (e.g. Amazon's 'Under ₹500' price-filter links)."""
    for selector in PRICE_SELECTORS:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            if text:
                return text
    return None

def extract_product_fallback(html: str) -> ProductFields:
    """
    Crude DOM-heuristic extraction for product pages with no JSON-LD/OG.
    Per the doc: keep this simple and rule-based for Phase 1 MVP.
    """
    try:
        soup = BeautifulSoup(html, "lxml")

        title = clean_text(_pick_best_h1(soup))
        if not title and soup.title:
            title = clean_text(soup.title.get_text())

        price, currency = None, None
        price_text = _find_price_via_selectors(soup)
        if price_text:
            price, currency = extract_price_and_currency(price_text)
        else:
            # Fallback to blind text scan only if no known price container found.
            # Known limitation: can match unrelated ₹/$ text (nav links, filters).
            text = soup.get_text(separator=" ")
            match = PRICE_PATTERN.search(text)
            if match:
                price, currency = extract_price_and_currency(match.group())

        images = []
        for img in soup.find_all("img", src=True)[:20]:
            src = img["src"]
            if src.startswith("http") and not any(x in src.lower() for x in ["icon", "pixel", "1x1", "sprite"]):
                images.append(src)
            if len(images) >= 5:
                break

    except Exception as e:
        logger.warning(f"DOM fallback extraction failed: {e}")
        title, price, currency, images = None, None, None, []

    return ProductFields(
        title=title,
        price=price,
        currency=currency,
        images=images,
        stock_status=None,
        brand=None,
        description=None,
    )