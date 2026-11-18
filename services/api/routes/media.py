"""
Media Retrieval Route for SiteSense.
Streams raw or annotated media files to the client with access checks.
"""

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Media
from services.core.schemas import ErrorResponse

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/{id}", responses={404: {"model": ErrorResponse}})
def get_media_file(
    id: int,
    annotated: bool = Query(False, description="Whether to fetch annotated media"),
    db: Session = Depends(get_db)
):
    """
    Stream the original or annotated media file binary.
    """
    media = db.query(Media).filter(Media.id == id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "MEDIA_NOT_FOUND", "message": f"Media {id} not found", "detail": None}}
        )

    target_path = media.annotated_path if (annotated and media.annotated_path) else media.path
    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": f"File at {target_path} not found on disk", "detail": None}}
        )

    # Determine media mime type
    ext = Path(target_path).suffix.lower()
    media_type = "application/octet-stream"
    if ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif ext == ".png":
        media_type = "image/png"
    elif ext == ".pdf":
        media_type = "application/pdf"
    elif ext == ".mp4":
        media_type = "video/mp4"

    return FileResponse(target_path, media_type=media_type, filename=media.filename)

