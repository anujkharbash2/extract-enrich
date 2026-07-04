from app.schemas import PageType


def classify_page(html: str, structured_data: dict) -> tuple[PageType, float]:
    """
    Lightweight rules-based classifier. Priority order:
    1. Trust JSON-LD/OG type signals if present (highest confidence)
    2. Fall back to DOM/text heuristics (lower confidence)
    """
    json_ld_items = structured_data.get("json-ld", [])
    og_list = structured_data.get("opengraph", [])

    # Signal 1: JSON-LD @type
    product_types = {"Product"}
    article_types = {"Article", "NewsArticle", "BlogPosting"}

    for item in json_ld_items:
        t = item.get("@type")
        types = t if isinstance(t, list) else [t]
        if any(x in product_types for x in types):
            return PageType.PRODUCT, 0.9
        if any(x in article_types for x in types):
            return PageType.ARTICLE, 0.9

    # Signal 2: og:type
    for og_entry in og_list:
        og_dict = dict(og_entry.get("properties", []))
        og_type = og_dict.get("og:type", "")
        if og_type == "product":
            return PageType.PRODUCT, 0.7
        if og_type == "article":
            return PageType.ARTICLE, 0.7

    # Signal 3: crude DOM heuristics (last resort, low confidence)
    html_lower = html.lower()
    price_signals = html_lower.count("add to cart") + html_lower.count("buy now")
    article_signals = html_lower.count("<article") + html_lower.count('itemprop="articlebody"')

    if price_signals > 0 and price_signals >= article_signals:
        return PageType.PRODUCT, 0.4
    if article_signals > 0:
        return PageType.ARTICLE, 0.4

    return PageType.OTHER, 0.0