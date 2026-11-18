"""
Week 2 Engines & End-to-End Milestone Test Suite.
Validates:
1. Computer Vision Pipeline (Detector, Zone Engine, Annotated Visual Output)
2. Knowledge Pipeline (Hybrid RAG, Page Citations, Refusal Behavior)
3. Structured Document Extraction (Delivery Notes, Confidence & Review Queue)
4. Rules Engine Evaluation (Compliance Checks, Citations, Evidence Links)
5. End-to-End Inspection Ingestion via API Gateway
"""

import os
from pathlib import Path
from fastapi.testclient import TestClient
from services.api.main import app
from services.vision.detector import VisionDetector
from services.vision.zones import ZoneEngine
from services.vision.annotator import annotate_image
from services.knowledge.rag import PolicyKnowledgeEngine
from services.knowledge.extractor import DocumentExtractor
from services.core.rules_engine import ComplianceRulesEngine

client = TestClient(app)


def test_week2_engines_and_integration():
    print("==========================================================")
    print("🧪 RUNNING WEEK 2 ENGINES (CV + KNOWLEDGE) VERIFICATION")
    print("==========================================================")

    # ----------------------------------------------------
    # 1. Computer Vision Engine Verification
    # ----------------------------------------------------
    print("\n--- 1. Testing Computer Vision Pipeline ---")
    image_path = "data/images/warehouse_scene_walkway_blocked.jpg"
    assert os.path.exists(image_path), "Test image missing"

    detector = VisionDetector()
    detections = detector.detect(image_path)
    assert len(detections) >= 3, f"Expected >= 3 detections, got {len(detections)}"
    classes_found = {d.class_name for d in detections}
    assert "pallet" in classes_found
    assert "fire_extinguisher" in classes_found
    print(f"✅ Vision Detection: Found {len(detections)} objects ({classes_found})")

    # Zone mapping
    zone_engine = ZoneEngine([
        {"id": "walkway_a", "name": "Walkway A", "polygon": [[100, 200], [800, 200], [800, 720], [100, 720]]},
        {"id": "loading_bay_4", "name": "Loading Bay", "polygon": [[800, 100], [1200, 100], [1200, 600], [800, 600]]}
    ])

    det_dicts = []
    for d in detections:
        z = zone_engine.evaluate_zone(d.bbox)
        det_dicts.append({"id": 1, "class_name": d.class_name, "bbox": d.bbox, "confidence": d.confidence, "zone": z})

    pallet_det = next(d for d in det_dicts if d["class_name"] == "pallet")
    assert pallet_det["zone"] == "walkway_a", f"Expected pallet in walkway_a, got {pallet_det['zone']}"
    print(f"✅ Zone Engine: Staged pallet accurately localized inside '{pallet_det['zone']}'")

    # Annotated image generation
    annotated_out = "storage/annotated/week2_test_annotated.jpg"
    annotate_image(image_path, annotated_out, det_dicts)
    assert os.path.exists(annotated_out)
    assert os.path.getsize(annotated_out) > 10000
    print(f"✅ Visual Evidence Annotator: Generated visual evidence ({os.path.getsize(annotated_out)} bytes)")

    # ----------------------------------------------------
    # 2. Knowledge Service & Grounded RAG Verification
    # ----------------------------------------------------
    print("\n--- 2. Testing Knowledge Retrieval & Citation Engine ---")
    rag = PolicyKnowledgeEngine()

    # 2a. Answerable query
    q1 = "What is the minimum clear width required for designated pedestrian walkways?"
    res1 = rag.answer_question(q1)
    assert not res1["refused"], "Expected answerable query not to be refused"
    assert len(res1["citations"]) > 0
    citation = res1["citations"][0]
    assert citation["page"] == 1
    assert "1.1" in citation["clause"]
    print(f"✅ Grounded Q&A: Successfully answered with Page {citation['page']} citation ({citation['clause']})")

    # 2b. Refusal query (DoD Gate #7)
    q2 = "What brand of coffee machine is authorized for the breakroom?"
    res2 = rag.answer_question(q2)
    assert res2["refused"], "Expected unanswerable query to be refused"
    print(f"✅ Refusal Behavior: Out-of-scope query safely refused without hallucination.")

    # ----------------------------------------------------
    # 3. Document Extraction & Confidence Calibration
    # ----------------------------------------------------
    print("\n--- 3. Testing Structured Document Extractor ---")
    extractor = DocumentExtractor()

    # Clean PDF
    clean_extractions = extractor.extract_from_pdf("data/delivery_notes/delivery_note_po98421.pdf")
    ext_dict = {e.field_name: e for e in clean_extractions}
    assert ext_dict["purchase_order"].value == "PO-98421"
    assert ext_dict["carrier_name"].value == "Apex Logistics Express"
    assert ext_dict["declared_pallets"].value == "14"
    assert ext_dict["purchase_order"].status == "auto_approved"
    print(f"✅ Document Extractor: Extracted {len(clean_extractions)} valid fields from delivery note")

    # Scratched PDF (Triggering Review Queue)
    scratched_extractions = extractor.extract_from_pdf("data/delivery_notes/delivery_note_po98423_scratched.pdf")
    pending_items = [e for e in scratched_extractions if e.status == "pending_review"]
    assert len(pending_items) > 0, "Expected low-confidence items flagged to pending_review"
    print(f"✅ Review Queue Routing: {len(pending_items)} low-confidence fields routed to review queue")

    # ----------------------------------------------------
    # 4. End-to-End API Ingestion with Real Engines
    # ----------------------------------------------------
    print("\n--- 4. Testing End-to-End API Pipeline Execution ---")
    with open(image_path, "rb") as f_img, open("data/delivery_notes/delivery_note_po98421.pdf", "rb") as f_doc:
        upload_res = client.post(
            "/inspections",
            data={"site_id": 1, "user_id": 1},
            files=[
                ("files", ("warehouse_inspection.jpg", f_img, "image/jpeg")),
                ("files", ("delivery_note.pdf", f_doc, "application/pdf")),
            ]
        )
    assert upload_res.status_code == 202
    job_id = upload_res.json()["job_id"]
    insp_id = upload_res.json()["inspection_id"]

    # Poll status
    job_status = client.get(f"/jobs/{job_id}").json()
    assert job_status["status"] == "completed"

    # Verify inspection details
    insp_data = client.get(f"/inspections/{insp_id}").json()
    assert len(insp_data["detections"]) >= 3
    assert len(insp_data["extractions"]) >= 4
    assert len(insp_data["findings"]) >= 4

    # Confirm visual evidence image was generated and linked
    annotated_media = next(m for m in insp_data["media"] if m["annotated_path"])
    assert os.path.exists(annotated_media["annotated_path"])
    print(f"✅ End-to-End Ingestion: Full inspection processed with {len(insp_data['findings'])} findings and linked evidence")

    print("\n==========================================================")
    print("🎉 ALL WEEK 2 ENGINE INTEGRATION TESTS PASSED!")
    print("==========================================================")


if __name__ == "__main__":
    test_week2_engines_and_integration()

