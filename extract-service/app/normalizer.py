import re
from typing import Optional
from app.schemas import ProductFields, ArticleFields
import html as html_lib




def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip() or None





def extract_price_and_currency(raw_price) -> tuple[Optional[str], Optional[str]]:
    """
    Handles cases like '$19.99', '19.99', {'@type': 'Offer', 'price': '19.99', 'priceCurrency': 'USD'}
    """
    if raw_price is None:
        return None, None

    if isinstance(raw_price, dict):
        price = raw_price.get("price") or raw_price.get("priceSpecification", {}).get("price")
        currency = raw_price.get("priceCurrency")
        return clean_text(str(price)) if price else None, currency

    if isinstance(raw_price, (int, float)):
        return str(raw_price), None

    if isinstance(raw_price, str):
        match = re.search(r"([£$€₹])?\s*([\d,]+\.?\d*)", raw_price)
        if match:
            symbol_map = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR"}
            symbol, amount = match.groups()
            currency = symbol_map.get(symbol) if symbol else None
            return amount.replace(",", ""), currency

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