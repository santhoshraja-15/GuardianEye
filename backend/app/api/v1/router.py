"""
GuardianEye API v1 Master Router
"""
from fastapi import APIRouter
from backend.app.api.v1 import (
    auth,
    behaviours,
    health,
    interactions,
    risks,
    storage,
    tracks,
    users,
    videos,
    zones,
)

api_v1_router = APIRouter()

# Register core endpoint modules
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(storage.router, prefix="/storage", tags=["Storage"])
api_v1_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
api_v1_router.include_router(tracks.router, prefix="/tracks", tags=["Tracking"])
api_v1_router.include_router(zones.router, prefix="/zones", tags=["Zones"])
api_v1_router.include_router(
    interactions.router, prefix="/interactions", tags=["Interactions"]
)
api_v1_router.include_router(
    behaviours.router, prefix="/behaviours", tags=["Behaviours"]
)
api_v1_router.include_router(
    risks.router, prefix="/risks", tags=["Risks"]
)
