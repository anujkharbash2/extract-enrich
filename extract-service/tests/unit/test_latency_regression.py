import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from benchmarks.latency_test import run_latency_benchmark

P95_TARGET_MS = 500  # doc's Phase 1 exit criterion


def test_extraction_latency_meets_target():
    report = run_latency_benchmark()
    assert report["overall_p95_ms"] <= P95_TARGET_MS, (
        f"P95 latency {report['overall_p95_ms']}ms exceeds the {P95_TARGET_MS}ms target. "
        f"Per-case breakdown: {report['per_case']}"
    )