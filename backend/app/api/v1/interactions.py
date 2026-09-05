"""
Interaction API Endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.interaction import (
    InteractionResponse,
    InteractionSummaryResponse,
)
from backend.app.services.interaction_service import interaction_service

router = APIRouter()


@router.get(
    "/{video_id}",
    response_model=InteractionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Video Interactions",
    description="Retrieve all detected human-object-equipment interactions for a video.",
)
def get_video_interactions(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InteractionSummaryResponse:
    interactions = interaction_service.get_interactions_for_video(db, video_id)
    resp_list = [
        InteractionResponse(
            interaction_id=f"int-{item.id}",
            source_track_id=item.source_track_id,
            source_class="person",
            target_track_id=item.target_track_id,
            target_class="carton",
            interaction_type=item.interaction_type,
            distance_px=item.min_distance_px,
            iou=item.max_iou,
            relative_velocity=(0.0, 0.0),
            start_frame=item.start_frame,
            current_frame=item.end_frame,
            start_time_seconds=item.start_time_seconds,
            current_time_seconds=item.end_time_seconds,
            duration_seconds=max(0.0, item.end_time_seconds - item.start_time_seconds),
            confidence=0.90,
        )
        for item in interactions
    ]
    return InteractionSummaryResponse(
        video_id=video_id,
        total_interactions=len(resp_list),
        interactions=resp_list,
    )
