from py3langid.langid import LanguageIdentifier, MODEL_FILE
from pydantic import BaseModel

TARGET_LANGUAGES = {"en", "hi", "ta", "bn", "mr"}

# Build our own identifier instance with norm_probs=True passed explicitly.
# (Setting the module-level NORM_PROBS flag doesn't work retroactively -
# it's baked into __init__'s default argument at class-definition time.)
_identifier = LanguageIdentifier.from_pickled_model(MODEL_FILE, norm_probs=True)


class LanguageResult(BaseModel):
    language_code: str
    confidence: float
    is_target_language: bool


def detect_language(text: str) -> LanguageResult:
    """
    Detects the language of the given text.
    Phase 1 scope: detection only, not deep extraction, for non-English content.
    """
    if not text or not text.strip():
        return LanguageResult(language_code="unknown", confidence=0.0, is_target_language=False)

    lang_code, confidence = _identifier.classify(text)
    return LanguageResult(
        language_code=lang_code,
        confidence=round(float(confidence), 4),
        is_target_language=lang_code in TARGET_LANGUAGES,
    )