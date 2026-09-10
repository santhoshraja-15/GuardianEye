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
    # Ground-contact anchor (bottom-center for people/forklifts/
    # equipment, centroid otherwise — see
    # ai/spatial/coordinate_transform.anchor_point) in video pixel
    # space, and that same point normalized to 0-1. Null for points
    # persisted before this field existed. The frontend should overlay
    # from anchor_xy, not re-derive one from bbox_xyxy itself.
    anchor_xy: Optional[Tuple[float, float]] = None
    normalized_xy: Optional[Tuple[float, float]] = None


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
