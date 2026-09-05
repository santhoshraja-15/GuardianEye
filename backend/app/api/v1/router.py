"""
GuardianEye API v1 Master Router
"""
from fastapi import APIRouter
from backend.app.api.v1 import auth, health, storage, users

api_v1_router = APIRouter()

# Register core endpoint modules
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(storage.router, prefix="/storage", tags=["Storage"])
