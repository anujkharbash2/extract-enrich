import json
import sys
from pathlib import Path
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent.parent))  # so `app` imports work

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BENCHMARK_DIR = Path(__file__).parent
FIXTURES_DIR = BENCHMARK_DIR.parent / "tests" / "fixtures"

# How similar two strings must be (0-1) to count as a "match" for text fields.
# Exact match isn't realistic for long body text; this allows for minor
# whitespace/formatting differences while still catching real extraction failures.
TEXT_SIMILARITY_THRESHOLD = 0.85


def text_similarity(a: str, b: str) -> float:
    if a is None or b is None:
        return 0.0
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def run_benchmark() -> dict:
    with open(BENCHMARK_DIR / "ground_truth.json") as f:
        cases = json.load(f)

    results = []
    correct_page_type = 0
    field_matches = 0
    field_total = 0

    for case in cases:
        fixture_path = FIXTURES_DIR / case["fixture_file"]
        with open(fixture_path, "r", encoding="utf-8") as f:
            html = f.read()

        response = client.post("/v1/extract", json={
            "html": html,
            "statusCode": 200,
            "renderTimeMs": 100,
            "finalUrl": case["final_url"],
            "error": None,
            "proxyId": "benchmark",
        })
        actual = response.json()

        page_type_correct = actual["page_type"] == case["expected_page_type"]
        if page_type_correct:
            correct_page_type += 1

        case_field_results = {}
        for field_name, expected_value in case["expected_fields"].items():
            actual_value = actual["fields"].get(field_name)
            field_total += 1

            if isinstance(expected_value, str) and isinstance(actual_value, str):
                similarity = text_similarity(expected_value, actual_value)
                is_match = similarity >= TEXT_SIMILARITY_THRESHOLD
            else:
                is_match = actual_value == expected_value
                similarity = 1.0 if is_match else 0.0

            if is_match:
                field_matches += 1

            case_field_results[field_name] = {
                "expected": expected_value,
                "actual": actual_value,
                "match": is_match,
                "similarity": round(similarity, 3),
            }

        results.append({
            "id": case["id"],
            "page_type_correct": page_type_correct,
            "extraction_method": actual.get("extraction_method"),
            "confidence": actual.get("confidence"),
            "fields": case_field_results,
        })

    total_cases = len(cases)
    summary = {
        "total_cases": total_cases,
        "page_type_accuracy": round(correct_page_type / total_cases, 4) if total_cases else 0,
        "field_level_accuracy": round(field_matches / field_total, 4) if field_total else 0,
        "field_matches": field_matches,
        "field_total": field_total,
    }

    return {"summary": summary, "results": results}


if __name__ == "__main__":
    report = run_benchmark()
    print(json.dumps(report, indent=2))
    print("\n=== SUMMARY ===")
    print(f"Page-type accuracy: {report['summary']['page_type_accuracy'] * 100:.1f}%")
    print(f"Field-level accuracy: {report['summary']['field_level_accuracy'] * 100:.1f}% "
          f"({report['summary']['field_matches']}/{report['summary']['field_total']} fields)")
    print(f"Doc's Phase 1 target: >=85% field-level accuracy")