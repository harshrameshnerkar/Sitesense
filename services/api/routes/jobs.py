"""
Job Status Route for SiteSense.
Enables frontend clients to poll asynchronous inspection processing jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Inspection
from services.core.schemas import JobStatusResponse, ErrorResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse, responses={404: {"model": ErrorResponse}})
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Poll the status of an asynchronous inspection processing job by job_id.
    """
    inspection = db.query(Inspection).filter(Inspection.job_id == job_id).first()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found", "detail": None}}
        )

    progress = 100
    if inspection.status == "queued":
        progress = 10
    elif inspection.status == "processing":
        progress = 65
    elif inspection.status == "completed":
        progress = 100
    elif inspection.status == "failed":
        progress = 100

    error_msg = "Pipeline execution error occurred" if inspection.status == "failed" else None

    return JobStatusResponse(
        status=inspection.status,
        progress=progress,
        result_id=inspection.id,
        error=error_msg
    )

