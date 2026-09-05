"""
FastAPI Route Dependencies & Authorization Guards
"""
from typing import Callable, List
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from backend.app.core.errors import AuthenticationException, AuthorizationException
from backend.app.core.security import decode_token
from backend.app.database.session import get_db
from backend.app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate bearer token and retrieve the current authenticated user"""
    if not credentials:
        raise AuthenticationException("Authorization bearer token required.")

    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationException("Invalid, expired, or malformed authentication token.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Token payload missing subject identifier.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationException("Authenticated user no longer exists.")
    if not user.is_active:
        raise AuthenticationException("User account is disabled.")

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """Server-side role guard ensuring current user belongs to authorized role set"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.name if current_user.role else "Operator"
        if current_user.is_superuser:
            return current_user
        if user_role not in allowed_roles:
            raise AuthorizationException(
                f"Role '{user_role}' is not authorized. Required: {allowed_roles}"
            )
        return current_user

    return role_checker
