"""
Audit Trail Route for SiteSense.
Provides an immutable queryable log of system actions, approvals, and agent runs.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import AgentRun, Ticket
from services.core.schemas import AuditLogItem

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("", response_model=List[AuditLogItem])
def get_audit_log(
    user_id: Optional[int] = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Query the complete system audit trail across human approvals and agent executions.
    """
    runs = db.query(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit).all()

    audit_records = []
    for r in runs:
        audit_records.append(
            AuditLogItem(
                timestamp=r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if r.created_at else "",
                user=f"User {r.user_id or 'System'}",
                action=f"Agent Run ({r.route})",
                detail=f"Q: '{r.question[:40]}...' | Tools: {len(r.tools_called or [])} | Cost: ${r.cost:.4f}"
            )
        )

    # Add approved tickets to audit
    tickets = db.query(Ticket).filter(Ticket.status == "approved").limit(limit).all()
    for t in tickets:
        audit_records.append(
            AuditLogItem(
                timestamp=t.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if t.created_at else "",
                user=f"Manager {t.approved_by or 'System'}",
                action="Ticket Approved",
                detail=f"Approved remediation ticket {t.id} for finding {t.finding_id}: '{t.description[:40]}...'"
            )
        )

    return audit_records

