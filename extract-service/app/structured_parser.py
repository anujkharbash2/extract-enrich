import extruct
from w3lib.html import get_base_url
import logging

logger = logging.getLogger(__name__)

def parse_structured_data(html: str, url: str) -> dict:
    """
    Extracts JSON-LD, Open Graph, and microdata from raw HTML.
    Returns a dict with whatever syntaxes were found, unmerged.
    Never raises - malformed structured data should degrade to empty results,
    not crash the request (real pages in the wild ship broken JSON-LD constantly).
    """
    base_url = get_base_url(html, url)
    try:
        data = extruct.extract(
            html,
            base_url=base_url,
            syntaxes=["json-ld", "microdata", "opengraph"],
        )
        return data
    except Exception as e:
        logger.warning(f"extruct failed to parse structured data for {url}: {e}")
        return {"json-ld": [], "microdata": [], "opengraph": []}


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