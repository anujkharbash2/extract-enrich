from fastapi import FastAPI
from pydantic import BaseModel
from app.language import detect_language, LanguageResult

app = FastAPI(title="DATARey Enrich Service", version="0.1.0")


class EnrichInput(BaseModel):
    text: str


class EnrichResponse(BaseModel):
    language: LanguageResult
    entities: list = []          # placeholder - Step 10+
    sentiment: float | None = None  # placeholder - later step
    cleaned_text: str | None = None  # placeholder - later step


@app.get("/health")
def health():
    return {"status": "ok", "service": "enrich-service"}


@app.post("/v1/enrich", response_model=EnrichResponse)
def enrich(payload: EnrichInput):
    lang_result = detect_language(payload.text)
    return EnrichResponse(
        language=lang_result,
        entities=[],
        sentiment=None,
        cleaned_text=None,
    )