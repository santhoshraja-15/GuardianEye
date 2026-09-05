"""
User Management and Administration Endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.errors import NotFoundException
from backend.app.core.security import get_password_hash
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List Users",
    description="Retrieve all registered users (Admin and Supervisor only).",
    dependencies=[Depends(require_roles(["Admin", "Supervisor"]))],
)
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[User]:
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User By ID",
    description="Retrieve specific user details.",
    dependencies=[Depends(require_roles(["Admin", "Supervisor"]))],
)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile / Status",
    description="Update user status, role, or credentials (Admin only).",
    dependencies=[Depends(require_roles(["Admin"]))],
)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)

    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.email is not None:
        user.email = user_update.email.lower()
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.role_id is not None:
        user.role_id = user_update.role_id
    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)

    db.commit()
    db.refresh(user)
    return user
