import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def load_fixture(name: str) -> str:
    with open(f"tests/fixtures/{name}", "r", encoding="utf-8") as f:
        return f.read()


def test_article_enrichment_merges_language_when_enrich_service_available():
    """
    This test requires enrich-service actually running on localhost:8002.
    It's an integration test, not a pure unit test - skip gracefully if
    the service isn't up, rather than failing CI runs that don't have it.
    """
    import httpx
    try:
        httpx.get("http://localhost:8002/health", timeout=1.0)
    except Exception:
        pytest.skip("enrich-service not running on localhost:8002")

    html = load_fixture("no_structured_article.html")
    response = client.post("/v1/extract", json={
        "html": html, "statusCode": 200, "renderTimeMs": 100,
        "finalUrl": "https://example.com", "error": None, "proxyId": "test",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["page_type"] == "article"
    assert "language" in data["fields"]
    assert data["fields"]["language"]["language_code"] == "en"
    assert data["fields"]["language"]["is_target_language"] is True


def test_extraction_still_works_when_enrich_service_unavailable():
    """
    Simulates enrich-service being down by pointing the client at a dead port.
    Extraction must still succeed - enrichment failure should never break extraction.
    """
    from app import enrich_client
    original_url = enrich_client.ENRICH_SERVICE_URL
    enrich_client.ENRICH_SERVICE_URL = "http://localhost:9999/v1/enrich"  # nothing listens here

    try:
        html = load_fixture("no_structured_article.html")
        response = client.post("/v1/extract", json={
            "html": html, "statusCode": 200, "renderTimeMs": 100,
            "finalUrl": "https://example.com", "error": None, "proxyId": "test",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["page_type"] == "article"
        assert "language" not in data["fields"]  # enrichment failed silently, extraction still worked
        assert data["fields"]["title"] == "Local Farmers Report Record Harvest This Season"
    finally:
        enrich_client.ENRICH_SERVICE_URL = original_url
        