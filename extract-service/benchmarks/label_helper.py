import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BENCHMARK_DIR = Path(__file__).parent
FIXTURES_DIR = BENCHMARK_DIR.parent / "tests" / "fixtures"
GROUND_TRUTH_PATH = BENCHMARK_DIR / "ground_truth.json"


def label_new_case(fixture_filename: str, final_url: str, case_id: str):
    """
    Runs current extraction on a saved HTML file, shows you the result,
    and lets you confirm or correct each field before saving it as a new
    ground-truth benchmark case.
    """
    fixture_path = FIXTURES_DIR / fixture_filename
    if not fixture_path.exists():
        print(f"ERROR: {fixture_path} does not exist. Save the HTML there first.")
        return

    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()

    response = client.post("/v1/extract", json={
        "html": html, "statusCode": 200, "renderTimeMs": 100,
        "finalUrl": final_url, "error": None, "proxyId": "labeling",
    })
    result = response.json()

    print(f"\n=== Extraction result for '{case_id}' ===")
    print(f"page_type: {result['page_type']}  (confidence: {result['confidence']})")
    print(f"extraction_method: {result['extraction_method']}")
    print("\nExtracted fields:")
    for key, value in result["fields"].items():
        print(f"  {key}: {value}")

    print("\n--- Now confirm the CORRECT values (press Enter to accept what was extracted) ---")

    confirmed_page_type = input(f"page_type [{result['page_type']}]: ").strip() or result["page_type"]

    confirmed_fields = {}
    skip_fields = {"images", "language", "entities", "sentiment", "skipped_reason"}
    for key, value in result["fields"].items():
        if key in skip_fields or value is None:
            continue
        user_input = input(f"{key} [{value}]: ").strip()
        confirmed_fields[key] = user_input if user_input else value

    new_case = {
        "id": case_id,
        "fixture_file": fixture_filename,
        "final_url": final_url,
        "expected_page_type": confirmed_page_type,
        "expected_fields": confirmed_fields,
    }

    with open(GROUND_TRUTH_PATH, "r") as f:
        ground_truth = json.load(f)

    existing_ids = [c["id"] for c in ground_truth]
    if case_id in existing_ids:
        print(f"\nWARNING: case_id '{case_id}' already exists. Skipping save. Use a unique id.")
        return

    ground_truth.append(new_case)
    with open(GROUND_TRUTH_PATH, "w") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"\n✅ Saved '{case_id}' to ground_truth.json. Total cases: {len(ground_truth)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m benchmarks.label_helper <fixture_filename> <final_url> <case_id>")
        print("Example: python -m benchmarks.label_helper flipkart_shoes.html https://flipkart.com/... flipkart_shoes_001")
        sys.exit(1)

    label_new_case(sys.argv[1], sys.argv[2], sys.argv[3])