from fastapi import FastAPI
from pydantic import BaseModel
from app.structured_parser import parse_structured_data

app = FastAPI(title="DATARey Extract Service", version="0.1.0")


class RawHtmlInput(BaseModel):
    url: str
    html: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "extract-service"}


@app.post("/debug/structured-data")
def debug_structured_data(payload: RawHtmlInput):
    """Temporary debug endpoint - lets us eyeball what extruct finds."""
    return parse_structured_data(payload.html, payload.url)