"""
Pydantic Schemas for Incident Visual Replay
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReplayKeyframeBox(BaseModel):
    track_id: int
    class_name: str
    bbox_xyxy: List[float]
    state_label: str
    is_primary: bool = False


class ReplayKeyframe(BaseModel):
    frame_index: int
    timestamp_seconds: float
    image_url: str
    sha256_hash: str
    boxes: List[ReplayKeyframeBox] = Field(default_factory=list)


class IncidentReplayResponse(BaseModel):
    incident_id: str
    video_id: str
    behaviour_code: str
    clip_url: str
    snapshot_url: str
    sha256_checksum: str
    duration_seconds: float
    keyframes: List[ReplayKeyframe] = Field(default_factory=list)
