"""
Background Ingestion Tasks for SiteSense.
Executes the real multimodal inspection processing pipeline:
1. Vision detection & spatial zone evaluation
2. Annotated visual evidence generation
3. Structured PDF document extraction & confidence calibration
4. Compliance rule evaluation against written policy clauses
5. Final report summary and status update
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from services.core.database import SessionLocal
from services.core.models import Inspection, Media, Detection, Extraction, Finding, Rule
from services.vision.detector import VisionDetector
from services.vision.zones import ZoneEngine
from services.vision.annotator import annotate_image
from services.knowledge.extractor import DocumentExtractor
from services.core.rules_engine import ComplianceRulesEngine
from services.core.config import get_settings

logger = logging.getLogger("sitesense.tasks")
settings = get_settings()

# Default site zone layout
SITE_7_ZONES = [
    {
        "id": "walkway_a",
        "name": "Walkway A",
        "polygon": [[100, 200], [800, 200], [800, 720], [100, 720]],
        "type": "clearance_mandatory"
    },
    {
        "id": "loading_bay_4",
        "name": "Loading Bay",
        "polygon": [[800, 100], [1200, 100], [1200, 600], [800, 600]],
        "type": "ppe_helmet_required"
    }
]


def run_inspection_pipeline(inspection_id: int, job_id: str):
    """
    Executes the end-to-end multimodal inspection pipeline for an uploaded inspection session.
    """
    db: Session = SessionLocal()
    try:
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            logger.error(f"Inspection {inspection_id} not found in background task.")
            return

        logger.info(f"Executing real multimodal inspection pipeline for inspection_id={inspection_id}, job_id={job_id}")
        inspection.status = "processing"
        db.commit()

        # Initialize engines
        detector = VisionDetector()
        zone_engine = ZoneEngine(SITE_7_ZONES)
        extractor = DocumentExtractor()
        rules_engine = ComplianceRulesEngine()

        media_items = db.query(Media).filter(Media.inspection_id == inspection_id).all()

        recorded_detections = []
        recorded_extractions = []

        # ----------------------------------------------------
        # 1. Process Visual Media (Images / Video Frames)
        # ----------------------------------------------------
        for media in media_items:
            if media.type in ["image", "video"]:
                file_path = media.path
                if os.path.exists(file_path):
                    raw_dets = detector.detect(file_path)
                    det_dicts_for_annotator = []

                    for d in raw_dets:
                        zone_id = zone_engine.evaluate_zone(d.bbox)
                        detection_record = Detection(
                            media_id=media.id,
                            class_name=d.class_name,
                            bbox=d.bbox,
                            confidence=d.confidence,
                            zone=zone_id,
                            frame_no=0
                        )
                        db.add(detection_record)
                        db.flush()

                        det_dict = {
                            "id": detection_record.id,
                            "class_name": d.class_name,
                            "bbox": d.bbox,
                            "confidence": d.confidence,
                            "zone": zone_id
                        }
                        det_dicts_for_annotator.append(det_dict)
                        recorded_detections.append(det_dict)

                    # Generate visual evidence with drawn bounding boxes and zones
                    annotated_dir = Path(settings.ANNOTATED_DIR)
                    annotated_dir.mkdir(parents=True, exist_ok=True)
                    annotated_filename = f"annotated_{media.id}_{Path(file_path).name}"
                    annotated_out_path = str(annotated_dir / annotated_filename)

                    annotate_image(
                        image_path=file_path,
                        output_path=annotated_out_path,
                        detections=det_dicts_for_annotator,
                        zones=SITE_7_ZONES
                    )
                    media.annotated_path = annotated_out_path
                    db.commit()
                    logger.info(f"Generated annotated visual evidence: {annotated_out_path}")

            # ----------------------------------------------------
            # 2. Process Document Media (PDF Inbound Delivery Notes)
            # ----------------------------------------------------
            elif media.type == "doc":
                file_path = media.path
                if os.path.exists(file_path) and file_path.lower().endswith(".pdf"):
                    doc_extractions = extractor.extract_from_pdf(file_path)
                    for ext in doc_extractions:
                        ext_record = Extraction(
                            media_id=media.id,
                            field_name=ext.field_name,
                            value=ext.value,
                            confidence=ext.confidence,
                            review_status=ext.status
                        )
                        db.add(ext_record)
                        db.flush()
                        recorded_extractions.append(ext.to_dict())

                    db.commit()
                    logger.info(f"Extracted {len(doc_extractions)} structured fields from {media.filename}")

        # ----------------------------------------------------
        # 3. Evaluate Compliance Rules Against Policy Clauses
        # ----------------------------------------------------
        rules = db.query(Rule).filter(Rule.active == True).all()
        findings = rules_engine.evaluate(rules, recorded_detections, recorded_extractions)

        fail_count = 0
        pass_count = 0
        for f in findings:
            finding_record = Finding(
                inspection_id=inspection.id,
                rule_id=f["rule_id"],
                status=f["status"],
                evidence_ids=f["evidence_ids"],
                explanation=f["explanation"]
            )
            db.add(finding_record)
            if f["status"] == "fail":
                fail_count += 1
            elif f["status"] == "pass":
                pass_count += 1

        # ----------------------------------------------------
        # 4. Finalize Inspection Summary & Status
        # ----------------------------------------------------
        inspection.status = "completed"
        inspection.summary = (
            f"Automated multimodal inspection completed: {pass_count} rules passed, "
            f"{fail_count} non-compliance failures identified. "
            f"{len(recorded_detections)} objects detected with annotated visual evidence."
        )
        inspection.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Inspection pipeline completed successfully for job_id={job_id}")

    except Exception as e:
        logger.error(f"Error in inspection pipeline for job_id={job_id}: {e}", exc_info=True)
        db.rollback()
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if inspection:
            inspection.status = "failed"
            db.commit()
    finally:
        db.close()
