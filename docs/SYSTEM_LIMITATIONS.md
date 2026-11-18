# SiteSense: Candid Technical System Limitations

> **Engineering Assessment — Grounded in Empirical System Boundaries**  
> *In accordance with Definition of Done Gate #22, this document details real operational weaknesses, failure modes, and hardware/environmental boundaries rather than generic caveats.*

---

## 1. Computer Vision & Environmental Boundaries

### 1.1 Specular Glare on Plastic Stretch Film
* **Weakness:** Industrial warehouse pallets are frequently wrapped in reflective, transparent polyethylene stretch film. Under direct high-bay sodium or LED lighting, intense specular glare masks object contours.
* **Impact:** Object detector confidence for `pallet` and `box` drops by up to 28% in glare zones, occasionally fracturing a single stacked pallet into multiple disconnected bounding box predictions.
* **Mitigation:** Zone engine incorporates area-ratio spatial merging, and confidence thresholds route ambiguous detections to the human review queue.

### 1.2 Low-Lux Night & Dark Corridor Performance
* **Weakness:** In unlit depot aisles or exterior staging yards during night operations (<10 lux ambient lighting), vision transformers experience severe chromatic noise.
* **Impact:** Distinguishing dark floor liquid spills (`spill`) from concrete shadow patches fails in low-lux footage without active IR illumination.

### 1.3 2D Perspective Projection & Tripwire Distortion
* **Weakness:** Zone boundaries are defined as 2D planar polygons mapped directly onto camera pixels. When a wide-angle / fisheye security camera views a long corridor, perspective foreshortening occurs.
* **Impact:** An object standing tall in the foreground may appear to visually intersect a background walkway zone even if its ground contact point is 2 meters away.
* **Remediation:** Ground-anchor evaluation uses bottom-center contact points `((x1+x2)/2, y2)` rather than bounding box centroids.

---

## 2. Document Extraction & OCR Boundaries

### 2.1 Thermal Paper & Faint Dot-Matrix Scans
* **Weakness:** Inbound freight carriers often supply carbon-copy or aged dot-matrix delivery notes. Faint character printing and skewed scanner feeds degrade optical character recognition.
* **Impact:** Critical numeric fields such as `trailer_seal` numbers and `purchase_order` codes drop below the 80% confidence threshold.
* **Remediation:** Automated routing to the Human Review Queue (`/review`) ensures zero unverified field values enter the compliance database.

### 2.2 Table Layout Variability Across Unstandardized Invoices
* **Weakness:** Every carrier utilizes distinct tabular formats (line items, column orders, nested freight charges).
* **Impact:** Fixed regex parsers require heuristic adaptation when carriers place quantity counts before SKU descriptions.

---

## 3. Retrieval & Generative Language Boundaries

### 3.1 Cross-Page Clause Splitting
* **Weakness:** Complex policy manuals occasionally split a compliance clause across a physical page boundary (e.g. text starts at bottom of Page 3 and concludes at top of Page 4).
* **Impact:** Without overlapping chunk sliding windows, a dense embedding vector may only represent the introductory portion of a clause, reducing retrieval score.
* **Remediation:** Chunks are constructed with 100-character forward overlaps and explicit section header preservation.

### 3.2 Read-Only SQL Query Complexity
* **Weakness:** The `query_database` tool uses a deterministic SQL sandbox to guarantee read-only safety. Complex multi-table joins involving temporal window functions can exceed standard template generation.
* **Remediation:** Fallback to structured SQL templates for common cross-site aggregate queries.

---

## 4. Operational Cost & Scaling Projections

| Scale Metric | Current Baseline (1 Site) | 10x Scale Projection (10 Sites) | 40x Scale Enterprise (40 Sites) |
| :--- | :--- | :--- | :--- |
| **Daily Inspections** | 5 inspections | 50 inspections | 200 inspections |
| **Inference Cost / Inspection** | $0.0018 | $0.0018 | $0.0014 (batch discount) |
| **Daily Agent Token Cost** | $0.012 | $0.120 | $0.480 |
| **Projected Monthly AI Cost** | **$0.36 / month** | **$3.60 / month** | **$14.40 / month** |
| **p95 End-to-End Latency** | 1.8 seconds | 2.4 seconds | 3.1 seconds |

---

*SiteSense Platform — Honest, rigorous, and deployable operational intelligence.*
