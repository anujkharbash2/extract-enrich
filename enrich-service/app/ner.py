import spacy
from pydantic import BaseModel

# Load once at module import time - loading per-request would be far too slow
_nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "lemmatizer", "attribute_ruler"])

# Map spaCy's internal entity labels to our simpler public categories.
# spaCy's en_core_web_sm produces ~18 label types; we only care about
# person/organization/location per the doc's Phase 1 scope.
SPACY_LABEL_MAP = {
    "PERSON": "person",
    "ORG": "organization",
    "GPE": "location",   # geopolitical entity (countries, cities, states)
    "LOC": "location",   # non-GPE locations (mountains, bodies of water)
}


class Entity(BaseModel):
    text: str
    type: str
    start_char: int
    end_char: int


def extract_entities(text: str) -> list[Entity]:
    """
    Extracts person/organization/location entities from English text.
    Phase 1 scope: English only, these three entity types only.
    """
    if not text or not text.strip():
        return []

    # Guard against extremely long text - spaCy can be slow on huge documents,
    # and article body text should never legitimately need more than this.
    MAX_CHARS = 50_000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    doc = _nlp(text)
    entities = []
    for ent in doc.ents:
        mapped_type = SPACY_LABEL_MAP.get(ent.label_)
        if mapped_type:
            entities.append(Entity(
                text=ent.text,
                type=mapped_type,
                start_char=ent.start_char,
                end_char=ent.end_char,
            ))
    return entities