import logging
from readability import Document
from bs4 import BeautifulSoup
from app.schemas import ArticleFields
from app.normalizer import clean_text

logger = logging.getLogger(__name__)


def extract_article_fallback(html: str) -> ArticleFields:
    """
    Readability-style extraction for pages with no usable JSON-LD/OG article data.
    Strips nav/ads/boilerplate, keeps the main content.
    """
    try:
        doc = Document(html)
        summary_html = doc.summary()
        body_soup = BeautifulSoup(summary_html, "lxml")
        body_text = clean_text(body_soup.get_text(separator=" "))

        # Prefer <h1> for title - more reliable than <title> tag, which often
        # has site-name suffixes ("Headline - Site Name") or generic page titles
        full_soup = BeautifulSoup(html, "lxml")
        h1_tag = full_soup.find("h1")
        if h1_tag and h1_tag.get_text(strip=True):
            title = clean_text(h1_tag.get_text())
        else:
            title = clean_text(doc.title())

    except Exception as e:
        logger.warning(f"Readability fallback failed: {e}")
        title, body_text = None, None

    return ArticleFields(
        title=title,
        author=None,
        published_time=None,
        body_text=body_text,
        images=[],
        description=None,
    )