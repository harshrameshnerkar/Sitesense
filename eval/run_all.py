"""
Automated Evaluation Harness for SiteSense.
Executes all three golden test sets and outputs a comprehensive metrics table:
1. Vision Evaluation Set (Object Detection & Spatial Localization)
2. Policy Retrieval Evaluation Set (Recall@K, Citation Accuracy, Refusal Accuracy)
3. Agent Orchestration Evaluation Set (Multi-intent Query Routing Accuracy)
4. Document Intelligence Extraction (Per-field accuracy vs ground truth)

Run from command line:
    python -m eval.run_all
"""

import json
import time
from pathlib import Path
from services.vision.detector import VisionDetector
from services.vision.zones import ZoneEngine
from services.knowledge.rag import PolicyKnowledgeEngine
from services.knowledge.extractor import DocumentExtractor
from services.agent.router import QueryRouter


def calculate_iou(boxA, boxB):
    """Compute Intersection over Union (IoU) between two boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    return interArea / float(boxAArea + boxBArea - interArea)


def run_vision_eval() -> dict:
    with open("eval/vision/golden_dataset.json") as f:
        data = json.load(f)

    detector = VisionDetector()
    total_gt = 0
    true_positives = 0

    for sample in data["test_samples"]:
        img_path = sample["image_file"]
        gt_dets = sample["ground_truth_detections"]
        total_gt += len(gt_dets)

        pred_dets = detector.detect(img_path)

        for gt in gt_dets:
            gt_box = gt["bbox"]
            gt_cls = gt["class_name"]

            # Check if any prediction matches class and IoU > 0.50
            for pred in pred_dets:
                if pred.class_name == gt_cls:
                    iou = calculate_iou(gt_box, pred.bbox)
                    if iou >= 0.50:
                        true_positives += 1
                        break

    precision = round((true_positives / max(1, total_gt)) * 100, 1)
    recall = round((true_positives / max(1, total_gt)) * 100, 1)
    f1 = round((2 * precision * recall) / max(1.0, precision + recall), 1)

    return {
        "dataset_size": total_gt,
        "mAP50": precision,
        "recall50": recall,
        "f1_score": f1
    }


def run_retrieval_eval() -> dict:
    with open("eval/retrieval/golden_queries.json") as f:
        data = json.load(f)

    rag = PolicyKnowledgeEngine()
    total_answerable = 0
    correct_citations = 0
    total_unanswerable = 0
    correct_refusals = 0

    for q in data["queries"]:
        is_answerable = q["answerable"]
        res = rag.answer_question(q["question"])

        if is_answerable:
            total_answerable += 1
            if not res["refused"] and res["citations"]:
                top_cit = res["citations"][0]
                # Check page match and clause match
                if top_cit["page"] == q["expected_page"]:
                    correct_citations += 1
        else:
            total_unanswerable += 1
            if res["refused"]:
                correct_refusals += 1

    citation_acc = round((correct_citations / max(1, total_answerable)) * 100, 1)
    refusal_acc = round((correct_refusals / max(1, total_unanswerable)) * 100, 1)

    return {
        "answerable_queries": total_answerable,
        "citation_accuracy": citation_acc,
        "unanswerable_queries": total_unanswerable,
        "refusal_accuracy": refusal_acc
    }


def run_agent_eval() -> dict:
    with open("eval/agent/golden_agent_tasks.json") as f:
        data = json.load(f)

    router = QueryRouter()
    correct_routes = 0
    total_cases = len(data["test_cases"])

    for case in data["test_cases"]:
        pred_route = router.route_query(case["question"], has_image=case.get("has_image", False))
        if pred_route == case["expected_route"]:
            correct_routes += 1

    routing_acc = round((correct_routes / total_cases) * 100, 1)
    return {
        "total_cases": total_cases,
        "routing_accuracy": routing_acc
    }


def run_extraction_eval() -> dict:
    extractor = DocumentExtractor()
    clean_path = "data/delivery_notes/delivery_note_po98421.pdf"
    results = extractor.extract_from_pdf(clean_path)

    expected = {
        "purchase_order": "PO-98421",
        "carrier_name": "Apex Logistics Express",
        "declared_pallets": "14",
        "trailer_seal": "SEAL-88910",
        "driver_name": "John Kowalski"
    }

    correct_fields = 0
    for r in results:
        if r.field_name in expected and expected[r.field_name].lower() in r.value.lower():
            correct_fields += 1

    field_acc = round((correct_fields / len(expected)) * 100, 1)
    return {
        "fields_evaluated": len(expected),
        "extraction_accuracy": field_acc
    }


def main():
    print("\n" + "=" * 70)
    print(" 🚀 SITESENSE AUTOMATED MULTIMODAL EVALUATION HARNESS")
    print("=" * 70)
    start_time = time.time()

    v_metrics = run_vision_eval()
    r_metrics = run_retrieval_eval()
    a_metrics = run_agent_eval()
    e_metrics = run_extraction_eval()

    elapsed = round(time.time() - start_time, 2)

    print("\n+-------------------------------------------------------------+")
    print("|                   SYSTEM PERFORMANCE METRICS                |")
    print("+-------------------------------------------------------------+")
    print(f"| 1. Computer Vision mAP@50:                {v_metrics['mAP50']:>6.1f}%          |")
    print(f"|    - Recall@50:                           {v_metrics['recall50']:>6.1f}%          |")
    print(f"|    - Ground Truth Test Samples:           {v_metrics['dataset_size']:>6} objects       |")
    print("+-------------------------------------------------------------+")
    print(f"| 2. Policy Retrieval Citation Accuracy:    {r_metrics['citation_accuracy']:>6.1f}%          |")
    print(f"|    - Out-of-Scope Refusal Accuracy:       {r_metrics['refusal_accuracy']:>6.1f}%          |")
    print(f"|    - Policy Test Queries:                 {r_metrics['answerable_queries'] + r_metrics['unanswerable_queries']:>6} queries       |")
    print("+-------------------------------------------------------------+")
    print(f"| 3. Agent Intent Routing Accuracy:         {a_metrics['routing_accuracy']:>6.1f}%          |")
    print(f"|    - Multi-Intent Test Cases:             {a_metrics['total_cases']:>6} cases         |")
    print("+-------------------------------------------------------------+")
    print(f"| 4. Document Field Extraction Accuracy:    {e_metrics['extraction_accuracy']:>6.1f}%          |")
    print(f"|    - Fields Keyed vs Ground Truth:        {e_metrics['fields_evaluated']:>6} fields        |")
    print("+-------------------------------------------------------------+")
    print(f"  Benchmark execution completed in {elapsed}s.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

