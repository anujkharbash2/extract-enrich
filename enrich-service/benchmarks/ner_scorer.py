import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ner import extract_entities

BENCHMARK_DIR = Path(__file__).parent


def entities_match(a: dict, b) -> bool:
    return a["text"].strip().lower() == b.text.strip().lower() and a["type"] == b.type


def run_ner_benchmark() -> dict:
    with open(BENCHMARK_DIR / "ner_ground_truth.json") as f:
        cases = json.load(f)

    total_expected = 0
    total_predicted = 0
    total_correct = 0
    per_case = []

    for case in cases:
        predicted = extract_entities(case["text"])
        expected = case["expected_entities"]

        matched_expected = set()
        matched_predicted = set()

        for i, exp in enumerate(expected):
            for j, pred in enumerate(predicted):
                if j in matched_predicted:
                    continue
                if entities_match(exp, pred):
                    matched_expected.add(i)
                    matched_predicted.add(j)
                    break

        correct = len(matched_expected)
        missed = [expected[i]["text"] for i in range(len(expected)) if i not in matched_expected]
        extra = [predicted[j].text for j in range(len(predicted)) if j not in matched_predicted]

        total_expected += len(expected)
        total_predicted += len(predicted)
        total_correct += correct

        per_case.append({
            "id": case["id"],
            "correct": correct,
            "expected_count": len(expected),
            "predicted_count": len(predicted),
            "missed": missed,
            "extra_false_positives": extra,
        })

    precision = round(total_correct / total_predicted, 4) if total_predicted else 1.0
    recall = round(total_correct / total_expected, 4) if total_expected else 1.0
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0

    return {
        "summary": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "total_expected": total_expected,
            "total_predicted": total_predicted,
            "total_correct": total_correct,
        },
        "per_case": per_case,
    }


if __name__ == "__main__":
    report = run_ner_benchmark()
    print(json.dumps(report, indent=2))
    print("\n=== SUMMARY ===")
    print(f"Precision: {report['summary']['precision']*100:.1f}%")
    print(f"Recall:    {report['summary']['recall']*100:.1f}%")
    print(f"F1:        {report['summary']['f1']*100:.1f}%")