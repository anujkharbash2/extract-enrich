import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from benchmarks.scorer import run_benchmark

MINIMUM_ACCEPTABLE_ACCURACY = 0.85  # matches the doc's Phase 1 exit criterion


def test_benchmark_meets_minimum_accuracy():
    report = run_benchmark()
    accuracy = report["summary"]["field_level_accuracy"]
    assert accuracy >= MINIMUM_ACCEPTABLE_ACCURACY, (
        f"Field-level accuracy {accuracy*100:.1f}% is below the {MINIMUM_ACCEPTABLE_ACCURACY*100:.0f}% "
        f"Phase 1 target. Full report: {report['results']}"
    )