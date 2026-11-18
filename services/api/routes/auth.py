"""
Authentication Route for SiteSense.
Handles user registration, authentication, profile inspection, and session management.
Directly reads and writes to PostgreSQL users table.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import User
from services.core.schemas import (
    LoginRequest, SignUpRequest, TokenResponse, UserSummary, ErrorResponse
)
from services.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    """
    Register a new user in the PostgreSQL database.
    """
    # 1. Check if email already registered
    existing_user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMAIL_ALREADY_REGISTERED", "message": f"Email '{payload.email}' is already registered."}}
        )

    # 2. Normalize role
    norm_role = payload.role.lower().strip()
    if norm_role not in ("admin", "manager", "supervisor", "employee", "field", "reviewer"):
        norm_role = "employee"

    # 3. Auto-generate employee_id if omitted
    emp_id = payload.employee_id
    if not emp_id:
        user_count = db.query(User).count()
        emp_id = f"EMP-{user_count + 1:03d}"

    # 4. Create user in PostgreSQL
    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=f"hash_{payload.password}",
        role=norm_role,
        department=payload.department or "Operations Logistics",
        employee_id=emp_id,
        shift=payload.shift or "General Shift (08:00 - 17:00)",
        phone=payload.phone or "N/A"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = f"jwt_mock_token_user_{new_user.id}_{new_user.role}"

    return TokenResponse(
        token=token,
        user=UserSummary(
            id=new_user.id,
            employee_id=new_user.employee_id,
            name=new_user.name,
            email=new_user.email,
            role=new_user.role,
            department=new_user.department,
            shift=new_user.shift,
            phone=new_user.phone
        )
    )


@router.post("/login", response_model=TokenResponse, responses={401: {"model": ErrorResponse}})
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user against PostgreSQL with email and password.
    """
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password", "detail": None}}
        )

    # Allow standard demo passwords or hashed match
    stored = user.hashed_password or ""
    pwd = payload.password
    valid = (
        pwd in (stored, stored.replace("hash_", ""), "admin123", "manager123", "field123", "employee123", "password123")
        or stored.endswith(pwd)
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password", "detail": None}}
        )

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


@router.get("/me", response_model=UserSummary)
def get_current_user_profile(current_user: UserSummary = Depends(get_current_user)):
    """
    Retrieve profile of the currently logged-in user from PostgreSQL.
    """
    return current_user


@router.get("/users", response_model=List[UserSummary])
def list_registered_users(db: Session = Depends(get_db)):
    """
    List all active employees and users registered in PostgreSQL.
    """
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        UserSummary(
            id=u.id,
            employee_id=u.employee_id,
            name=u.name,
            email=u.email,
            role=u.role,
            department=u.department,
            shift=u.shift,
            phone=u.phone
        )
        for u in users
    ]

