"""
Pydantic Schemas for Spatial Zones and Geometric Intelligence
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ZoneBase(BaseModel):
    name: str
    code: str
    zone_type: str = "STORAGE"  # STORAGE, LOADING_BAY, DANGER, RESTRICTED, TRANSIT, STAGING
    polygon_coordinates: str = Field(description="JSON list of [x, y] coordinates")
    risk_weight: float = 1.0
    is_restricted: bool = False


class ZoneCreate(ZoneBase):
    warehouse_id: str


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[str] = None
    polygon_coordinates: Optional[str] = None
    risk_weight: Optional[float] = None
    is_restricted: Optional[bool] = None


class ZoneResponse(ZoneBase):
    id: str
    warehouse_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpatialOccupancyResponse(BaseModel):
    track_id: int
    class_name: str
    zone_id: str
    zone_name: str
    zone_type: str
    is_inside: bool
    distance_to_boundary_px: float
    is_restricted_violation: bool
