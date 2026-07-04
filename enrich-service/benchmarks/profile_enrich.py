import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.language import detect_language
from app.ner import extract_entities
from app.sentiment import score_sentiment
from app.text_cleanup import clean_enrichment_text

SAMPLE_TEXT = (
    "Farmers across the region are reporting one of the best harvests in a decade, "
    "thanks to favorable monsoon patterns and improved irrigation techniques introduced "
    "last year. Agricultural officials say wheat and rice yields are up nearly twenty "
    "percent compared to the five-year average, providing a much-needed boost to rural "
    "incomes. Experts caution that continued investment in water management will be key "
    "to sustaining these gains into future seasons."
)

RUNS = 20


def time_function(name, fn, *args):
    durations = []
    for _ in range(RUNS):
        start = time.perf_counter()
        fn(*args)
        durations.append((time.perf_counter() - start) * 1000)
    durations.sort()
    p95 = durations[int(len(durations) * 0.95)]
    mean = sum(durations) / len(durations)
    print(f"{name:20} mean={mean:7.2f}ms  p95={p95:7.2f}ms")


print(f"Profiling on {len(SAMPLE_TEXT)} chars of text, {RUNS} runs each:\n")
time_function("detect_language", detect_language, SAMPLE_TEXT)
time_function("extract_entities", extract_entities, SAMPLE_TEXT)
time_function("score_sentiment", score_sentiment, SAMPLE_TEXT)
time_function("clean_enrichment_text", clean_enrichment_text, SAMPLE_TEXT)