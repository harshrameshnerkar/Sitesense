"""
Week 1 Contract & Integration Test Suite.
Validates the end-to-end API specification, upload path, background job queue,
review queue routing, human-in-the-loop approval gate, and dashboard analytics.
"""

import time
from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


def test_week1_end_to_end_pipeline():
    print("==================================================")
    print("🧪 RUNNING WEEK 1 CONTRACT & SKELETON VERIFICATION")
    print("==================================================")

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("✅ 1. Health Check passed:", res.json())

    # 2. Authentication
    res = client.post("/auth/login", json={"email": "alice@sitesense.io", "password": "any_password"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    auth_data = res.json()
    assert "token" in auth_data
    assert auth_data["user"]["role"] == "field"
    print(f"✅ 2. Auth Login passed: Authenticated as {auth_data['user']['name']} ({auth_data['user']['role']})")

    # 3. List Sites
    res = client.get("/sites")
    assert res.status_code == 200
    sites = res.json()
    assert len(sites) >= 3
    site_7 = next(s for s in sites if "Site 7" in s["name"])
    print(f"✅ 3. Sites List passed: Found {len(sites)} sites, selected {site_7['name']} (ID: {site_7['id']})")

    # 4. Multi-format Upload (Image + Scratched PDF to exercise review queue)
    image_path = "data/images/warehouse_scene_walkway_blocked.jpg"
    doc_path = "data/delivery_notes/delivery_note_po98423_scratched.pdf"

    with open(image_path, "rb") as f_img, open(doc_path, "rb") as f_doc:
        files = [
            ("files", ("warehouse_scene_walkway_blocked.jpg", f_img, "image/jpeg")),
            ("files", ("delivery_note_po98423_scratched.pdf", f_doc, "application/pdf")),
        ]
        res = client.post(
            "/inspections",
            data={"site_id": site_7["id"], "user_id": auth_data["user"]["id"]},
            files=files
        )

    assert res.status_code == 202, f"Upload failed: {res.text}"
    upload_res = res.json()
    inspection_id = upload_res["inspection_id"]
    job_id = upload_res["job_id"]
    print(f"✅ 4. Asynchronous Upload passed: Created Inspection ID {inspection_id}, Job ID {job_id}")

    # 5. Poll Job Status
    res = client.get(f"/jobs/{job_id}")
    assert res.status_code == 200
    job_info = res.json()
    print(f"✅ 5. Job Polling passed: Status={job_info['status']}, Progress={job_info['progress']}%")

    # 6. Retrieve Full Inspection Detail & Findings
    res = client.get(f"/inspections/{inspection_id}")
    assert res.status_code == 200
    insp_detail = res.json()
    print(f"✅ 6. Inspection Detail retrieved:")
    print(f"    - Site: {insp_detail['site_name']}")
    print(f"    - Status: {insp_detail['status']}")
    print(f"    - Media Items: {len(insp_detail['media'])}")
    print(f"    - Vision Detections: {len(insp_detail['detections'])}")
    print(f"    - Document Extractions: {len(insp_detail['extractions'])}")
    print(f"    - Rule Findings: {len(insp_detail['findings'])}")

    for f in insp_detail["findings"]:
        print(f"      • [{f['status'].upper()}] {f['rule_name']} ({f['policy_ref']}): {f['explanation']}")

    # 7. Check Human Review Queue (Low-confidence extraction)
    res = client.get("/review")
    assert res.status_code == 200
    review_items = res.json()
    assert len(review_items) > 0, "Expected at least 1 low-confidence item in review queue"
    target_review = review_items[0]
    print(f"✅ 7. Human Review Queue populated: Flagged item ID {target_review['id']} ('{target_review['field_name']}' = '{target_review['proposed_value']}', confidence: {target_review['confidence']})")

    # 8. Review Action (Approve / Correct)
    res = client.post(f"/review/{target_review['id']}", json={"action": "accept"})
    assert res.status_code == 200
    assert res.json()["status"] == "approved"
    print(f"✅ 8. Review Queue Action passed: Item {target_review['id']} approved by reviewer.")

    # 9. Human Approval Gate for Remediation Ticket (Manager Role)
    failed_finding = next(f for f in insp_detail["findings"] if f["status"] == "fail")

    # Authenticate as Manager Dave
    res_mgr = client.post("/auth/login", json={"email": "manager@sitesense.io", "password": "password123"})
    assert res_mgr.status_code == 200
    mgr_token = res_mgr.json()["token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # 9a. Attempt ticket creation with approved=False -> Must be rejected!
    res_gate = client.post("/tickets", json={"finding_id": failed_finding["id"], "description": "Clear pallet", "approved": False}, headers=mgr_headers)
    assert res_gate.status_code == 400
    assert res_gate.json()["error"]["code"] == "APPROVAL_REQUIRED"
    print("✅ 9a. Human Approval Gate Held: Unapproved ticket creation was blocked by security policy.")

    # 9b. Submit ticket with approved=True -> Must succeed!
    res_ticket = client.post("/tickets", json={"finding_id": failed_finding["id"], "description": "Manager approved: Dispatch maintenance to clear walkway corridor.", "approved": True}, headers=mgr_headers)
    assert res_ticket.status_code == 200
    print(f"✅ 9b. Approved Ticket Created: Ticket ID {res_ticket.json()['ticket_id']} (Status: {res_ticket.json()['status']})")

    # 10. Dashboard Analytics Verification
    res_metrics = client.get("/dashboard/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    print(f"✅ 10. Dashboard Analytics verified:")
    print(f"    - Total Inspections: {metrics['inspections']}")
    print(f"    - Compliance Pass Rate: {metrics['pass_rate']}%")
    print(f"    - Top Failing Rules: {metrics['top_failing_rules']}")
    print(f"    - Pending Review Items: {metrics['pending_review']}")

    print("\n==================================================")
    print("🎉 ALL WEEK 1 CONTRACT & SKELETON TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    test_week1_end_to_end_pipeline()

