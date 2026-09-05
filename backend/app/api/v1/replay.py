"""
API Router for Incident Visual Replays
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.replay import IncidentReplayResponse
from backend.app.services.replay_service import replay_service

router = APIRouter(prefix="/replay", tags=["Incident Replay"])


@router.get("/{incident_id}", response_model=IncidentReplayResponse)
async def get_incident_replay_timeline(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full visual replay timeline and keyframe overlays for an incident."""
    replay = await replay_service.get_incident_replay(db, incident_id=incident_id)
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay timeline for incident '{incident_id}' not found",
        )
    return replay
