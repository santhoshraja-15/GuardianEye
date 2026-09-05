"""
Authentication and Token Management API Endpoints
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    Token,
    UserCreate,
    UserResponse,
)
from backend.app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate credentials and obtain signed JWT access & refresh tokens.",
)
def login(login_data: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    return AuthService.create_user_tokens(user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user account with role assignment.",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    user = AuthService.register_user(db, user_in)
    return user


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Exchange a valid refresh token for a fresh access token.",
)
def refresh_token(refresh_data: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    return AuthService.refresh_access_token(db, refresh_data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Retrieve the profile and role details of the currently authenticated user.",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user
