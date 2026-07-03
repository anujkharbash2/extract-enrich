import extruct
from w3lib.html import get_base_url


def parse_structured_data(html: str, url: str) -> dict:
    """
    Extracts JSON-LD, Open Graph, and microdata from raw HTML.
    Returns a dict with whatever syntaxes were found, unmerged.
    """
    base_url = get_base_url(html, url)
    data = extruct.extract(
        html,
        base_url=base_url,
        syntaxes=["json-ld", "microdata", "opengraph"],
    )
    return data


def find_schema_type(json_ld_items: list, target_types: set) -> dict | None:
    """
    Given a list of JSON-LD items, return the first one whose @type
    matches one of the target_types (e.g. {"Product"} or {"Article", "NewsArticle"}).
    """
    for item in json_ld_items:
        item_type = item.get("@type")
        if isinstance(item_type, list):
            if any(t in target_types for t in item_type):
                return item
        elif item_type in target_types:
            return item
    return None