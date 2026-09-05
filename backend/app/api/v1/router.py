"""
GuardianEye API v1 Master Router
"""
from fastapi import APIRouter
from backend.app.api.v1 import health

api_v1_router = APIRouter()

# Register core endpoints
api_v1_router.include_router(health.router, tags=["Health"])
