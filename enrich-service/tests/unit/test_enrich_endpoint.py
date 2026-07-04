from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_enrich_detects_english():
    response = client.post("/v1/enrich", json={
        "text": "The quick brown fox jumps over the lazy dog near the riverbank."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["language"]["language_code"] == "en"
    assert data["language"]["is_target_language"] is True
    assert data["language"]["confidence"] > 0.8


def test_enrich_detects_hindi():
    response = client.post("/v1/enrich", json={
        "text": "यह एक परीक्षण वाक्य है जो हिंदी भाषा में लिखा गया है।"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["language"]["language_code"] == "hi"
    assert data["language"]["is_target_language"] is True


def test_enrich_handles_empty_text():
    response = client.post("/v1/enrich", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["language"]["language_code"] == "unknown"
    assert data["language"]["confidence"] == 0.0


def test_enrich_response_has_placeholder_fields():
    response = client.post("/v1/enrich", json={"text": "Hello world."})
    data = response.json()
    assert data["entities"] == []
    assert data["sentiment"] is None
    assert data["cleaned_text"] is None