import time
import sys
import statistics
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Doc's Phase 1 exit criterion: enrichment should add <=300ms on top of extraction
P95_TARGET_MS = 300
RUNS = 20

SAMPLE_TEXTS = [
    "Farmers across the region are reporting one of the best harvests in a decade, "
    "thanks to favorable monsoon patterns and improved irrigation techniques.",

    "Prime Minister Narendra Modi met with representatives from Tata Group and "
    "Infosys in New Delhi on Friday to discuss investment opportunities.",

    "Reliance Industries announced a partnership with Google and Facebook to "
    "expand digital services across India, with CEO Mukesh Ambani calling it "
    "a landmark deal that could reshape the country's digital economy over "
    "the coming decade, according to analysts who reviewed the announcement.",
]


def percentile(data: list[float], pct: float) -> float:
    sorted_data = sorted(data)
    index = min(int(len(sorted_data) * pct), len(sorted_data) - 1)
    return sorted_data[index]


def run_enrich_latency_benchmark() -> dict:
    all_durations = []
    per_text_results = []

    for i, text in enumerate(SAMPLE_TEXTS):
        durations = []
        for _ in range(RUNS):
            start = time.perf_counter()
            response = client.post("/v1/enrich", json={"text": text})
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            durations.append(elapsed_ms)

        all_durations.extend(durations)
        per_text_results.append({
            "sample_index": i,
            "char_count": len(text),
            "mean_ms": round(statistics.mean(durations), 2),
            "p95_ms": round(percentile(durations, 0.95), 2),
        })

    overall_p95 = percentile(all_durations, 0.95)

    return {
        "overall_p95_ms": round(overall_p95, 2),
        "overall_mean_ms": round(statistics.mean(all_durations), 2),
        "target_p95_ms": P95_TARGET_MS,
        "meets_target": overall_p95 <= P95_TARGET_MS,
        "per_text": per_text_results,
    }


if __name__ == "__main__":
    report = run_enrich_latency_benchmark()
    print(report)
    print(f"\nOverall P95: {report['overall_p95_ms']}ms (target: <={P95_TARGET_MS}ms)")
    print(f"Meets target: {report['meets_target']}")