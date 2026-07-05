import re
from typing import Optional
from app.schemas import ProductFields, ArticleFields
import html as html_lib

CURRENCY_SYMBOL_MAP = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR"}
CURRENCY_CODE_PATTERN = re.compile(r"\b(INR|USD|GBP|EUR|Rs\.?)\b", re.IGNORECASE)
CODE_TO_CURRENCY = {"inr": "INR", "usd": "USD", "gbp": "GBP", "eur": "EUR", "rs": "INR", "rs.": "INR"}



def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip() or None



def _parse_number_format(raw_number: str) -> str | None:
    """
    Handles both US/Indian format (1,999.00 - comma=thousands, dot=decimal)
    and European format (1.999,00 - dot=thousands, comma=decimal).

    Heuristic: if there's exactly one comma and one dot, whichever comes
    LAST is the real decimal separator (the other is a thousands separator).
    If only one type of separator appears, and it has exactly 2 digits after
    it, treat it as decimal; otherwise treat it as a thousands separator.
    """
    raw_number = raw_number.strip()
    has_comma = "," in raw_number
    has_dot = "." in raw_number

    if has_comma and has_dot:
        last_comma = raw_number.rfind(",")
        last_dot = raw_number.rfind(".")
        if last_dot > last_comma:
            cleaned = raw_number.replace(",", "")
        else:
            cleaned = raw_number.replace(".", "").replace(",", ".")
    elif has_comma:
        parts = raw_number.split(",")
        if len(parts[-1]) == 2:
            cleaned = raw_number.replace(",", ".")
        else:
            cleaned = raw_number.replace(",", "")
    else:
        cleaned = raw_number

    match = re.search(r"[\d.]+", cleaned)
    return match.group() if match else None

def extract_price_and_currency(raw_price) -> tuple[Optional[str], Optional[str]]:
    """
    Handles cases like '$19.99', '19.99', {'@type': 'Offer', 'price': '19.99', 'priceCurrency': 'USD'},
    European format '1.999,00', and text currency codes like 'Rs. 2500' / 'INR 3,450'.
    """
    if raw_price is None:
        return None, None

    if isinstance(raw_price, dict):
        price = raw_price.get("price") or raw_price.get("priceSpecification", {}).get("price")
        currency = raw_price.get("priceCurrency")
        return (_parse_number_format(str(price)) if price else None), currency

    if isinstance(raw_price, (int, float)):
        return str(raw_price), None

    if isinstance(raw_price, str):
        currency = None

        symbol_match = re.search(r"[£$€₹]", raw_price)
        if symbol_match:
            currency = CURRENCY_SYMBOL_MAP.get(symbol_match.group())

        if not currency:
            code_match = CURRENCY_CODE_PATTERN.search(raw_price)
            if code_match:
                currency = CODE_TO_CURRENCY.get(code_match.group().lower().rstrip("."))

        number_match = re.search(r"\d[\d,.]*", raw_price)
        if number_match:
            price = _parse_number_format(number_match.group())
            return price, currency

    return None, None


def normalize_product_from_jsonld(item: dict) -> ProductFields:
    offers = item.get("offers", {})
    price, currency = extract_price_and_currency(offers)

    images = item.get("image", [])
    if isinstance(images, str):
        images = [images]
    elif isinstance(images, dict):
        images = [images.get("url")] if images.get("url") else []

    availability = offers.get("availability") if isinstance(offers, dict) else None
    stock_status = None
    if availability:
        stock_status = "in_stock" if "InStock" in availability else "out_of_stock" if "OutOfStock" in availability else availability

    return ProductFields(
        title=clean_text(item.get("name")),
        price=price,
        currency=currency,
        images=[img for img in images if img],
        stock_status=stock_status,
        brand=clean_text(item.get("brand", {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand")),
        description=clean_text(item.get("description")),
    )


def normalize_article_from_jsonld(item: dict) -> ArticleFields:
    author = item.get("author")
    if isinstance(author, dict):
        author = author.get("name")
    elif isinstance(author, list) and author:
        author = author[0].get("name") if isinstance(author[0], dict) else author[0]

    images = item.get("image", [])
    if isinstance(images, str):
        images = [images]
    elif isinstance(images, dict):
        images = [images.get("url")] if images.get("url") else []

    return ArticleFields(
        title=clean_text(item.get("headline") or item.get("name")),
        author=clean_text(author) if isinstance(author, str) else None,
        published_time=item.get("datePublished"),
        body_text=clean_text(item.get("articleBody")),
        images=[img for img in images if img],
        description=clean_text(item.get("description")),
    )
def og_list_to_dict(og_properties: list) -> dict:
    """extruct returns OG properties as a list of [key, value] pairs; flatten to a dict."""
    result = {}
    for key, value in og_properties:
        if key not in result:
            result[key] = value
    return result


def normalize_product_from_og(og: dict) -> ProductFields:
    price, currency = extract_price_and_currency(og.get("product:price:amount"))
    currency = og.get("product:price:currency") or currency
    return ProductFields(
        title=clean_text(og.get("og:title")),
        price=price,
        currency=currency,
        images=[og["og:image"]] if og.get("og:image") else [],
        stock_status=None,
        brand=None,
        description=clean_text(og.get("og:description")),
    )


def normalize_article_from_og(og: dict) -> ArticleFields:
    return ArticleFields(
        title=clean_text(og.get("og:title")),
        author=clean_text(og.get("article:author")),
        published_time=og.get("article:published_time"),
        body_text=None,
        images=[og["og:image"]] if og.get("og:image") else [],
        description=clean_text(og.get("og:description")),
    )