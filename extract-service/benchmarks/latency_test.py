import json
import time
import sys
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BENCHMARK_DIR = Path(__file__).parent
FIXTURES_DIR = BENCHMARK_DIR.parent / "tests" / "fixtures"

# Doc's Phase 1 exit criterion for Team 2
P95_TARGET_MS = 500

# Run each fixture multiple times to get a stable distribution -
# a single run is noisy (OS scheduling, warm/cold cache effects).
RUNS_PER_FIXTURE = 20


def measure_latency(fixture_file: str, final_url: str) -> list[float]:
    fixture_path = FIXTURES_DIR / fixture_file
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()

    payload = {
        "html": html,
        "statusCode": 200,
        "renderTimeMs": 100,
        "finalUrl": final_url,
        "error": None,
        "proxyId": "latency-test",
    }

    durations_ms = []
    for _ in range(RUNS_PER_FIXTURE):
        start = time.perf_counter()
        response = client.post("/v1/extract", json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        durations_ms.append(elapsed_ms)

    return durations_ms


def percentile(data: list[float], pct: float) -> float:
    sorted_data = sorted(data)
    index = int(len(sorted_data) * pct)
    index = min(index, len(sorted_data) - 1)
    return sorted_data[index]


def run_latency_benchmark():
    with open(BENCHMARK_DIR / "ground_truth.json") as f:
        cases = json.load(f)

    all_durations = []
    per_case_results = []

    for case in cases:
        durations = measure_latency(case["fixture_file"], case["final_url"])
        all_durations.extend(durations)

        per_case_results.append({
            "id": case["id"],
            "mean_ms": round(statistics.mean(durations), 2),
            "p95_ms": round(percentile(durations, 0.95), 2),
            "max_ms": round(max(durations), 2),
        })

    overall_p95 = percentile(all_durations, 0.95)

    return {
        "overall_p95_ms": round(overall_p95, 2),
        "overall_mean_ms": round(statistics.mean(all_durations), 2),
        "target_p95_ms": P95_TARGET_MS,
        "meets_target": overall_p95 <= P95_TARGET_MS,
        "per_case": per_case_results,
    }


if __name__ == "__main__":
    report = run_latency_benchmark()
    print(json.dumps(report, indent=2))
    print("\n=== SUMMARY ===")
    print(f"Overall P95 latency: {report['overall_p95_ms']}ms")
    print(f"Doc's Phase 1 target: <={P95_TARGET_MS}ms")
    print(f"Meets target: {report['meets_target']}")