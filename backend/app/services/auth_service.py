"""
Authentication & Authorization Domain Service Logic
"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.errors import (
    AuthenticationException,
    NotFoundException,
    ValidationException,
)
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.app.models.user import Role, User
from backend.app.schemas.auth import Token, UserCreate


class AuthService:
    """Service providing user authentication, token issuance, and registration"""

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            raise AuthenticationException("Invalid email or password.")
        if not verify_password(password, user.hashed_password):
            raise AuthenticationException("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationException("User account is deactivated.")
        return user

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing_user:
            raise ValidationException(f"User with email '{user_in.email}' already exists.")

        # Resolve role
        role = db.query(Role).filter(Role.name == user_in.role_name).first()
        if not role:
            # Create role if missing in seed
            role = Role(name=user_in.role_name, description=f"{user_in.role_name} Role")
            db.add(role)
            db.flush()

        new_user = User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
            role_id=role.id,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def create_user_tokens(user: User) -> Token:
        role_name = user.role.name if user.role else "Operator"
        access_token = create_access_token(subject=user.id, role=role_name)
        refresh_token = create_refresh_token(subject=user.id)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=28800,  # 8 hours in seconds
        )

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationException("Invalid or expired refresh token.")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise AuthenticationException("User not found or inactive.")

        return AuthService.create_user_tokens(user)
