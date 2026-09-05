"""
Pydantic Schemas for Entity Interactions
"""
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class InteractionResponse(BaseModel):
    interaction_id: str
    source_track_id: int
    source_class: str
    target_track_id: int
    target_class: str
    interaction_type: str
    distance_px: float
    iou: float
    relative_velocity: Tuple[float, float]
    start_frame: int
    current_frame: int
    start_time_seconds: float
    current_time_seconds: float
    duration_seconds: float
    confidence: float


class InteractionSummaryResponse(BaseModel):
    video_id: str
    total_interactions: int
    interactions: List[InteractionResponse] = Field(default_factory=list)
