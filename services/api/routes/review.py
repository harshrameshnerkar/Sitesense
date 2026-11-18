"""
Human Review Queue Route for SiteSense.
Enables human-in-the-loop validation of low-confidence document extractions and detections.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Extraction
from services.core.schemas import ReviewItem, ReviewActionRequest, ReviewActionResponse, ErrorResponse

router = APIRouter(prefix="/review", tags=["Review Queue"])


@router.get("", response_model=List[ReviewItem])
def get_review_items(
    type: Optional[str] = Query(None, description="extraction or detection"),
    db: Session = Depends(get_db)
):
    """
    Fetch all items currently flagged for human verification.
    """
    query = db.query(Extraction).filter(Extraction.review_status == "pending_review")
    extractions = query.all()

    result = []
    for ext in extractions:
        result.append(
            ReviewItem(
                id=ext.id,
                type="extraction",
                media_id=ext.media_id,
                field_name=ext.field_name,
                proposed_value=ext.value,
                confidence=ext.confidence
            )
        )
    return result


@router.post("/{id}", response_model=ReviewActionResponse, responses={404: {"model": ErrorResponse}})
def process_review_action(
    id: int,
    payload: ReviewActionRequest,
    reviewer_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Accept, correct, or reject a low-confidence item with attributed audit history.
    """
    ext = db.query(Extraction).filter(Extraction.id == id).first()
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ITEM_NOT_FOUND", "message": f"Review item {id} not found", "detail": None}}
        )

    action = payload.action.lower()
    if action == "accept":
        ext.review_status = "approved"
    elif action == "correct":
        ext.review_status = "corrected"
        if payload.corrected_value:
            ext.value = payload.corrected_value
    elif action == "reject":
        ext.review_status = "rejected"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_ACTION", "message": f"Action {action} not supported", "detail": None}}
        )

    ext.reviewed_by = reviewer_id
    db.commit()

    return ReviewActionResponse(
        id=ext.id,
        status=ext.review_status,
        reviewed_by=reviewer_id
    )

