# NER Accuracy Report

Model: spaCy `en_core_web_sm` (tokenizer + NER only; tagger/parser/lemmatizer disabled for speed - see Step 15)
Scope: English text only, entity types: person, organization, location

## Run 1 — n=3 ground-truth cases (hand-labeled)
- Precision: 100.0%
- Recall: 81.8%
- F1: 90.0%

## Known misses (documented, not hidden)
1. **"Maharashtra"** missed as a location in "...investment opportunities in
   Maharashtra and Karnataka" - Karnataka was correctly caught in the same
   sentence. Likely a training-data gap in the small model for certain
   Indian state names.
2. **"Facebook"** missed as an organization in "...partnership with Google
   and Facebook..." - Google was correctly caught in the same sentence.
   Not an Indian-specific gap; appears to be a genuine weak spot in
   en_core_web_sm's handling of this specific phrasing/context.

## No false positives observed
Precision is 100% on this sample - every entity we did extract was correct.
The gap is entirely recall (missed entities), not incorrect extractions.

## Limitations of this report
n=3 cases, 11 total expected entities - too small to be statistically
reliable. This documents real, reproducible misses, but does not yet
represent true population-level accuracy. Should be re-run as the ground
truth set grows (target: real article samples from design-partner content,
per the doc's Month 4 validation step).

## Considered but not done
Switching to a larger spaCy model (en_core_web_md or _lg) would likely
improve recall but costs more memory/latency - worth revisiting only if
recall on a larger, real sample proves inadequate for the product need.