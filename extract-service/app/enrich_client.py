import logging
import httpx

logger = logging.getLogger(__name__)

ENRICH_SERVICE_URL = "http://localhost:8002/v1/enrich"
ENRICH_TIMEOUT_SECONDS = 0.3  # per doc: enrichment shouldn't add much latency; fail fast


def call_enrich_service(text: str) -> dict | None:
    """
    Calls enrich-service synchronously. Returns None on any failure -
    per the doc's own guidance: 'return extraction without enrichment if the
    enrichment step is slow, rather than blocking the whole request.'
    """
    if not text or not text.strip():
        return None

    try:
        response = httpx.post(
            ENRICH_SERVICE_URL,
            json={"text": text},
            timeout=ENRICH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"enrich-service call failed, returning extraction without enrichment: {e}")
        return None