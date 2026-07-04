from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from app.fallback_article import extract_article_fallback
from app.fallback_product import extract_product_fallback
from app.structured_parser import parse_structured_data, find_schema_type
from app.normalizer import (
    normalize_product_from_jsonld,
    normalize_article_from_jsonld,
    normalize_product_from_og,
    normalize_article_from_og,
    og_list_to_dict,
)
from app.classifier import classify_page
from app.fetch_guard import should_skip_extraction, looks_suspect
from app.schemas import PageType, ExtractionMethod, ExtractResponse
from app.enrich_client import call_enrich_service

app = FastAPI(title="DATARey Extract Service", version="0.1.0")

PRODUCT_TYPES = {"Product"}
ARTICLE_TYPES = {"Article", "NewsArticle", "BlogPosting"}

MAX_HTML_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@app.middleware("http")
async def limit_payload_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_HTML_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Payload too large")
    return await call_next(request)


class FetchResult(BaseModel):
    html: Optional[str] = None
    statusCode: Optional[int] = None
    renderTimeMs: Optional[int] = None
    finalUrl: Optional[str] = None
    error: Optional[str] = None
    proxyId: Optional[str] = None


def maybe_enrich(page_type: PageType, fields_dict: dict) -> dict:
    """Attach enrichment fields to article results when body_text is available."""
    if page_type != PageType.ARTICLE:
        return fields_dict
    body_text = fields_dict.get("body_text")
    if not body_text:
        return fields_dict
    enrichment = call_enrich_service(body_text)
    if enrichment:
        fields_dict["language"] = enrichment.get("language")
        fields_dict["entities"] = enrichment.get("entities")
        fields_dict["sentiment"] = enrichment.get("sentiment")
    return fields_dict


@app.get("/health")
def health():
    return {"status": "ok", "service": "extract-service"}


@app.post("/debug/structured-data")
def debug_structured_data(payload: FetchResult):
    url = payload.finalUrl or ""
    return parse_structured_data(payload.html or "", url)


@app.post("/v1/extract", response_model=ExtractResponse)
def extract(payload: FetchResult):
    if should_skip_extraction(payload.error):
        return ExtractResponse(
            page_type=PageType.OTHER,
            confidence=0.0,
            extraction_method=ExtractionMethod.NONE,
            fields={"skipped_reason": payload.error},
        )

    if looks_suspect(payload.html):
        return ExtractResponse(
            page_type=PageType.OTHER,
            confidence=0.0,
            extraction_method=ExtractionMethod.NONE,
            fields={"skipped_reason": "SUSPECT_CONTENT_POSSIBLE_BLOCK_FALSE_NEGATIVE"},
        )

    url = payload.finalUrl or ""
    structured = parse_structured_data(payload.html, url)
    json_ld_items = structured.get("json-ld", [])
    og_items = structured.get("opengraph", [])

    page_type, confidence = classify_page(payload.html, structured)

    # 1. Try JSON-LD first (highest quality)
    if page_type == PageType.PRODUCT:
        item = find_schema_type(json_ld_items, PRODUCT_TYPES)
        if item:
            fields = normalize_product_from_jsonld(item)
            fields_dict = maybe_enrich(page_type, fields.model_dump())
            return ExtractResponse(page_type=page_type, confidence=confidence,
                                    extraction_method=ExtractionMethod.JSON_LD, fields=fields_dict)

    if page_type == PageType.ARTICLE:
        item = find_schema_type(json_ld_items, ARTICLE_TYPES)
        if item:
            fields = normalize_article_from_jsonld(item)
            fields_dict = maybe_enrich(page_type, fields.model_dump())
            return ExtractResponse(page_type=page_type, confidence=confidence,
                                    extraction_method=ExtractionMethod.JSON_LD, fields=fields_dict)

    # 2. Fall back to OG if JSON-LD didn't have what we needed
    if og_items:
        og_dict = og_list_to_dict(og_items[0].get("properties", []))
        if page_type == PageType.PRODUCT:
            fields = normalize_product_from_og(og_dict)
            fields_dict = maybe_enrich(page_type, fields.model_dump())
            return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.7),
                                    extraction_method=ExtractionMethod.OPEN_GRAPH, fields=fields_dict)
        if page_type == PageType.ARTICLE:
            fields = normalize_article_from_og(og_dict)
            fields_dict = maybe_enrich(page_type, fields.model_dump())
            return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.7),
                                    extraction_method=ExtractionMethod.OPEN_GRAPH, fields=fields_dict)

    # 3. Last resort: DOM-heuristic fallback extraction
    if page_type == PageType.PRODUCT:
        fields = extract_product_fallback(payload.html)
        fields_dict = maybe_enrich(page_type, fields.model_dump())
        return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.4),
                                extraction_method=ExtractionMethod.FALLBACK, fields=fields_dict)

    if page_type == PageType.ARTICLE:
        fields = extract_article_fallback(payload.html)
        fields_dict = maybe_enrich(page_type, fields.model_dump())
        return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.4),
                                extraction_method=ExtractionMethod.FALLBACK, fields=fields_dict)

    return ExtractResponse(page_type=PageType.OTHER, confidence=0.0,
                            extraction_method=ExtractionMethod.NONE, fields={})