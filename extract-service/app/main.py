from typing import Optional
from fastapi import FastAPI
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

app = FastAPI(title="DATARey Extract Service", version="0.1.0")

PRODUCT_TYPES = {"Product"}
ARTICLE_TYPES = {"Article", "NewsArticle", "BlogPosting"}


class FetchResult(BaseModel):
    html: Optional[str] = None
    statusCode: Optional[int] = None
    renderTimeMs: Optional[int] = None
    finalUrl: Optional[str] = None
    error: Optional[str] = None
    proxyId: Optional[str] = None


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

    if page_type == PageType.PRODUCT:
        item = find_schema_type(json_ld_items, PRODUCT_TYPES)
        if item:
            fields = normalize_product_from_jsonld(item)
            return ExtractResponse(page_type=page_type, confidence=confidence,
                                    extraction_method=ExtractionMethod.JSON_LD, fields=fields.model_dump())

    if page_type == PageType.ARTICLE:
        item = find_schema_type(json_ld_items, ARTICLE_TYPES)
        if item:
            fields = normalize_article_from_jsonld(item)
            return ExtractResponse(page_type=page_type, confidence=confidence,
                                    extraction_method=ExtractionMethod.JSON_LD, fields=fields.model_dump())

    if og_items:
        og_dict = og_list_to_dict(og_items[0].get("properties", []))
        if page_type == PageType.PRODUCT:
            fields = normalize_product_from_og(og_dict)
            return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.7),
                                    extraction_method=ExtractionMethod.OPEN_GRAPH, fields=fields.model_dump())
        if page_type == PageType.ARTICLE:
            fields = normalize_article_from_og(og_dict)
            return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.7),
                                    extraction_method=ExtractionMethod.OPEN_GRAPH, fields=fields.model_dump())
        
        # Last resort: DOM-heuristic fallback extraction
    if page_type == PageType.PRODUCT:
        fields = extract_product_fallback(payload.html)
        return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.4),
                                extraction_method=ExtractionMethod.FALLBACK, fields=fields.model_dump())

    if page_type == PageType.ARTICLE:
        fields = extract_article_fallback(payload.html)
        return ExtractResponse(page_type=page_type, confidence=min(confidence, 0.4),
                                extraction_method=ExtractionMethod.FALLBACK, fields=fields.model_dump())

    return ExtractResponse(page_type=PageType.OTHER, confidence=0.0,
                            extraction_method=ExtractionMethod.NONE, fields={})