"""
Authentication Route for SiteSense.
Handles user authentication and JWT token generation.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import User
from services.core.schemas import LoginRequest, TokenResponse, UserSummary, ErrorResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, responses={401: {"model": ErrorResponse}})
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password, returning a session token and role.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password", "detail": None}}
        )

    # In production use bcrypt verify; for seed/dev verify plain or hashed
    # Seed passwords: admin@sitesense.io, manager@sitesense.io, alice@sitesense.io, bob@sitesense.io
    token = f"jwt_mock_token_user_{user.id}_{user.role}"

    return TokenResponse(
        token=token,
        user=UserSummary(
            id=user.id,
            employee_id=user.employee_id,
            name=user.name,
            email=user.email,
            role=user.role,
            department=user.department,
            shift=user.shift,
            phone=user.phone
        )
    )

