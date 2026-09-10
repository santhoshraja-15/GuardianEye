"""
Pydantic Schemas for Digital Twin Warehouse Topology

normalized_polygon_points / normalized_position fields put zones,
cameras, and entities on one shared 0-1 plane (see
ai.spatial.coordinate_transform and DigitalTwinService) — the frontend
should render from these, not re-derive its own normalization from
polygon_points/dimensions_meters/position_xyz, which is exactly what
produced three incompatible coordinate spaces on one SVG before this
(zones scaled by warehouse meters, heatmap already 0-1, cameras in
meters — see architecture audit section 3).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ZoneTopology(BaseModel):
    zone_id: str
    zone_code: str
    zone_name: str
    zone_type: str
    polygon_points: List[List[float]]
    normalized_polygon_points: List[List[float]] = Field(default_factory=list)
    risk_multiplier: float
    is_restricted: bool = False


class CameraTopology(BaseModel):
    camera_id: str
    camera_code: str
    camera_name: str
    position_xyz: List[float]
    normalized_position: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    is_positioned: bool = False
    orientation_degrees: Optional[float] = None
    fov_degrees: float = 90.0
    coverage_range_m: float = 15.0
    coverage_zones: List[str]
    is_calibrated: bool = False
    status: str = "ONLINE"


class EntityTopology(BaseModel):
    """A real, currently-known tracked entity — the last recorded
    position of a Track row, not a decorative or invented marker.
    last_seen_seconds_ago lets the frontend honestly gray out anything
    stale rather than presenting a video-processing-time position as
    if it were a live camera feed."""

    track_id: int
    video_id: str
    camera_id: Optional[str] = None
    class_name: str
    normalized_position: List[float]
    zone_id: Optional[str] = None
    world_position: Optional[List[float]] = None
    world_position_quality: Optional[str] = None
    confidence: float
    last_seen_frame: int
    last_seen_timestamp_seconds: float


class DigitalTwinTopologyResponse(BaseModel):
    warehouse_id: str
    warehouse_name: str
    dimensions_meters: List[float]  # [width, length, height]
    zones: List[ZoneTopology] = Field(default_factory=list)
    cameras: List[CameraTopology] = Field(default_factory=list)
    entities: List[EntityTopology] = Field(default_factory=list)
    # Real count of distinct entities tracked across every video
    # attributed to this warehouse — NOT a fabricated constant or a
    # zones-count-times-four placeholder (see architecture audit,
    # digital_twin_service.py). "active" here means "has a track point
    # from the most recently processed video for this warehouse", which
    # is an honest definition given there is no live camera ingestion —
    # see is_live_entity_count below.
    active_entity_count: int = 0
    # False whenever active_entity_count describes the most-recently-
    # processed video rather than an actual live camera feed — always
    # False today (see architecture audit section 4: Live Streams is
    # uploaded-video replay, not RTSP ingestion), surfaced explicitly so
    # the frontend never has to guess.
    is_live_entity_count: bool = False
