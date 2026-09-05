"""
API Router for Behaviour Events
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.behaviour import BehaviourEventResponse
from backend.app.services.behaviour_service import behaviour_service

router = APIRouter(prefix="/behaviours", tags=["Behaviours"])


@router.get("/video/{video_id}", response_model=List[BehaviourEventResponse])
async def get_behaviours_for_video(
    video_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all detected behaviour events for a video."""
    events = await behaviour_service.get_behaviour_events_by_video(
        db, video_id=video_id, limit=limit, offset=offset
    )
    return [
        BehaviourEventResponse(
            id=event.id,
            video_id=event.video_id,
            behaviour_type=event.behaviour_code,
            severity="HIGH",
            start_frame=event.start_frame,
            end_frame=event.end_frame,
            start_time_seconds=event.start_time_seconds,
            end_time_seconds=event.end_time_seconds,
            duration_seconds=event.duration_seconds,
            confidence=event.confidence,
            description=event.behaviour_name,
            keyframe_indices=[],
        )
        for event in events
    ]
