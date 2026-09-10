"""
Pydantic Schemas for Generalized Spatial Events (zone transitions,
proximity warnings, ...) — see backend/app/models/spatial_event.py for
why this is a separate stream from BehaviourEvent/Incident.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SpatialEventResponse(BaseModel):
    id: str
    video_id: str
    camera_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    event_type: str
    severity: str
    frame_number: int
    timestamp_seconds: float
    zone_id: Optional[str] = None
    from_zone_id: Optional[str] = None
    to_zone_id: Optional[str] = None
    involved_track_ids: List[int]
    confidence: float
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
