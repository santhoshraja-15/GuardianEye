"""
FastAPI Route Dependencies & Authorization Guards (Open Access Mode)
"""
from typing import Callable, List, Optional
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from backend.app.core.security import decode_token
from backend.app.database.session import get_db
from backend.app.models.user import User, Role

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieve current active user without requiring authentication.
    If a valid bearer token is provided, it resolves the specific user.
    Otherwise, it automatically returns the active system operator.
    """
    if credentials:
        token = credentials.credentials
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return user

    # Fallback to the first active user in the database
    user = db.query(User).filter(User.is_active == True).first()
    if user:
        return user

    # Create a default operator if none exists
    role = db.query(Role).first()
    if not role:
        role = Role(name="Admin", description="System Administrator", permissions="*")
        db.add(role)
        db.flush()

    user = User(
        email="operator@guardianeye.ai",
        hashed_password="not-required",
        full_name="GuardianEye Operator",
        is_active=True,
        is_superuser=True,
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Role check bypass: all features and routes are open and accessible to all users.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        return current_user

    return role_checker
