import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from benchmarks.enrich_latency_test import run_enrich_latency_benchmark

P95_TARGET_MS = 300  # doc's Phase 1 enrichment latency budget


def test_enrichment_latency_meets_target():
    report = run_enrich_latency_benchmark()
    assert report["overall_p95_ms"] <= P95_TARGET_MS, (
        f"Enrichment P95 latency {report['overall_p95_ms']}ms exceeds "
        f"the {P95_TARGET_MS}ms target. Per-text breakdown: {report['per_text']}"
    )