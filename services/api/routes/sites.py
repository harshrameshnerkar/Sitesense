"""
Sites Route for SiteSense.
Lists physical facilities accessible to the caller.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Site
from services.core.schemas import SiteResponse

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("", response_model=List[SiteResponse])
def list_sites(db: Session = Depends(get_db)):
    """
    List all physical facilities under inspection.
    """
    sites = db.query(Site).filter(Site.active == True).all()
    return sites

