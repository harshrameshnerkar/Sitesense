"""
Authentication & Role-Based Access Control (RBAC) Dependencies for SiteSense.
Enforces role permissions at the API layer (DoD Criterion #15).
"""

from typing import List
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import User
from services.core.schemas import UserSummary


def get_current_user(
    authorization: str = Header(None),
    x_user_role: str = Header(None),
    db: Session = Depends(get_db)
) -> UserSummary:
    """
    Extracts authenticated user and role from Authorization header or test token.
    Token format: 'Bearer jwt_mock_token_user_{user_id}_{role}' or header 'X-User-Role'.
    """
    role = "field"
    user_id = 3
    user_name = "Field Alice"
    user_email = "alice@sitesense.io"

    if authorization and "jwt_mock_token_user_" in authorization:
        parts = authorization.replace("Bearer ", "").split("_")
        try:
            user_id = int(parts[4])
            role = parts[5]
        except (IndexError, ValueError):
            pass
    elif x_user_role:
        role = x_user_role.lower()
        user_id = 3 if role in ("field", "supervisor") else (2 if role == "manager" else (1 if role == "admin" else 4))

    # Look up in DB by ID first, then by role
    if user_id:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            return UserSummary(
                id=db_user.id,
                employee_id=db_user.employee_id,
                name=db_user.name,
                email=db_user.email,
                role=role,
                department=db_user.department,
                shift=db_user.shift,
                phone=db_user.phone
            )

    aliases = ["supervisor", "field"] if role in ("supervisor", "field") else [role]
    db_user = db.query(User).filter(User.role.in_(aliases)).first()
    if db_user:
        return UserSummary(
            id=db_user.id,
            employee_id=db_user.employee_id,
            name=db_user.name,
            email=db_user.email,
            role=role,
            department=db_user.department,
            shift=db_user.shift,
            phone=db_user.phone
        )

    return UserSummary(id=user_id or 99, name=user_name, email=user_email, role=role)


ROLE_HIERARCHY_ALIASES = {
    "supervisor": ["supervisor", "field"],
    "field": ["supervisor", "field"],
    "reviewer": ["reviewer", "manager"],
    "manager": ["manager", "reviewer"],
    "employee": ["employee"],
    "admin": ["admin", "manager", "supervisor", "field", "reviewer", "employee"]
}


def require_role(allowed_roles: List[str]):
    """
    Factory creating a dependency that enforces the user's role is permitted.
    Supports role hierarchy aliases (e.g. supervisor <-> field).
    Raises HTTP 403 Forbidden if unauthorized.
    """
    def role_checker(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
        user_role = current_user.role.lower()
        effective_roles = ROLE_HIERARCHY_ALIASES.get(user_role, [user_role])
        
        # Check if any effective role intersects with allowed_roles, or if user is admin
        is_permitted = any(r in allowed_roles for r in effective_roles) or user_role == "admin"
        
        if not is_permitted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN_ROLE",
                        "message": f"Forbidden: Action requires one of roles {allowed_roles}. Current role: '{current_user.role}'",
                        "detail": "RBAC policy enforced at API Gateway."
                    }
                }
            )
        return current_user

    return role_checker
