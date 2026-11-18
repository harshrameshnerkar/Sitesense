"""
Policy Document Ingestion Route for SiteSense.
Handles uploading and indexing company compliance manuals and handbooks.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Policy
from services.core.schemas import PolicyIngestResponse

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("", response_model=list)
def list_policies(db: Session = Depends(get_db)):
    """
    List all registered company safety manuals and compliance handbooks.
    """
    policies = db.query(Policy).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "version": p.version,
            "effective_date": p.effective_date,
            "source_file": p.source_file,
            "chunks_count": p.chunks_count,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in policies
    ]


@router.post("", response_model=PolicyIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_policy(
    file: UploadFile = File(...),
    title: str = Form("Warehouse Operations & Compliance Manual"),
    version: str = Form("v2026.Q4"),
    effective_date: str = Form("2026-10-01"),
    db: Session = Depends(get_db)
):
    """
    Ingest a new company policy handbook, chunk with metadata, and register in database.
    """
    save_dir = Path("data/policies")
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "policy_manual.pdf"
    save_path = save_dir / filename

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Simulated chunk count (approx 1 chunk per 400 words)
    chunks_created = max(1, len(content) // 2048)

    policy = Policy(
        title=title,
        version=version,
        source_file=str(save_path),
        effective_date=effective_date,
        chunks_count=chunks_created
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return PolicyIngestResponse(
        policy_id=policy.id,
        chunks_created=policy.chunks_count
    )

