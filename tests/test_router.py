"""
Benchmark Test for Agent Query Router.
"""

import json
from services.agent.router import QueryRouter


def benchmark_router():
    with open("eval/agent/golden_agent_tasks.json") as f:
        data = json.load(f)

    router = QueryRouter()
    correct = 0
    total = len(data["test_cases"])

    print("=== Benchmarking Query Router on Golden Agent Set ===")
    for case in data["test_cases"]:
        has_img = case.get("has_image", False)
        predicted = router.route_query(case["question"], has_image=has_img)
        is_correct = (predicted == case["expected_route"])
        if is_correct:
            correct += 1
        mark = "PASS" if is_correct else "FAIL"
        print(f"[{mark}] Q: '{case['question'][:40]}...' -> Pred: {predicted} | Exp: {case['expected_route']}")

    accuracy = (correct / total) * 100
    print(f"\nFinal Routing Accuracy: {accuracy:.1f}% ({correct}/{total})")
    assert accuracy >= 90.0, f"Router accuracy too low: {accuracy}%"


if __name__ == "__main__":
    benchmark_router()

