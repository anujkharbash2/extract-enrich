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
    assert data["cleaned_text"] is not None  # cleanup now runs on all input


def test_enrich_extracts_entities_for_english():
    response = client.post("/v1/enrich", json={
        "text": "Narendra Modi met with Tata Group representatives in New Delhi."
    })
    assert response.status_code == 200
    data = response.json()
    entity_texts = [e["text"] for e in data["entities"]]
    assert "Narendra Modi" in entity_texts
    assert any(e["type"] == "organization" for e in data["entities"])
    assert any(e["type"] == "location" for e in data["entities"])


def test_enrich_skips_ner_for_non_english():
    response = client.post("/v1/enrich", json={
        "text": "यह एक परीक्षण वाक्य है जो हिंदी भाषा में लिखा गया है।"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["entities"] == []

def test_enrich_positive_sentiment():
    response = client.post("/v1/enrich", json={
        "text": "This is a wonderful, fantastic product. I absolutely love it!"
    })
    data = response.json()
    assert data["sentiment"] > 0.5


def test_enrich_negative_sentiment():
    response = client.post("/v1/enrich", json={
        "text": "This is terrible and awful. I hate it completely."
    })
    data = response.json()
    assert data["sentiment"] < -0.5


def test_enrich_strips_boilerplate_in_cleaned_text():
    response = client.post("/v1/enrich", json={
        "text": "Real article content here.   Subscribe to our newsletter   for updates."
    })
    data = response.json()
    assert "newsletter" not in data["cleaned_text"].lower()
    assert "Real article content here." in data["cleaned_text"]