import json
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def load_fixture(name: str) -> str:
    with open(f"tests/fixtures/{name}", "r", encoding="utf-8") as f:
        return f.read()


def make_payload(html, error=None, final_url="https://example.com"):
    return {
        "html": html,
        "statusCode": 200 if error is None else None,
        "renderTimeMs": 1200,
        "finalUrl": final_url if error is None else None,
        "error": error,
        "proxyId": "test-proxy",
    }


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_real_article_extraction():
    html = load_fixture("sample_article.html")
    response = client.post("/v1/extract", json=make_payload(
        html,
        final_url="https://www.thehindu.com/news/international/west-asia-war-live-updates-july-3-2026-iran-israel-usa-strait-of-hormuz/article71177098.ece",
    ))
    assert response.status_code == 200
    data = response.json()
    assert data["page_type"] == "article"
    assert data["extraction_method"] == "json_ld"
    assert data["fields"]["title"] == "West Asia war LIVE: Ayatollah Khamenei laid in state in Tehran ahead of weeklong mass funeral"
    assert data["fields"]["author"] == "The Hindu Bureau"


def test_error_skips_extraction():
    response = client.post("/v1/extract", json=make_payload(None, error="BLOCKED"))
    assert response.status_code == 200
    data = response.json()
    assert data["page_type"] == "other"
    assert data["fields"]["skipped_reason"] == "BLOCKED"


@pytest.mark.parametrize("error_code", [
    "TIMEOUT", "CAPTCHA", "DNS_FAIL", "INVALID_URL",
    "ROBOTS_DISALLOWED", "NO_PROXIES_AVAILABLE",
])
def test_all_known_error_codes_skip_cleanly(error_code):
    response = client.post("/v1/extract", json=make_payload(None, error=error_code))
    assert response.status_code == 200
    assert response.json()["fields"]["skipped_reason"] == error_code


def test_empty_html_treated_as_suspect():
    html = load_fixture("empty.html")
    response = client.post("/v1/extract", json=make_payload(html))
    assert response.status_code == 200
    data = response.json()
    assert data["page_type"] == "other"
    assert data["fields"]["skipped_reason"] == "SUSPECT_CONTENT_POSSIBLE_BLOCK_FALSE_NEGATIVE"


def test_malformed_jsonld_does_not_crash():
    html = load_fixture("malformed_jsonld.html")
    # Malformed JSON-LD is short, so pad it to pass the length guard and isolate
    # the actual malformed-JSON handling behavior we care about.
    html = html + ("<!-- padding -->" * 50)
    response = client.post("/v1/extract", json=make_payload(html))
    assert response.status_code == 200
    # Should not crash - either falls through to "other" or extracts what it can
    data = response.json()
    assert "page_type" in data


def test_captcha_marker_flagged_as_suspect():
    html = "<html><body>" + ("Please complete the CAPTCHA to continue. " * 30) + "</body></html>"
    response = client.post("/v1/extract", json=make_payload(html))
    assert response.status_code == 200
    data = response.json()
    assert data["fields"]["skipped_reason"] == "SUSPECT_CONTENT_POSSIBLE_BLOCK_FALSE_NEGATIVE"

def test_fallback_extraction_no_structured_data():
    html = load_fixture("no_structured_article.html")
    response = client.post("/v1/extract", json=make_payload(html))
    assert response.status_code == 200
    data = response.json()
    assert data["page_type"] == "article"
    assert data["extraction_method"] == "fallback"
    assert "Local Farmers" in data["fields"]["title"]
    assert "harvest" in data["fields"]["body_text"].lower()