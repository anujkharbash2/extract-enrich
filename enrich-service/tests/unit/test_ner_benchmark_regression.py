import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from benchmarks.ner_scorer import run_ner_benchmark

# Current measured recall is 81.8% with 2 known misses (Maharashtra, Facebook).
# Floor set slightly below that so genuine regressions are caught, without
# being so tight that normal noise on this tiny sample causes false alarms.
MINIMUM_RECALL = 0.75
MINIMUM_PRECISION = 0.90


def test_ner_meets_minimum_recall_and_precision():
    report = run_ner_benchmark()
    recall = report["summary"]["recall"]
    precision = report["summary"]["precision"]
    assert recall >= MINIMUM_RECALL, (
        f"NER recall {recall*100:.1f}% dropped below floor {MINIMUM_RECALL*100:.0f}%. "
        f"Per-case misses: {[c['missed'] for c in report['per_case'] if c['missed']]}"
    )
    assert precision >= MINIMUM_PRECISION, (
        f"NER precision {precision*100:.1f}% dropped below floor {MINIMUM_PRECISION*100:.0f}%."
    )