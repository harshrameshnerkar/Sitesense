# SiteSense Operations Runbook

> **Guide for System Administrators, Evaluators, and Developers**  
> *Enables unassisted deployment, verification, and failure mode recovery from a clean clone.*

---

## 1. Quickstart Deployment

### Option A: Clean Local Setup (Python 3.11+)
```bash
# 1. Clone repository
git clone <repo-url>
cd Sitesense

# 2. Initialize virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize Database & Seed Data
python -m services.core.init_db

# 5. Start Application Gateway
uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000/` to access the full operational dashboard.

### Option B: Docker Compose Single-Command Deployment
```bash
docker compose up --build -d
```
All services (PostgreSQL database, API gateway, static frontend) will boot automatically.

---

## 2. Automated Evaluation Suite Execution

To verify all system benchmarks in a single command from a clean terminal:
```bash
python -m eval.run_all
```
Outputs the real-time performance metrics table for:
1. Computer Vision mAP@50
2. Grounded Policy Retrieval & Page Citation Accuracy
3. Out-of-Scope Safe Refusal Accuracy
4. Agent Intent Routing Accuracy
5. Document Intelligence Field Extraction Accuracy

---

## 3. Operational Failure Modes & Recovery Procedures

### 3.1 Failure Mode: PostgreSQL Offline / Connection Timeout
* **Symptom:** Logs show `Could not connect to configured PostgreSQL`.
* **Automatic Safeguard:** SiteSense automatically falls back to local SQLite database (`sitesense.db`) with zero crash.
* **Recovery:** When local PostgreSQL or Neon is ready, update `DATABASE_URL` in `.env` and restart the server.

### 3.2 Failure Mode: Low-Confidence Document Extractions
* **Symptom:** Scanned manifest fields are blurred or torn.
* **Automatic Safeguard:** Extractor assigns confidence < 0.80 and routes to `/review` queue.
* **Recovery:** Navigate to the **Review Queue** tab in the dashboard, review the proposed value, edit/correct if necessary, and click **Approve**.

### 3.3 Failure Mode: Adversarial Prompt Injection Attempt
* **Symptom:** Input contains `ignore previous instructions` or destructive SQL.
* **Automatic Safeguard:** `SecurityGuardrails` intercepts payload, returns `SECURITY_BLOCK` event, and halts tool execution.

---

## 4. Key Endpoints Reference

| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/health` | GET | Public | Healthcheck probe |
| `/auth/login` | POST | Public | User authentication token |
| `/inspections` | POST | Field / Admin | Multi-format upload & inspection start |
| `/jobs/{job_id}` | GET | All | Background pipeline status polling |
| `/chat` | POST | All | Streaming multimodal agent chat |
| `/review` | GET / POST | Reviewer / Admin | Human-in-the-loop validation queue |
| `/reports/{id}` | POST | Manager / Admin | Official PDF report export with evidence |
| `/dashboard/metrics`| GET | All | Real-time cross-site analytics |
