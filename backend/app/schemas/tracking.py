"""
Pydantic Schemas for Multi-Object Tracking & Trajectories
"""
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class TrackPointResponse(BaseModel):
    frame_number: int
    timestamp_seconds: float
    bbox_xyxy: List[float]
    centroid_xy: Tuple[float, float]
    velocity_xy: Tuple[float, float]
    confidence: float
    zone_id: Optional[str] = None


class TrackResponse(BaseModel):
    id: str
    video_id: str
    track_id: int
    class_name: str
    confidence: float
    first_frame: int
    last_frame: int
    duration_seconds: float
    max_velocity: float
    trajectory_points: List[TrackPointResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TrajectorySummaryResponse(BaseModel):
    video_id: str
    total_tracks: int
    tracks: List[TrackResponse]
