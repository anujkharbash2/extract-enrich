import re
import logging
from bs4 import BeautifulSoup
from app.schemas import ProductFields
from app.normalizer import clean_text, extract_price_and_currency

logger = logging.getLogger(__name__)

PRICE_PATTERN = re.compile(r"[₹$£€]\s?[\d,]+\.?\d*")


def extract_product_fallback(html: str) -> ProductFields:
    """
    Crude DOM-heuristic extraction for product pages with no JSON-LD/OG.
    Per the doc: keep this simple and rule-based for Phase 1 MVP.
    """
    try:
        soup = BeautifulSoup(html, "lxml")

        # Title: prefer <h1>, fall back to <title>
        title_tag = soup.find("h1")
        title = clean_text(title_tag.get_text()) if title_tag else None
        if not title and soup.title:
            title = clean_text(soup.title.get_text())

        # Price: search visible text for a currency-symbol pattern
        price, currency = None, None
        text = soup.get_text(separator=" ")
        match = PRICE_PATTERN.search(text)
        if match:
            price, currency = extract_price_and_currency(match.group())

        # Images: first few <img> tags with a real src, skip tiny icons/tracking pixels
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