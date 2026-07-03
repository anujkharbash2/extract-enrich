from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class PageType(str, Enum):
    PRODUCT = "product"
    ARTICLE = "article"
    OTHER = "other"


class ExtractionMethod(str, Enum):
    JSON_LD = "json_ld"
    OPEN_GRAPH = "open_graph"
    MICRODATA = "microdata"
    FALLBACK = "fallback"
    NONE = "none"


class ProductFields(BaseModel):
    title: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    images: List[str] = []
    stock_status: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None


class ArticleFields(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    published_time: Optional[str] = None
    body_text: Optional[str] = None
    images: List[str] = []
    description: Optional[str] = None


class ExtractResponse(BaseModel):
    page_type: PageType
    confidence: float
    extraction_method: ExtractionMethod
    fields: dict  # will hold ProductFields or ArticleFields as dict