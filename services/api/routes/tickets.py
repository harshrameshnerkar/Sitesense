"""
Maintenance Tickets Route for SiteSense.
Enforces the human-in-the-loop approval gate and API-level RBAC for remediation tickets.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Finding, Ticket
from services.core.schemas import TicketCreateRequest, TicketResponse, ErrorResponse, UserSummary
from services.api.deps import require_role

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
def create_ticket(
    payload: TicketCreateRequest,
    current_user: UserSummary = Depends(require_role(["manager", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Create a remediation ticket from a failed finding.
    Strictly enforces:
    1. Role-Based Access Control: Caller must be a Manager or Admin (DoD #15).
    2. Human Approval Gate: 'approved' must be True (DoD #13).
    """
    if not payload.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "APPROVAL_REQUIRED", "message": "Ticket creation rejected: Human approval gate is mandatory.", "detail": None}}
        )

    finding = db.query(Finding).filter(Finding.id == payload.finding_id).first()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FINDING_NOT_FOUND", "message": f"Finding {payload.finding_id} not found", "detail": None}}
        )

    # Check if a ticket already exists for this finding
    existing_ticket = db.query(Ticket).filter(Ticket.finding_id == payload.finding_id).first()
    if existing_ticket:
        return TicketResponse(ticket_id=existing_ticket.id, status=existing_ticket.status)

    ticket = Ticket(
        finding_id=payload.finding_id,
        status="approved",
        description=payload.description,
        created_by="agent",
        approved_by=current_user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketResponse(
        ticket_id=ticket.id,
        status=ticket.status
    )
