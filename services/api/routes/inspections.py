"""
Inspections Route for SiteSense.
Handles multi-format upload, inspection listing, and detailed reports.
"""

import os
import uuid
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Site, Inspection, Media, Detection, Extraction, Finding, Rule
from services.core.schemas import (
    InspectionCreateResponse, InspectionListItem, InspectionDetailResponse,
    MediaItem, DetectionItem, ExtractionItem, FindingItem, ErrorResponse
)
from services.core.config import get_settings
from services.api.tasks import run_inspection_pipeline

router = APIRouter(prefix="/inspections", tags=["Inspections"])
settings = get_settings()


@router.post("", response_model=InspectionCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_inspection(
    background_tasks: BackgroundTasks,
    site_id: int = Form(...),
    user_id: int = Form(1),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Accept multi-format upload (images, videos, PDFs), register inspection,
    and kick off asynchronous processing pipeline.
    """
    # 1. Validate site exists
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SITE_NOT_FOUND", "message": f"Site with ID {site_id} does not exist", "detail": None}}
        )

    # 2. Create inspection record
    job_id = str(uuid.uuid4())
    inspection = Inspection(
        site_id=site_id,
        user_id=user_id,
        job_id=job_id,
        status="queued"
    )
    db.add(inspection)
    db.flush()

    # 3. Store uploaded files & register media records
    upload_dir = Path(settings.UPLOAD_DIR) / str(inspection.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    for upload_file in files:
        filename = upload_file.filename or "upload.dat"
        file_path = upload_dir / filename
        
        # Read and save file content
        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Infer media type
        ext = file_path.suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            m_type = "image"
        elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
            m_type = "video"
        elif ext in [".pdf", ".docx", ".txt"]:
            m_type = "doc"
        else:
            m_type = "doc"

        media = Media(
            inspection_id=inspection.id,
            type=m_type,
            filename=filename,
            path=str(file_path),
            metadata_json={"file_size": len(content), "extension": ext}
        )
        db.add(media)

    db.commit()

    # 4. Enqueue background processing
    background_tasks.add_task(run_inspection_pipeline, inspection.id, job_id)

    return InspectionCreateResponse(
        inspection_id=inspection.id,
        job_id=job_id,
        status="queued"
    )


@router.get("", response_model=List[InspectionListItem])
def list_inspections(
    site_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List past inspections with calculated rule pass rates.
    """
    query = db.query(Inspection)
    if site_id:
        query = query.filter(Inspection.site_id == site_id)

    inspections = query.order_by(Inspection.created_at.desc()).offset(offset).limit(limit).all()

    result = []
    for insp in inspections:
        total_findings = len(insp.findings)
        pass_count = sum(1 for f in insp.findings if f.status == "pass")
        pass_rate = round((pass_count / total_findings * 100), 1) if total_findings > 0 else 0.0

        result.append(
            InspectionListItem(
                id=insp.id,
                site=insp.site.name if insp.site else f"Site {insp.site_id}",
                date=insp.created_at.strftime("%Y-%m-%d %H:%M UTC") if insp.created_at else "",
                status=insp.status,
                pass_rate=pass_rate
            )
        )
    return result


@router.get("/{id}", response_model=InspectionDetailResponse)
def get_inspection_detail(id: int, db: Session = Depends(get_db)):
    """
    Retrieve full inspection details including media, detections, extractions, and findings.
    """
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "INSPECTION_NOT_FOUND", "message": f"Inspection {id} not found", "detail": None}}
        )

    # Detections & Extractions across media
    detections_list = []
    extractions_list = []
    media_list = []

    for m in inspection.media:
        media_list.append(
            MediaItem(
                id=m.id,
                type=m.type,
                filename=m.filename,
                path=m.path,
                annotated_path=m.annotated_path
            )
        )
        for d in m.detections:
            detections_list.append(
                DetectionItem(
                    id=d.id,
                    class_name=d.class_name,
                    bbox=d.bbox,
                    confidence=d.confidence,
                    zone=d.zone,
                    frame_no=d.frame_no
                )
            )
        for e in m.extractions:
            extractions_list.append(
                ExtractionItem(
                    id=e.id,
                    field_name=e.field_name,
                    value=e.value,
                    confidence=e.confidence,
                    review_status=e.review_status
                )
            )

    findings_list = []
    for f in inspection.findings:
        findings_list.append(
            FindingItem(
                id=f.id,
                rule_name=f.rule.name if f.rule else f"Rule {f.rule_id}",
                policy_ref=f.rule.policy_ref if f.rule else "",
                status=f.status,
                explanation=f.explanation,
                evidence_ids=f.evidence_ids or []
            )
        )

    return InspectionDetailResponse(
        inspection_id=inspection.id,
        site_name=inspection.site.name if inspection.site else "",
        status=inspection.status,
        created_at=inspection.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if inspection.created_at else "",
        summary=inspection.summary,
        media=media_list,
        detections=detections_list,
        extractions=extractions_list,
        findings=findings_list
    )

