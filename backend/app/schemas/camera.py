"""
Pydantic Schemas for Camera Management and Calibration
"""
from datetime import datetime
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class CameraBase(BaseModel):
    name: str
    camera_code: str
    zone_id: Optional[str] = None
    rtsp_url: Optional[str] = None
    fps: int = 30
    resolution: str = "1920x1080"
    status: str = "ONLINE"


class CameraCreate(CameraBase):
    warehouse_id: str


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    zone_id: Optional[str] = None
    rtsp_url: Optional[str] = None
    fps: Optional[int] = None
    resolution: Optional[str] = None
    status: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    location_z: Optional[float] = None
    orientation_degrees: Optional[float] = None
    fov_degrees: Optional[float] = None
    coverage_range_m: Optional[float] = None


class CameraResponse(CameraBase):
    id: str
    warehouse_id: str
    location_x: float
    location_y: float
    location_z: float
    is_positioned: bool
    orientation_degrees: Optional[float] = None
    fov_degrees: float
    coverage_range_m: float
    is_calibrated: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalibrationPointPair(BaseModel):
    """One operator-supplied correspondence: a normalized (0-1) video
    point the operator clicked on a source frame, and the warehouse-meter
    point they entered for it."""

    video_point: Tuple[float, float] = Field(description="Normalized (0-1, 0-1) video-space point")
    world_point: Tuple[float, float] = Field(description="Warehouse-meters (x, y) point")


class CalibrationCreate(BaseModel):
    points: List[CalibrationPointPair] = Field(min_length=4, description="At least 4 point correspondences")


class CalibrationResponse(BaseModel):
    camera_id: str
    source_points: List[Tuple[float, float]]
    world_points: List[Tuple[float, float]]
    homography_matrix: Optional[List[List[float]]] = None
    reprojection_error: Optional[float] = None
    is_active: bool
    calibrated_at: datetime

    class Config:
        from_attributes = True
