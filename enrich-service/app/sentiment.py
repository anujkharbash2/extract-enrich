from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def score_sentiment(text: str) -> float | None:
    """
    Returns a compound sentiment score from -1 (very negative) to +1 (very positive).
    None if text is empty. Phase 1 scope: 'basic sentiment scoring', not a trained
    model - VADER is a well-established lexicon/rule-based approach, good enough
    for a first pass and fast (no model inference cost).
    """
    if not text or not text.strip():
        return None
    scores = _analyzer.polarity_scores(text)
    return round(scores["compound"], 4)