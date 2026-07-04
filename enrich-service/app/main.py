from fastapi import FastAPI
from pydantic import BaseModel
from app.language import detect_language, LanguageResult
from app.ner import extract_entities, Entity
from app.sentiment import score_sentiment
from app.text_cleanup import clean_enrichment_text

app = FastAPI(title="DATARey Enrich Service", version="0.1.0")


class EnrichInput(BaseModel):
    text: str


class EnrichResponse(BaseModel):
    language: LanguageResult
    entities: list[Entity] = []
    sentiment: float | None = None
    cleaned_text: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "enrich-service"}


@app.post("/v1/enrich", response_model=EnrichResponse)
def enrich(payload: EnrichInput):
    lang_result = detect_language(payload.text)

    entities = []
    if lang_result.language_code == "en":
        entities = extract_entities(payload.text)

    sentiment = score_sentiment(payload.text)
    cleaned = clean_enrichment_text(payload.text)

    return EnrichResponse(
        language=lang_result,
        entities=entities,
        sentiment=sentiment,
        cleaned_text=cleaned,
    )