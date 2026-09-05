"""
Pydantic Schemas for Behaviour Detection Events
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BehaviourEvidenceResponse(BaseModel):
    trigger_rule: str
    primary_entity_id: int
    primary_class: str
    secondary_entity_id: Optional[int] = None
    secondary_class: Optional[str] = None
    peak_velocity_px_s: float = 0.0
    impact_deceleration: float = 0.0
    fall_height_px: float = 0.0
    duration_seconds: float = 0.0
    zone_code: Optional[str] = None
    spatial_overlap_iou: float = 0.0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class BehaviourEventResponse(BaseModel):
    id: Optional[str] = None
    video_id: Optional[str] = None
    behaviour_type: str
    severity: str
    start_frame: int
    end_frame: int
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    confidence: float
    description: str
    evidence: Optional[BehaviourEvidenceResponse] = None
    keyframe_indices: List[int] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BehaviourQueryRequest(BaseModel):
    video_id: Optional[str] = None
    behaviour_types: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    min_confidence: float = 0.5
    limit: int = 100
    offset: int = 0
