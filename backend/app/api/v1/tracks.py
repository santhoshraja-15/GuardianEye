"""
Tracking and Trajectory API Endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.tracking import (
    TrackPointResponse,
    TrackResponse,
    TrajectorySummaryResponse,
)
from backend.app.services.tracking_service import tracking_service

router = APIRouter()


@router.get(
    "/{video_id}",
    response_model=TrajectorySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Video Trajectories",
    description="Retrieve all tracked entities and full trajectory timelines for a video.",
)
def get_video_tracks(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TrajectorySummaryResponse:
    tracks = tracking_service.get_tracks_for_video(db, video_id)
    track_responses = []

    for t in tracks:
        points = [
            TrackPointResponse(
                frame_number=p.frame_number,
                timestamp_seconds=p.timestamp_seconds,
                bbox_xyxy=[p.bbox_x1, p.bbox_y1, p.bbox_x2, p.bbox_y2],
                centroid_xy=(p.centroid_x, p.centroid_y),
                velocity_xy=(p.velocity_x, p.velocity_y),
                confidence=p.confidence,
                zone_id=p.zone_id,
            )
            for p in t.track_points
        ]

        track_responses.append(
            TrackResponse(
                id=t.id,
                video_id=t.video_id,
                track_id=t.track_id,
                class_name=t.class_name,
                confidence=t.confidence,
                first_frame=t.first_frame,
                last_frame=t.last_frame,
                duration_seconds=t.duration_seconds,
                max_velocity=t.max_velocity,
                trajectory_points=points,
            )
        )

    return TrajectorySummaryResponse(
        video_id=video_id,
        total_tracks=len(track_responses),
        tracks=track_responses,
    )
